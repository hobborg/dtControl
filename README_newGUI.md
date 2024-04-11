# New Frontend

## Page 1

#### Organisation of Tables
|   Before  |   Now  | Done?
| --- | --- | --- |
| one table for the experiments, one table for the results (de facto 1:1 correspondence of rows in the two tables) | only one table for experiments and results | [x]
| no controller table, controller upload + experiment settings are the same step, re-upload controller for a new experiment (if page refresh since last upload) | first upload controller file once, examine it in table for controllers, then option start different experiments for that controller | [x]
| no information about controller files available | display # states, # state-action pairs, variable types, # state variables, # output variables and maximum non-determinism in controller table so information available when choosing an experiment | [x]
| starting the same experiment from the experiments table multiple times is possible (why would you do that?), but only one computation will be displayed as finished in the results table, the other identical computations stay at status 'Running...' | no separation between experiments and results in two different tables, one table for the experiment and its result, same experiment multiple times not a problem | [x]
| procedure felt like 'too many clicks': upload controller + add experiment (with default preset) + start experiment | reduce 'number of clicks': upload controller (only if first time use) + start experiment (for any of the three default presets) | [x]
| user predicates not accessible after input anymore | user predicates are stored in the results table (in a modal) | [x]
| deletion of experiments leads to duplicate ids, ids then change upon page refresh (because row numbers used as ids) | deletion (of controllers or experiments/results) and page refresh does not lead to problems, ids stay unique | [x]
| deletion of results not possible | deletion of results possible | [x]
| currently running experiments disappear upon page refresh | running experiments are still in results table after page refresh | [x]

#### Options to Run Experiments (Old Sidebar, New Modal)
|   Before  |   Now  | Done?
| --- | --- | --- |
| 17 different presets in drop-down (all different combinations of the advanced options): confusing, not necessary because advanced options allow to do same thing |  three presets: one simple deterministic, two permissive | [x]
| not clear that more than one option for the numeric and categorical predicates can be chosen / how to do that | checkboxes to check more than one option | [x]
| 'auto' determinization mandatory if impurity is 'multilabelentropy', otherwise error in computation, but connection not clear in GUI | 'multilabelentropy' is now a determinization technique | [x]
| choices for impurity | impurity is 'multilabelentropy' if 'multilabelentropy' chosen as determinization, 'entropy' otherwise | [x] 
| entering custom user predicates is its own preset ('algebraic'), needs a fallback preset, but cannot be combined with advanced options, also the user predicate input field and the fallback field do not disappear if the preset is changed again | enter user predicates with any combination of the advanced options | [x]
| user predicates not checked | user predicates get duplicate check + syntax check | [x]
| tolerance field always available in advanced settings |  tolerance field only available when 'valuegrouping' checked because only then relevant | [x]
| options for determinize, categorical and numeric predicates always available in advanced options |  options for determinize, categorical and numeric predicates only available in advanced options when applicable to controller | [x]
| linear-logreg option for numeric predicates not working | fixed penalty parameter in linear-logreg | [x]
| safe-pruning is a separate option with (True/False) | safe-pruning is a determinization technique | [x]

#### File Upload
|   Before  |   Now  | Done?
| --- | --- | --- |
| no file format check for controller file, no error message, but result computation never finishes if wrong file format uploaded | file format check immediately, upload denied with error message | [x]
| no name check for metadata file (but will not find the uploaded file during computation if named incorrectly) | name check for metadata file | [x]
| metadata file upload counter-intuitive: if there is a metadata file with the correct name in /tmp/, it will be used automatically (even if not explicitly uploaded, might be there from earlier upload) | duplicate check for controllers and deletion of metadata file if controller is deleted, so situation where a metadata file from past upload is used is not possible anymore | [x]

#### Further Ideas / ToDos
- testing! different file formats, safe-pruning, oc1, user predicates, categorical predicates...
- safe-pruning does not seem to be working (does not work on main branch/in old GUI, same error in new GUI, backend error)
- oc1 not working, also sometimes not on main branch/in old GUI
- test/think about safe-pruning as determinizer
- tolerance parameter not shown in new GUI in results table (only relevant when 'valuegrouping' chosen)
- add priorities in advanced options modal: check that values in [0, 1]
- now user predicates are entered individually, maybe also give option to enter many at once / from a file (?)
- jump directly to tree builder
- abort a running experiment
- possibility to give custom name to an edited tree, display in results table, like a mini-note
- instead of the status "Running...", show the increasing second count
- add more explanations on hover (already done for the buttons in the controller table), e.g. in advanced options modal
- also show number of nodes for an edited tree in results table
- update results table if retrained with different configurations

## Page 2

