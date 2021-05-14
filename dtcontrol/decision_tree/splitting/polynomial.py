from abc import ABC
import numpy as np
from sklearn import svm
import math, logging
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.linear_split import LinearSplit
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy
from dtcontrol.decision_tree.splitting.split import Split

# we transform the dataset to a higher dimesion by added features such aus x_0^2, x_0*x_1, ...
# as this is rather costly, we save the transformed dataset in the dataset object
# as we could have multiple different transformed datasets, we associate it with a key
KEY_QUAD = "poly_2"
# a bound on the error that can occur when transforming coefficients
FLOAT_PRECISION = 1e-12


class PolynomialClassifierSplittingStrategy(SplittingStrategy):
    def __init__(self, prettify=True, determinizer=LabelPowersetDeterminizer(), linear_svc_params={}):
        """ Args:
        prettify: Disabling prettify can give a ~2x speed-up.
        determinizer: Default is LabelPowersetDeterminizer.
        linear_svc_params: Keyword args given to sklearn.svm.LinearSVC, default values are:
                            max_iter=200, dual=False, C=1e6,
        """
        super().__init__()
        self.logger = logging.getLogger("poly_logger")
        self.logger.setLevel(logging.ERROR)
        self.determinizer = determinizer
        self.prettify = prettify
        # C scales the error term when data is misclassified. Set it so something very high
        # so that we get as many samples correct as possible correct (overfitting is not a problem)
        self.linear_svc_params = {
            "max_iter": 200,
            "dual": False,
            "C": 1e6,
            **linear_svc_params
        }

    @staticmethod
    def transform_quadratic(X):
        """
        transforms a list of vectors [(x_0, …, x_n)] to a higher dimensional space:
        -> [(x_0^2, x_1^2, …, x_0*x_1, …, x_0, x_1, …, 1)]
        """
        def phi(X):
            X = np.append(X, 1)
            return np.array([X[i]*X[j] for j in range(len(X)) for i in range(j+1)])

        return np.apply_along_axis(phi, 1, X)

    @staticmethod
    def get_coefficients(standardizer, classifier):
        """ returns the correctly scaled coefficients for the equation
        """
        # The standardizer transforms the input data to have mean=0 and stdderv=1
        # so a value v becomes (v-mean)/scale
        # we now have the coefs for the standardized data:
        # c_1 * (x_1-m)/s
        # so the coef for the non-standardized data is c_1/s
        # and the intercept changes with -c_1*m/s
        def rev_transf(mean, scale, coefs, b):
            """undo standardization: c*(x-m)/s --> c/s*x - c*m/s"""
            newCoefs = []
            for m, s, c in zip(mean, scale, coefs):
                b -= c*m/s
                newCoefs.append(c/s)
            return (newCoefs, b)

        coefsScaled = classifier.coef_[0]
        interceptScaled = classifier.intercept_[0]

        coefs, intercept = rev_transf(
            standardizer.mean_, standardizer.scale_, coefsScaled, interceptScaled)
        coefs[-1] += intercept  # last coef is has factor 1
        return coefs

    def prettify_coefs(self, x, y, std, svc, pipeline):
        """rounds coefficients (possible to 0) without changing the classification"""
        # 1: we test if we can fit the function without a certain coefficient
        # For that, we re-train the model without this dimension.
        #
        # 2: we scale the equation so that at least one coefficient is =1
        #
        # 3: we test if we can round coefficient c to rnd(c),
        # starting with a low precision then getting more precise until
        # there is no change in classification.
        # To test if the classification still works, we over-approximate the change.
        # This way, we have no problems with rounding errors when transforming the coefficents
        # to the non-standardized form.
        self.logger.debug("prettifying..")
        baseAccurarcy = pipeline.score(x, y)
        basePred = pipeline.predict(x)
        coefs = svc.coef_[0]  # reference which we write into
        enabledFeatures = np.ones(len(coefs), dtype=bool) #bool flag if enabled

        # we use this pipline to fit with less variables
        # the normal pipline is fixed in the number of features
        alt_standardizer = StandardScaler()
        alt_svc = svm.LinearSVC(**self.linear_svc_params)
        alt_pipeline = make_pipeline(alt_standardizer, alt_svc)

        def test_in_alt():
            alt_pipeline.fit(x[:, enabledFeatures], y)
            return alt_pipeline.score(x[:, enabledFeatures], y) >= baseAccurarcy

        def accuracy_still_good():
            #return pipeline.score(x, y) >= baseAccurarcy
            return (basePred == pipeline.predict(x)).all()

        # sort by increasing order -> round small coefficients to 0 first
        # last index is intercept, has to be done last
        coefIndOrder = sorted(list(range(len(coefs) - 1))) + [len(coefs) - 1]

        # step 1: set as many coefficients to zero as possible
        for coefInd in coefIndOrder:
            if coefs[coefInd] == 0:
                enabledFeatures[coefInd] = False
                continue
            if coefInd == len(coefs) - 1:
                # we cannot leave out the constant offset (intercept will be added either way)
                # also the intercept will change in step 2
                continue
            # try setting it to 0 without retraining (is much faster if it works)
            orgCoef = coefs[coefInd]
            coefs[coefInd] = 0 + \
                (FLOAT_PRECISION if coefs[coefInd] < 0 else -FLOAT_PRECISION)
            if accuracy_still_good():
                coefs[coefInd] = 0
                enabledFeatures[coefInd] = False
                continue
            coefs[coefInd] = orgCoef
            # try removing feature and retraining
            enabledFeatures[coefInd] = False
            if test_in_alt():
                # did work, take newly trained coefs into real pipeline
                coefs[enabledFeatures] = alt_svc.coef_[0]
                coefs[~enabledFeatures] = 0
                svc.intercept_[0] = alt_svc.intercept_[0]
                continue
            enabledFeatures[coefInd] = True

        basePred = pipeline.predict(x)

        # step 2: take one coefficient and fix it to 1 (scale the entire equation)
        # choose the one closest to 1, distance is abs(log10(abs(x)))
        coefTo1 = min(
            list(range(len(coefs) - 1)),
            key= lambda x: abs(math.log10(abs(coefs[x]/std.scale_[x])))
                                if coefs[x]*std.scale_[x] != 0 else math.inf
        )
        # only positive scaling is allowed
        scaleFac = abs(1 / (coefs[coefTo1] / std.scale_[coefTo1])) \
                        if coefs[coefTo1]*std.scale_[coefTo1] != 0 else 1
        coefs *= scaleFac
        svc.intercept_[0] *= scaleFac
        if not accuracy_still_good():
            # can happen if precision error occur for very high coefs
            # will be dealt with later in check_reasonable_coefs
            self.logger.warn(f"After scaling the equation, accuracy decreased. Scale factor: {scaleFac}")

        # step 3: round remaining coefficients
        for coefInd in coefIndOrder:
            scale = std.scale_[coefInd]
            lastInd = coefInd == len(coefs) - 1
            if (not lastInd and coefs[coefInd] == 0) or scale == 0:
                continue
            # eqCoef is the coefficent of the final equation.
            if lastInd:  # coefficient for factor 1
                # eqCoef = intercept + off set from other coefs
                interceptBase = svc.intercept_[0]
                eqCoef = self.get_coefficients(std, svc)[-1]
                if eqCoef == 0:
                    continue
            else:
                eqCoef = coefs[coefInd] / scale

            # try rounding
            exp = math.floor(math.log10(abs(eqCoef)))
            for precision in range(0, 15):
                # start with one above so that 0.7 can become 1
                round_scale = 10**(exp + 1 - precision)
                eqCoefGoal = round(eqCoef / round_scale) * round_scale
                if eqCoefGoal == 0:
                    continue  # we have already tried it and for this, the over-approximation is not valid
                if lastInd:
                    svc.intercept_[0] = interceptBase + \
                        (eqCoefGoal - eqCoef) * (1+FLOAT_PRECISION)
                    if accuracy_still_good():
                        svc.intercept_[0] = interceptBase + eqCoefGoal - eqCoef
                        break
                else:
                    # it has to be correct even when faced with relative rounding errors:
                    overApproxFac = (
                        1+FLOAT_PRECISION if abs(eqCoefGoal) > abs(eqCoef) else 1-FLOAT_PRECISION)
                    coefs[coefInd] = eqCoefGoal * scale * overApproxFac
                    if accuracy_still_good():
                        coefs[coefInd] = eqCoefGoal * scale  # without overApproxFac
                        break
            else: # should never happen
                self.logger.warn(f"Could not find rounded value for variable with index {coefInd}")
        self.logger.debug("prettifying done.")
        return self.get_coefficients(std, svc)

    def check_reasonable_coefs(self, x, y, std, svc, pipeline):
        """
        We want to avoid coefficients > 1e7 and < 1e-7. Otherwise we run into
        precision errors when computing the dot product (calculation is no longer
        commutative).
        This method checks if the coefficients are in this reasobale range, otherwise
        changes them. This could decrease accuracy.
        """
        # If we have very large coeffients, we add additional samplepoints
        # for every feature with both labels. This way, a high coeffient is
        # penalized. We set a low sample weight, to not disturb the fitting
        # too much.

        eqCoef = self.get_coefficients(std, svc) # the coefs for the equation
        if any(abs(c) > 1e7 for c in eqCoef): # should only occur exceptionally
            featCnt = x.shape[1]
            addX1 = np.array([[1.0 if f == i else 0.0 for i in range(featCnt)] for f in range(featCnt)])
            newX = np.concatenate((x, addX1, addX1))
            addY = np.array([i<featCnt for i in range(2*featCnt)]) # first half True, other False
            newY = np.concatenate((y, addY))
            weights = np.concatenate((np.full(x.shape[0], 1), np.full(2*featCnt, 1e-3)))
            
            self.logger.warn(f"Fixing unreasonable coefs: {eqCoef}")
            pipeline.fit(newX, newY, linearsvc__sample_weight=weights) # changes the coefs
            eqCoef = self.get_coefficients(std, svc)
            self.logger.warn(f"New coefs: {eqCoef}")

            # this should remove unreasonable high coefs. If not
            # change it by force (will change accuracy)
            if any(abs(c) > 1e7 for c in eqCoef):
                self.logger.warn(f"Coefs still too high.")
                eqCoefNP = np.array(eqCoef)
                inds = np.where(abs(eqCoefNP) > 1e7)[0]
                # reference which we write into
                # note: these are not scaled yet
                coefs = svc.coef_[0]
                for ind in inds:
                    coefs[ind] = std.scale_[ind] * (1e7 if coefs[ind] > 0 else -1e7)
                eqCoef = self.get_coefficients(std, svc)
                self.logger.warn(f"New coefs: {eqCoef}")
        # set coef < 1e-9 to 0 by force
        # (will change accuracy)
        if any(c != 0 and abs(c) < 1e-7 for c in eqCoef):
            self.logger.warn(f"Coefs near zero: {eqCoef}")
            eqCoefNP = np.array(eqCoef)
            inds = np.where((eqCoefNP != 0) & (abs(eqCoefNP) < 1e-7))[0]
            # reference which we write into
            coefs = svc.coef_[0]
            for ind in inds:
                coefs[ind] = 0
            eqCoef = self.get_coefficients(std, svc)
            self.logger.warn(f"New coefs: {eqCoef}")

        return eqCoef

    def find_split(self, dataset, impurity_measure, **kwargs):
        x_numeric = dataset.get_numeric_x()
        if x_numeric.shape[1] == 0:
            return None

        y = self.determinizer.determinize(dataset)
        splits = []
        x_high_dim = dataset.get_transformed_x( # get the cached transformed dataset
            self.transform_quadratic, KEY_QUAD)
        labels, counts = np.unique(y, return_counts=True)
        # sort labels by count, descending
        # (order only matters if we find multiple prefect splits)
        labels = labels[np.argsort(-counts)]
        for label in labels:
            label_mask = (y == label)
            standardizer = StandardScaler()  # LinearSVC needs standardized values
            svc = svm.LinearSVC(**self.linear_svc_params)
            pipeline = make_pipeline(standardizer, svc)
            pipeline.fit(x_high_dim, label_mask)
            acc = pipeline.score(x_high_dim, label_mask)
            totCnt = x_high_dim.shape[0]
            falseCount = totCnt * (1-acc)

            coefs = self.get_coefficients(standardizer, svc)
            split = PolynomialSplit(
                pipeline, coefs, dataset.numeric_columns, self.priority
            )
            impurity = impurity_measure.calculate_impurity(dataset, split)
            splitData = (impurity, split, label_mask, standardizer, svc)
            splits.append(splitData)
            
            self.logger.debug(f"misclassified: {round(falseCount)}" +
                  f" out of {totCnt} iterations: {svc.n_iter_}" +
                  f" impurity: {impurity}")
            if falseCount == 0:
                # if everything is correct, we take this split
                break

        imp, bestSplit, label_mask, standardizer, svc = min(
            splits, key=lambda t: t[0])
        if self.prettify:
            prettyCoefs = self.prettify_coefs(
                x_high_dim, label_mask, standardizer, svc, bestSplit.pipeline)
            bestSplit.coefficients = prettyCoefs
        
        bestSplit.coefficients = self.check_reasonable_coefs(
            x_high_dim, label_mask, standardizer, svc, bestSplit.pipeline
        )
        return bestSplit


