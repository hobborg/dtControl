// supported file formats for the controller files
var inputFormats = [".scs", ".dump", ".csv", ".prism", ".storm.json"]
// see extension_to_loader in dataset.py and get_files(path) in benchmark_suite.py and ALLOWED_EXTENSIONS in app.py
// TODO T: if not p.endswith('_states.prism') ? + put somewhere else...

// note that we once had a function loadControllers(path), if we need it again, it can be found here in code of old frontend

$(document).ready(function () {

    // load data and init listeners
    $.get('/controllers', controllers => Object.entries(controllers).forEach(e => addToControllerTable(e[1]))).then(() => initControllerTableListeners());
    $.get('/results', results => {
        for (const [, result] of Object.entries(results)) {
            addToResultsTable(result);
            if (result.status === "Running") {
                startPolling(result.res_id);
                // calls the function once for each unfinished experiment
                // if slow: call it once for all unfinished experiments
            }
        }
    });

    function startPolling(res_id) {
        // if an experiment was running during a page refresh, we have to manually update the table when it completes
        const interval = setInterval(() => {
            $.get('/results', results => {
                if (results[res_id]["status"] == "Completed") {
                    addToResultsTable(results[res_id]);
                    clearInterval(interval);
                }
            })
        }, 5000);
    }

    $('[data-toggle="tooltip"]').tooltip();

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            if ($('#messageModal').hasClass('show')) {
                // if Enter key is pressed and message modal (popup used for error messages) is open -> trigger close
                $('#messageModal button[data-dismiss="modal"]').trigger('click');
            } else if ($('#advanced-options-modal').hasClass('show')) {
                // if Enter key is pressed and Advanced Options modal is open
                if (document.activeElement.id == "option-user-pred") {
                    // if text field to add new predicates is active -> submit predicate
                    $('#add-pred').trigger('click');
                    event.stopPropagation();
                } else {
                    // submit modal / form data
                    $('#advanced-options-modal button[type="submit"]').trigger('click');
                }
            } else if ($('#upload-modal').hasClass('show')) {
                // if Enter key is pressed and upload modal is open -> trigger submit
                $('#upload-modal button[type="submit"]').trigger('click');
                event.preventDefault();
            }
        }
    });

    // add a controller file
    $('#add-controller-file').on("change", function (){
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (! validControllerFile(fileName)) {
            popupModal("Error: Invalid Controller File", "Supported file formats: " + inputFormats.join(", "))
            // TODO T: test formats...
            return ;
        }
        let formData = new FormData();
        formData.append("file", document.getElementById("add-controller-file").files[0]);
        $.ajax({
            // From https://stackoverflow.com/a/8758614
            // Your server script to process the upload
            url: '/upload',
            type: 'POST',
            // Form data
            data: formData,
            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,
            beforeSend: () => {
                // add loading animation in button
                var spinner = $('<span>', {class: 'spinner-border spinner-border-sm', role: 'status', 'aria-hidden': 'true'});
                let btn = $('#add-controller-button');
                btn.html(spinner);
                btn.append(" Uploading...");
                btn[0].disabled = true;
            },
        }).done(() => {
            // reset the button
            var plus = $('<i>', {class: 'fa fa-plus', style: 'font-size: 80%', 'aria-hidden': 'true'});
            let btn = $('#add-controller-button');
            btn.html(plus);
            btn.append(" Add new controller file");
            btn[0].disabled = false;

            // initialize controller table
            var controller = $("#add-controller-file").val().replace('C:\\fakepath\\', "");
            var nice_name = controller;
            if (nice_name.startsWith("/")) {
                nice_name = nice_name.substr(1);
            }
            initializeControllerTable([controller, nice_name]);
        });
    })

    // show modal to upload controller and metadata file
    $('#add-controller-metadata-button').on('click', function () {
        $('#upload-modal').modal('show');
    });

    // add a controller file from modal where controller file and metadata file can be added
    $('#controller-file-upload').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (! validControllerFile(fileName)) {
            // file extension not allowed
            $('#controller-type-help')[0].style.visibility = 'visible';
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            document.getElementById("submit-file-button").disabled = true;
            $('#controller-file-upload').val('');
            return ;
        } else {
            $('#controller-type-help')[0].style.visibility = 'hidden';
            $(this).removeClass('is-invalid');
            $(this).addClass('is-valid');
        }
        //replace the "Choose controller file" label
        $(this).next('.custom-file-label').html(fileName);
        $('#controller-file-upload-progress-bar').attr({
            'aria-valuenow': 0
        })
            .width("0%");
        let formData = new FormData();
        formData.append("file", document.getElementById("controller-file-upload").files[0]);
        $.ajax({
            // From https://stackoverflow.com/a/8758614
            // Your server script to process the upload
            url: '/upload',
            type: 'POST',

            // Form data
            data: formData,

            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,

            // Custom XMLHttpRequest
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            $('#controller-file-upload-progress-bar').attr({
                                'aria-valuenow': Math.round(e.loaded * 100 / e.total)
                            })
                                .width(Math.round(e.loaded * 100 / e.total)+"%");
                        }
                    }, false);
                }
                return myXhr;
            }
        }).done(() => {
            document.getElementById("submit-file-button").disabled = false;
        });
    });

    // add a metadata file from modal where controller file and metadata file can be added
    $('#metadata-file-upload').on('change', function () {
        //get the file name
        let metadataFileName = $(this).val().replace('C:\\fakepath\\', "");
        let fileName = $('#controller-file-upload').val().replace('C:\\fakepath\\', "");
        let correctName = fileName.substr(0, fileName.lastIndexOf('.')) + "_config.json";
        if (fileName != "" && metadataFileName != correctName) {
            $('#metadata-type-help')[0].innerText = "The metadata file has to be named '" + correctName + "'.";
            $('#metadata-type-help')[0].style.visibility = 'visible';
            $(this).addClass('is-invalid');
            $(this).removeClass('is-valid');
            $('#metadata-file-upload').val('');
            return ;
        } else if (!metadataFileName.endsWith(".json")) {
            $('#metadata-type-help')[0].style.visibility = 'visible';
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            $('#metadata-file-upload').val('');
            return ;
        } else {
            $('#metadata-type-help')[0].style.visibility = 'hidden';
            $(this).removeClass('is-invalid');
            $(this).addClass('is-valid');
        }
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(metadataFileName);
        let formData = new FormData();
        formData.append("file", document.getElementById("metadata-file-upload").files[0]);
        $.ajax({
            // From https://stackoverflow.com/a/8758614
            // Your server script to process the upload
            url: '/upload',
            type: 'POST',

            // Form data
            data: formData,

            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,

            // Custom XMLHttpRequest
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            $('#metadata-file-upload-progress-bar').attr({
                                'aria-valuenow': Math.round(e.loaded * 100 / e.total)
                            })
                                .width(Math.round(e.loaded * 100 / e.total)+"%");
                        }
                    }, false);
                }
                return myXhr;
            }
        });
    });

    function validControllerFile(fileName) {
        for (let i = 0; i < inputFormats.length; i++) {
            if (fileName.endsWith(inputFormats[i])) {
                return true;
            }
        }
        return false;
    }

    // reset the upload modal when it is closed
    $('#upload-modal').on('hidden.bs.modal', function () {
        // clear input fields
        $('#controller-file-upload').val('');
        $('#metadata-file-upload').val('');

        // reset the custom file labels
        $('.custom-file-label[for="controller-file-upload"]').text('Choose controller file');
        $('.custom-file-label[for="metadata-file-upload"]').text('Choose metadata file');
    
        // reset progress bars
        $('#controller-file-upload-progress-bar').css('width', '0%');
        $('#metadata-file-upload-progress-bar').css('width', '0%');
    
        // reset error messages
        $('#metadata-type-help')[0].style.visibility = 'hidden';
        $('#controller-type-help')[0].style.visibility = 'hidden';
        $('#metadata-file-upload').removeClass('is-invalid');
        $('#metadata-file-upload').removeClass('is-valid');
        $('#controller-file-upload').removeClass('is-invalid');
        $('#controller-file-upload').removeClass('is-valid');

        // disable submit button
        document.getElementById("submit-file-button").disabled = true;
    });

    $('#submit-file-button').on('click', function() {
        let fileName = $('#controller-file-upload').val().replace('C:\\fakepath\\', "");

        // check if controller file uploaded
        if (fileName == "") {
            // submit button should not even be activated if no file uploaded
            console.error("Error when submitting file: No file uploaded.")
            return ;
        }

        // check if metadata file has correct name
        let metadataFileName = $('#metadata-file-upload').val().replace('C:\\fakepath\\', "");
        let correctName = fileName.substr(0, fileName.lastIndexOf('.')) + "_config.json";
        if (metadataFileName != "" && metadataFileName != correctName) {
            // metadata file was uploaded, but not right name
            $('#metadata-type-help')[0].innerText = "The metadata file has to be named '" + correctName + "'.";
            $('#metadata-type-help')[0].style.visibility = 'visible';
            $('#metadata-file-upload').addClass('is-invalid');
            $('#metadata-file-upload').removeClass('is-valid');
            return ;
        }

        // controller file was uploaded and metadata file was either not uploaded or uploaded with correct name
        var controller = $("#controller-file-upload").val().replace('C:\\fakepath\\', "");
        var nice_name = controller;
        if (nice_name.startsWith("/")) {
            nice_name = nice_name.substr(1);
        }
        initializeControllerTable([controller, nice_name]);
        $('#upload-modal').modal('hide');
        
        // TODO T: we are not doing anything with the metadata file!

        return ;
    });

    function initializeControllerTable(row_contents) {
        // Row contents at this point is [controller_name, nice_name]
        $.ajax('/controllers/initialize', {
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(row_contents),
            success: function(cont_id) {
                row_contents = [cont_id].concat(row_contents)
                // Row contents is now [controller_id, controller_name, nice_name]

                var table = document.getElementById("controller-table");
                var thead = table.getElementsByTagName('thead')[0];
                var tbody = table.getElementsByTagName('tbody')[0];

                var row = tbody.insertRow(-1);
                addToControllerTable(row_contents, row);

                var spanningCell = row.insertCell(-1);
                var numColumns = thead.rows[0].cells.length;
                spanningCell.colSpan = numColumns;
                var spinner = $('<span>', {class: 'spinner-border spinner-border-sm', role: 'status', 'aria-hidden': 'true'});
                $(spanningCell).html(spinner);
                $(spanningCell).append(" Parse dataset...");

                parseControllerFile(row_contents, row)
            },
            error: function(xhr) {
                if (xhr.status === 500 && xhr.responseJSON && xhr.responseJSON.error === "duplicate") {
                    popupModal("Error: Duplicate found", "A controller with this name was already uploaded.");
                }
            }
        });
    }

    function addToControllerTable(row_contents, row=null) {
        // This function is called
        // 1. to initialize the table when a new controller file was uploaded
        // 2. to populate the controller table when the controller file was parsed
        // 3. to populate the controller table when the page is refreshed

        // Table columns
        // 0: controller id
        // 1: controller (hidden)
        // 2: nice name
        // 3: # states
        // 4: # state-action pairs
        // 5: variable types
        // 6: state variables
        // 7: output variables
        // 8: maximum non-determinism
        // 9: actions

        // row_contents is an array
        // TODO T: change to dict?

        $("#controller-table tr.special").hide();
        if (row == null) {
            // create a new row
            var table = document.getElementById("controller-table").getElementsByTagName('tbody')[0];
            row = table.insertRow(-1);
        } else {
            // delete everything currently in that row
            while (row.cells.length > 0) {
                row.deleteCell(0);
            }
        }

        var firstCell = row.insertCell(-1);
        firstCell.outerHTML = "<th scope=\"row\">" + String(row_contents[0]) + "</th>";

        var secondCell = row.insertCell(-1);
        secondCell.innerHTML = row_contents[1];
        secondCell.style = "display: none";

        var thirdCell = row.insertCell(-1);
        thirdCell.innerHTML = row_contents[2];

        if (row_contents.length > 3) {
            for (let j = 3; j < 9; j++) {
                var c = row.insertCell(-1);
                c.innerHTML = row_contents[j];
            }
            // add the actions
            var icon = row.insertCell(-1);
            var det_tree_button = makeButton("Run deterministic", "det-build-button-cont-table", "preset-btn", "fa-play text-success", "build a deterministic tree using the options 'axisonly' and 'linear-logreg' to find splits");
            var aa_permissive_tree_button = makeButton("Run axis-aligned permissive", "aa-permissive-build-button-cont-table", "preset-btn", "fa-play text-success", "build a permissive tree using only axis-aligned splits");
            var logreg_permissive_tree_button = makeButton("Run logreg permissive", "logreg-permissive-build-button-cont-table", "preset-btn", "fa-play text-success", "build non-deterministic tree using the options 'axisonly' and 'linear-logreg' to find splits");
            var advanced_settings_button = makeButton("Show advanced", "advanced-button-cont-table", "", "fa-gears", "choose from the advanced settings");
            var edit_button =  makeButton("Go to tree builder", "edit-button-cont-table", "", "fa-wrench", "jump directly to the interactive tree builder");
            var delete_button = makeButton("Delete", "delete-button-cont-table", "", "fa-trash text-danger", "delete this controller file");
            // we could also use other nice icons from font-awesome: fa-tree, fa-sitemap (looks like a decision tree)
            icon.innerHTML = det_tree_button +
                aa_permissive_tree_button +
                logreg_permissive_tree_button +
                advanced_settings_button +
                edit_button + delete_button;
        }
    }

    function makeButton(text, id, btn_class="", fa_symbol=null, description="", font_size=80) {
        // e.g. "fa-plus" as fa_symbol
        if (fa_symbol) {
            return '<button class="btn btn-light m-1 ' + String(btn_class) + ' " data-toggle="tooltip" title=" ' + String(description) + '" id="' + String(id) + '"> <i class="fa ' + String(fa_symbol) +
                ' " style="font-size: ' + String(font_size) + ' % "> </i> ' + String(text) + '</button>';
        } else {
            return '<button class="btn btn-light " id=' + String(id) + '>' + String(text) + '</button>';
        }
    }

    function parseControllerFile(row_contents, row) {
        // Row contents at this point is [controller_id, controller_name, nice_name]
        $.ajax('/controllers', {
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(row_contents),
            // controller data is added to the backend table
        }).done(function(row_contents) {
            addToControllerTable(row_contents, row);
        });
    }

    function initControllerTableListeners() {
        // react to clicks in controller table (buttons, advanced options modal...)
        
        // clicks on preset buttons
        $("#controller-table").on("click", ".preset-btn", function () {
            $(this).blur();

            var buttonId = $(this).attr("id");
            var preset = null;
            // find out which preset-btn was clicked
            switch (buttonId) {
                case "det-build-button-cont-table":
                    preset = "deterministic";
                    break;
                case "aa-permissive-build-button-cont-table":
                    preset = "axisonly-permissive";
                    break;
                case "logreg-permissive-build-button-cont-table":
                    preset = "logreg-permissive";
                    break;
                default:
                    console.error("Unknown preset button from controller table clicked: ", buttonId);  
            }

            var row_items = $(this).parent().parent().find('th,td');
            let config = {
                id: row_items[0].innerHTML,
                controller: row_items[1].innerHTML,
                nice_name: row_items[2].innerHTML,
                config: preset
            };

            $.ajax('/results/initialize', {
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify(config),
                success: function(row_contents) {
                    runSingleBenchmark(row_contents);
                }
            });
        });

        // TODO T: I don't think we wanted this when planning... 
        // delete a controller, i.e. a row of the controller table
        $("#controller-table").on("click", "#delete-button-cont-table", function () {
            const row = $(this).parent().parent();
            var row_items = $(this).parent().parent().find('th,td');
            var row_content = [];
            row_items.each(function (k, v) {
                row_content.push(v.innerHTML);
            });
            row_content = row_content.slice(0, -1); // Drop the actions
            row_content[5] = row_content[5].split(","); // convert the variable types to an array
            $.ajax('/controllers/delete', {
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify(row_content),
                success: () => {
                    row.remove();
                    if (document.getElementById("controller-table").getElementsByTagName('tbody')[0].children.length == 1) {
                        $("#controller-table tr.special").show();      // show instruction when table empty
                    }
                }
            });
        });

        // click button to tree builder
        $('#controller-table').on('click', '#edit-button-cont-table', function () {
            console.log("jump to tree builder");
            // TODO T
        });

        // open advanced options modal
        $('#controller-table').on('click', '#advanced-button-cont-table', function () {
            $('#advanced-options-modal').modal('show');
            var row_items = $(this).parent().parent().find('th,td');
            document.getElementById("hidden-controller-id").value = row_items[0].innerHTML;
            document.getElementById("hidden-controller-name").value = row_items[1].innerHTML;
            document.getElementById("modal-subtitle").innerHTML = row_items[2].innerHTML;
        });

        // show the tolerance checkbox if (and only if) valuegrouping checked
        $("#option-categorical-predicates").on("change", "#valuegrouping", function () {
            if ($(this).prop('checked')) {
                $('#tolerance-label').css('visibility', 'visible');
                $('#tolerance-field').css('visibility', 'visible');
            } else {
                $('#tolerance-label').css('visibility', 'hidden');
                $('#tolerance-field').css('visibility', 'hidden');
            }
        });

        // add a user predicate
        $('#add-pred').on('click', function (event) {
            event.preventDefault();
            let predicate = document.getElementById('option-user-pred').value;

            $.ajax({
                data: JSON.stringify({"predicate": predicate}),
                type: 'POST',
                contentType: "application/json; charset=utf-8",
                url: '/check-user-predicate',
            }).done(data => {
                let response = JSON.parse(data);
                if (response.type === "error") {
                    $('#user-pred-error-msg')[0].innerText = "The predicate does not have a valid structure.";
                    $('#user-pred-error-msg')[0].style.visibility = 'visible';
                } else if (response.type === "success") {
                    var pred = response["body"]
                    // duplicate check
                    var table = document.getElementById('user-pred-table-modal').getElementsByTagName('tbody')[0];
                    for (var i = 0; i < table.rows.length; i++) {
                        var entry = table.rows[i].cells[0].innerText;
                        if (entry === pred) {
                            $('#user-pred-error-msg')[0].innerText = "The predicate has already been added.";
                            $('#user-pred-error-msg')[0].style.visibility = 'visible';
                            return;
                        }
                    }
                    $('#user-pred-error-msg')[0].style.visibility = 'hidden';

                    // add predicate to collection in modal
                    var table_body = document.getElementById("user-pred-table-modal").getElementsByTagName('tbody')[0];
                    var row = table_body.insertRow(-1);
                    var pred_cell = row.insertCell(-1);
                    pred_cell.innerHTML = pred;
                    var icon = row.insertCell(-1);
                    icon.innerHTML = "<i class=\"fa fa-trash text-danger\"></i>";
                }
            });
        });

        // delete a user predicate
        $("#user-pred-table-modal").on("click", "i.fa-trash", function () {
            const row = $(this).parent().parent();
            row.remove();
        });

        // button to restore default values in advanced options modal
        $('#restore-default-button').on('click', function () {
            $(this).blur();
            if(document.getElementById("maxfreq") != null) {
                document.getElementById("option-determinize").options["maxfreq"].selected = true;
            }
            // TODO T: check if numerical and cat predicates options present
            if(document.getElementById("axisonly") != null) {
                let numeric_checkboxes = document.getElementById("option-numeric-predicates").children;
                for (let i = 0; i < numeric_checkboxes.length; i++) {
                    numeric_checkboxes[i].children[0].checked = false;
                }
                document.getElementById("axisonly").checked = true;
            }
            if(document.getElementById("multisplit") != null) {
                let cat_checkboxes = document.getElementById("cat-pred-div").children;
                for (let i = 0; i < cat_checkboxes.length; i++) {
                    cat_checkboxes[i].children[0].checked = false;
                }
                // Trigger the change event manually for event handler that makes Tolerance field (dis)appear
                $("#cat-pred-div input[type='checkbox']").trigger('change');
                document.getElementById("multisplit").checked = true;
            }
            $('#user-pred-error-msg')[0].style.visibility = 'hidden';
            $('#option-user-pred')[0].value = "x_0 + 3*x_1 <= c_0; c_0 in {20, 40, 60}";
        });

        // react if the form in the advanced options modal is submitted
        $('#tree-builder-form').on('submit', function (event) {
            event.preventDefault();
            if (document.activeElement.id == "option-user-pred") {
                return;
            }
            document.getElementById('cat-pred-error-msg').style.visibility = 'hidden';
            document.getElementById('num-pred-error-msg').style.visibility = 'hidden';

            var selected_num_predicates = [];
            $('#option-numeric-predicates .form-check-input:checked').each(function() {
                var checkboxValue = $(this).attr('name');
                selected_num_predicates.push(checkboxValue);
            });

            // TODO: show numerical / categorical choices only if numerical/categorical variables present
            if (selected_num_predicates.length == 0) {
                document.getElementById('num-pred-error-msg').style.visibility = 'visible';
                return;
            }

            var selected_cat_predicates = [];
            $('#option-categorical-predicates .form-check-input:checked').each(function() {
                let checkboxValue = $(this).attr('name');
                selected_cat_predicates.push(checkboxValue);
            });
            if (selected_cat_predicates.length == 0) {
               document.getElementById('cat-pred-error-msg').style.visibility = 'visible';
                return;
            }

            $('#advanced-options-modal').modal('hide');
            document.getElementById('user-pred-error-msg').style.visibility = 'hidden';

            var tolerance = -1;  // tolerance only used if valuegrouping checked
            if (selected_cat_predicates.includes('valuegrouping')) {
                tolerance = document.getElementById('#tolerance-field').value
            }

            var chosen_determinize = document.getElementById("option-determinize").value;
            var chosen_impurity = "entropy";
            // in CLI + old GUI + backend: "multilabelentropy" was a choice for the impurity
            // had to be combined with "determinize: auto" bc multilabelentropy automatically determinizes
            // in new GUI: multilabelentropy is displayed as a choice for the determinization
            // and we choose impurity automatically depending on the determinization
            if (chosen_determinize === "multilabelentropy") {
                chosen_determinize = "auto";
                chosen_impurity = "multilabelentropy";
            }

            let config = {
                id: parseInt(document.getElementById("hidden-controller-id").value),
                controller: document.getElementById("hidden-controller-name").value,
                nice_name: document.getElementById("modal-subtitle").innerHTML,
                config: "custom",
                determinize: chosen_determinize,
                numeric_predicates: selected_num_predicates,
                categorical_predicates: selected_cat_predicates,
                impurity: chosen_impurity,
                tolerance: tolerance,
                safe_pruning: false,    // TODO T
                user_predicates: null   // TODO T
            };
            $.ajax('/results/initialize', {
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify(config),
                success: function(row_contents) {
                    runSingleBenchmark(row_contents);
                }
            });
        });
    }

    function runSingleBenchmark(config) {
        /*
        config is a dict with:
            "res_id"
            "cont_id"
            "controller"
            "nice_name"
            "config" (preset)
            "determinize"
            "numeric_predicates"
            "catergorical_predicates"
            "impurity"          # TODO
            "tolerance"         # TODO
            "safe_pruning"    # TODO 
            "status"
            "user prediactes"
        */
        if (config["status"] != "Running") {
            console.error("Try to run a benchmark for configuration with status ", config["status"]);
        }
        $.ajax({
            data: JSON.stringify(config),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/construct',
            beforeSend: addToResultsTable(config)
        }).done(data => addToResultsTable(data));
    }

    function addToResultsTable(result) {
        // This function is called
        // 1. to initialize the table when a new experiment is started
        // 2. to populate the results table when results arrive from polling
        // 3. to populate the results table when the page is refreshed

        // Table columns
        // 0: result id (unique, hidden)
        // 1: controller id
        // 2: controller (hidden)
        // 3: nice name 
        // 4: determinize
        // 5: predicates (numeric and categorical)
        // 6: nodes (inner nodes and leaf nodes)
        // 7: status
        // 8: construction_time
        // 9: actions

        // result is a dict with these possible keys:
        // res_id, cont_id, controller, nice_name, config, determinize, numeric_predicates, categorical_predicates,
        // impurity, tolerance, safe_pruning, inner_nodes, leaf_nodes, status, construction_time

        $("#results-table tr.special").hide();
        var table = document.getElementById("results-table").getElementsByTagName('tbody')[0];
        var res_id = result.res_id;
        var resultsRow = getResultsTableRow(res_id);

        if (!resultsRow) {
            // create a new row and fill it
            resultsRow = table.insertRow(-1);
            for (let j = 0; j <= 9; j++) {
                const cell = resultsRow.insertCell(-1);
                switch (j) {        // feel free to refactor this...
                    case 0:
                        cell.innerHTML = result.res_id;
                        cell.style = "display: none";
                        break;
                    case 1:
                        cell.outerHTML = '<th scope="row">' + result.cont_id + '</th>';
                        break;
                    case 2:
                        cell.innerHTML = result.controller;
                        cell.style = "display: none";
                        break;
                    case 3:
                        cell.innerHTML = result.nice_name;
                        break;
                    case 4:
                        if (result.determinize === "auto") {
                            cell.innerHTML = "multilabelentropy"
                        } else {
                            cell.innerHTML = result.determinize;
                        }
                        break;
                    case 5:
                        if ("numeric_predicates" in result) {
                            cell.innerHTML = result.numeric_predicates.join(', ');
                        }
                        if ("numeric_predicates" in result && "categorical_predicates" in result) {
                            cell.innerHTML += ", ";
                        }    
                        if ("categorical_predicates" in result) {
                            cell.innerHTML += result.categorical_predicates.join(', ');
                        }            
                        break;
                    case 6:
                        if (result.status === "Completed") {
                            cell.innerHTML = result.inner_nodes + " inner, " + result.leaf_nodes + " leafs";
                        }
                        break;
                    case 7:
                        if (result.status === "Running") {
                            cell.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
                        } else {
                            cell.innerHTML = result.status;
                        }
                        break;
                    case 8:
                        if (result.status === "Completed") {
                            cell.innerHTML = result.construction_time.milliSecondsToHHMMSS();
                        }
                        break;
                    default:
                        break;
                }
            }
        } else if (result.status === "Completed") {
            // if row already existed: update it
            resultsRow.children[6].innerHTML = result.inner_nodes + " inner, " + result.leaf_nodes + " leafs";
            resultsRow.children[7].innerHTML = result.status;
            resultsRow.children[8].innerHTML = result.construction_time.milliSecondsToHHMMSS();
        } else if (result.status === "Edited") {
            // TODO T: we don't know them?
            resultsRow.children[6].innerHTML = "";
            resultsRow.children[7].innerHTML = result.status;
            resultsRow.children[8].innerHTML = "";
        } else if (result.status.startsWith("Error")) {
            // don't overwrite other attributes with faulty values
            // depends on error what might make sense here
            resultsRow.children[7].innerHTML = result.status;
        }
        // no case for result.status === "Running" because the status of an existing row will never change to "Running"

        if (result.status != "Running") {
            // set up action buttons: eye and trash can
            resultsRow.children[9].innerHTML = '<i class="fa fa-eye text-primary"></i>&nbsp;&nbsp;<i class="fa fa-trash text-danger"></i>';
            $(resultsRow.children[9]).find('i.fa-eye').on('click', () => {
                $.post('/select', {runConfigIndex: res_id}, () => {
                    window.location.href = 'simulator'
                });
            });
            $(resultsRow.children[9]).find('i.fa-trash').on('click', () => {
                $.post('/results/delete', {id: res_id}, () => {
                    resultsRow.remove();
                    if (document.getElementById("results-table").getElementsByTagName('tbody')[0].children.length == 1) {
                        $("#results-table tr.special").show();
                    }
                });
            });
        }
    }

    function getResultsTableRow(res_id) {
        // every result has a unique id in the first (hidden) column of the results table
        let rows =$("#results-table tbody tr");
        for (let j = 0; j < rows.length; j++) {
            const result_id = rows[j].children[0].innerHTML;
            if (result_id == res_id) {
                return rows[j];
            }
        }
    }

    Number.prototype.milliSecondsToHHMMSS = function () {
        var sec_num = this;
        var hours = Math.floor(sec_num / 3600);
        var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
        var seconds = sec_num - (hours * 3600) - (minutes * 60);

        if (hours < 10) {
            hours = "0" + hours;
        }
        if (minutes < 10) {
            minutes = "0" + minutes;
        }
        if (seconds < 10) {
            seconds = "0" + seconds;
        }
        return hours + ':' + minutes + ':' + seconds;
    }
});