|   Before  |   Now  | Done?
| --- | --- | --- |
| edit mode: 17 presets, always show all advanced options no matter if applicable or not, input of predicate classes not intuitive  | restructure similarly to advanced options modal on page 1 | [x]
| after retraining, retrain button is not disabled although no node is selected in visualization | fixed | [x]
| no plotting | rudimentary 2d plotting of dataset and of linear cuts, also plotting datasets corresponding to single nodes possible from sidebar (button located in Edit mode because supposed to support interactive tree builder) | [x]

#### Further Ideas / ToDos
- add custom predicates in edit mode similarly to page 1	
- **interactive tree builder**
	- testing! many bugs, e.g. when you start on a leaf
	- redesign? go through everything, there are elements that do not make sense/ do not work...
	- make predicate collection global, so predicates stay in the Predicate Collection table even if you change nodes --> already implemented on branch svm-predicates, see commit Apr 19, 2023
	- make add predicate modal prettier -> already implemented on branch svm-predicates, see commit Apr 19, 2023
	- add custom names to the predicates added in the interactive tree builder -> already implemented on branch svm-predicates, see commit Apr 19, 2023
	- Delete Predicate button in Predicate Collection enabled when no predicates available (clicking it leads to error)
- make interactive tree builder and plotting work together, get rid of bugs when you switch between the two modes, use plotting to support interactive tree builder
- click again on Inspect / Edit / Simulate in bar to close corresponding sidebar etc
- inspect mode: only "all" can be selected, selection of "some" not possible because has class="d-none" although possible in code
- **tree**
	- do sth about resetFocus that pulls tree to the center of the box when the page is loaded
	- can we do sth to make huge trees prettier, e.g. non-deterministic tree of 10 rooms very hard to inspect because of distances/ sizes of tree visualization
- **plotting**
	- 3D plotting only works in certain browsers/ if you're lucky
	- enable plotting of dataset also in leaves that are not yet homogeneous because of current construction in interactive tree builder --> already implemented on branch svm-predicates, see commit Mar 9, 2023
	- enable plotting of root node from sidebar
	- replace selection of dimensions with drop down or refine error message, use names of dims if provided
	- testing, e.g. if same dimension selected more than once, if splits more complex than linear
	- goal: plot labelled data space + predicates
	- plot predicates as hyperplanes
	- click on node in tree and see dataset of that node
	- whole visualization collapsible
	- find got size and opacity for markers: fixed, automatically adapting or drop down to choose?
	- give good legend: size of dataset, how many points shown, how much is in the node
	- dealing with huge controllers (currently: plot random subset of controller)
		- idea: clustering -> hard!
		- discretize/aggregate with grid, quantization, heatmap, grid fields with number + color-coded
	- use plot to find good predicates
		- get predicate input from clicking in plot because clicking is approximate (simplify, round to nearest point?), but popular
		- ...or just enter predicates manually and see them in plot, visualize what a predicate would do
		- clicking idea "cherry on top" (Jan), fit a line the user traces --> hard!
		- propose a split, build interactively because what seems natural for a human vs a machine differs, optimality vs interpretability/explainability

## General Further Ideas / ToDos

- look at new tools: AMYTISS (reachability, safety like SCOTS, also noise), OmegaThreads (LTL) https://www.hyconsys.com/software.html
- explore 10 rooms further: radius post to 1, in SCOTS smaller eta
- find better algebraic predicates for dcdc example like we did for cruise control
- new ideas for predicate strategies after looking at dcdc plot
	- oblique predicates/cuts: ignore "mixed" area of dcdc plot, only use points with determinized labels, ignore the others
	- determinize after split
- clean up all the branches of the repo
- **documentation**
	- update screenshots for new frontend --> TODO if we put new frontend on main
	- tutorial videos are also on old frontend --> TODO if we put new frontend on main
	- parts seem outdated / not properly tested / unclear to non-developers --> go through everything, update, add explanations 


## Comments on My Branches

- **new-GUI**: Everything described here is on that branch (except stated otherwise).
- **debug/ids-exp-results-tables**: I did some debugging of the indices for the controllers and results there. (On the current main / in the old GUI, results did not have a unique id and controllers got the current row number as id, which lead to various problems.) Everything I did on that branch is already included in **new-GUI**, however Christoph did some session support stuff on that branch as well.
- **update/docs-v3**: This branch was used to test how to change the documentation to write the ReadMe in `docs` file. It contains minor changes in the documentation that were also later commited to the main branch directly, i.e. this branch can be deleted.
- **svm-predicates**: Most things on this branch are already part of **new-GUI**. Only the last few commits from March 09, 2023 and later could still be useful if the Interactive Tree Builder gets debugged and refactored.

If you have any questions on this, feel free to contact me at <tabea.frisch@tum.de>.