class PolynomialSplit(Split, ABC):
    """
      Represents a polynomial split of the form p(x) <= 0.
      Right now, the polynomial is quadratic.
    """

    def __init__(self, pipeline, coefs, numeric_columns, priority=1):
        """
        Args:
            pipline: used to predict data
            coefs: the coefficients of the polynomial with respect to the relevant columns
            numeric_columns: a list of integers defining the columns used in the polynomial
        """
        super().__init__()
        self.coefficients = coefs
        self.relevant_columns = numeric_columns
        self.pipeline = pipeline
        self.priority = priority

    def get_masks(self, dataset):
        x_transf = dataset.get_transformed_x( # try to use the cached transformation
            PolynomialClassifierSplittingStrategy.transform_quadratic, KEY_QUAD
        )
        mask = np.dot(x_transf, self.coefficients) <= 0
        return [mask, ~mask]

    def predict(self, features):
        x_transf = PolynomialClassifierSplittingStrategy.transform_quadratic(
                                            features[:, self.relevant_columns])
        return 0 if np.dot(x_transf, self.coefficients) <= 0 else 1

    def __repr__(self):
        return "PolynomialSplit: " + self.get_equation_str(rounded=True)

    def print_dot(self, variables=None, category_names=None):
        return self.get_equation_str(rounded=True, newlines=True, variables=variables)

    def print_c(self):
        return self.get_equation_str(machineReadable=True)

    def print_vhdl(self):
        eq = self.get_equation_str(machineReadable=True)
        return eq.replace('[', '').replace(']', '')

    def _getVariablesWithOne(self, variables):
        if not variables:
            variables = [f"x[{i}]" for i in range(
                max(self.relevant_columns)+1)]
        variables = np.array(variables)[self.relevant_columns]
        return np.append(variables, "1")

    def get_equation_str(self, rounded=False, newlines=False, variables=None, machineReadable=False):
        # if the classifier is called with prettify=True, rounding should not make a difference
        line = []
        n = len(self.relevant_columns)
        variables = self._getVariablesWithOne(variables)
        for ind, (i, j) in enumerate([(i, j) for j in range(n+1) for i in range(j+1)]):
            coef = self.coefficients[ind]
            if coef == 0 or rounded and abs(coef) < 1e-6:
                continue
            coef = round(coef, 6) if rounded else coef
            if variables[i] == "1":  # i<=j --> var[j] == 1 --> constant offset without var
                line.append(
                    f"{int(coef) if int(coef) == coef else coef}")
                continue
            elif variables[j] == "1":
                var = f"{variables[i]}"
            else:
                var = f"{variables[i]}²" if i == j and not machineReadable else f"{variables[i]}*{variables[j]}"
            if coef == 1:
                term = var
            elif coef == -1:
                term = f"-{var}"
            elif not machineReadable and int(coef) == coef:
                # leave out the '*'
                term = f"{int(coef)}{var}"
            else:
                term = f"{coef}*{var}"
            line.append(term)
        joiner = "\\n+" if newlines else "+"
        poly = joiner.join(line) + " <= 0"
        return poly.replace('+-', '-')

    def to_json_dict(self, rounded=False, variables=None, **kwargs):
        lhs = []
        n = len(self.relevant_columns)
        variables = self._getVariablesWithOne(variables)
        for ind, (i, j) in enumerate([(i, j) for j in range(n+1) for i in range(j+1)]):
            coef = self.coefficients[ind]
            if coef == 0 or rounded and abs(coef) < 1e-6:
                continue
            coef = round(coef, 6) if rounded else coef
            if variables[i] == "1":  # i<=j --> var[j] == 1
                continue
            elif variables[j] == "1":
                var = f"{variables[i]}"
            else:
                var = f"{variables[i]}^2" if i == j else f"{variables[i]}*{variables[j]}"
            lhs.append({"coeff": coef, "var": var})
        lhs.append({"intercept": round(
            self.coefficients[-1], 6) if rounded else self.coefficients[-1]})
        return {
            "lhs": lhs,
            "op": "<=",
            "rhs": 0}
