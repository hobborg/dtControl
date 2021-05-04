from abc import ABC
import numpy as np
from sklearn import svm
import math
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
    def __init__(self, prettify=True, determinizer=LabelPowersetDeterminizer(), linear_svc_params={}, **kwargs):
        """Disabling prettify can give a ~2x speed-up"""
        super().__init__()
        self.determinizer = determinizer
        self.kwargs = kwargs
        self.prettify = prettify
        # C scales the error term when data is misclassified. Set it so something very high
        # so that we get as many samples correct as possible correct (overfitting is not a problem)
        self.linear_svc_params = {
            "max_iter": 200,
            "dual": False,
            "C": 1e8,
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
        # 2: we test if we can round coefficient c to rnd(c),
        # starting with a low precision then getting more precise until
        # there is no change in classification.
        # To test if the classification still works, we over-approximate the change.
        # This way, we have no problems with rounding errors when transforming the coefficents
        # to the non-standardized form.
        baseAccurarcy = pipeline.score(x, y)
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
            return pipeline.score(x, y) >= baseAccurarcy

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

        # step 2: round remaining coefficients
        for coefInd in coefIndOrder:
            scale = std.scale_[coefInd]
            lastInd = coefInd == len(coefs) - 1
            if not lastInd and coefs[coefInd] == 0:
                continue
            if lastInd:  # coefficient for factor 1
                # coef = intercept + off
                interceptBase = svc.intercept_[0]
                eqCoef = self.get_coefficients(std, svc)[-1]
            else:
                eqCoef = coefs[coefInd] / scale

            # try rounding
            exp = math.floor(math.log10(abs(eqCoef)))
            for precision in range(0, 10):
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
                print(f"WARN: could not find rounded value for variable with index {coefInd}")
        return self.get_coefficients(std, svc)

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
            #print("misclassified:", round(falseCount),
            #      "out of", totCnt, "iterations:", svc.n_iter_)

            coefs = self.get_coefficients(standardizer, svc)
            split = PolynomialSplit(
                pipeline, coefs, dataset.numeric_columns, self.priority
            )
            impurity = impurity_measure.calculate_impurity(dataset, split)
            splitData = (impurity, split, label_mask, standardizer, svc)
            splits.append(splitData)
            
            if falseCount == 0:
                # if everything is correct, we take this split
                break

        imp, bestSplit, label_mask, standardizer, svc = min(
            splits, key=lambda t: t[0])
        if self.prettify:
            prettyCoefs = self.prettify_coefs(
                x_high_dim, label_mask, standardizer, svc, bestSplit.pipeline)
            bestSplit.coefficients = prettyCoefs
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
        mask = self.pipeline.predict(x_transf)
        return [~mask, mask]

    def predict(self, features):
        #return 1 if self.pipeline.predict(
        #    PolynomialClassifierSplittingStrategy.transform_quadratic(
        #        features[:, self.relevant_columns])
        #)[0] else 0
        x_transf = PolynomialClassifierSplittingStrategy.transform_quadratic(
                                            features[:, self.relevant_columns])
        return 0 if np.dot(x_transf, self.coefficients) <= 0 else 1

    def __repr__(self):
        return "PolynomialSplit: " + self.get_equation_str(rounded=True)

    def print_dot(self, variables=None, category_names=None):
        return self.get_equation_str(rounded=True, newlines=True, variables=variables)

    def print_c(self):
        return self.get_equation_str(square=False)

    def print_vhdl(self):
        eq = self.get_equation_str(square=False)
        return eq.replace('[', '').replace(']', '')

    def _getVariablesWithOne(self, variables):
        if not variables:
            variables = [f"x[{i}]" for i in range(
                max(self.relevant_columns)+1)]
        variables = np.array(variables)[self.relevant_columns]
        return np.append(variables, "1")

    def get_equation_str(self, rounded=False, newlines=False, variables=None, square=True):
        # if the classifier is called with prettify=True, rounding should not make a difference
        line = []
        n = len(self.relevant_columns)
        variables = self._getVariablesWithOne(variables)
        for ind, (i, j) in enumerate([(i, j) for j in range(n+1) for i in range(j+1)]):
            coef = self.coefficients[ind]
            if rounded and abs(coef) < 1e-6:
                continue
            coef = round(coef, 6) if rounded else coef
            if variables[i] == "1":  # i<=j --> var[j] == 1 --> constant offset without var
                if coef != 0:
                    line.append(
                        f"{int(coef) if int(coef) == coef else coef}")
                continue
            elif variables[j] == "1":
                var = f"{variables[i]}"
            else:
                var = f"{variables[i]}²" if i == j and square else f"{variables[i]}*{variables[j]}"
            if coef == 1:
                term = var
            elif coef == -1:
                term = f"-{var}"
            elif int(coef) == coef:
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
            if rounded and abs(coef) < 1e-6:
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
