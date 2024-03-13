// supported file formats for the controller files
var inputFormats = [".scs", ".dump", ".csv", ".prism", ".storm.json"]
// see extension_to_loader in dataset.py and get_files(path) in benchmark_suite.py
// TODO T: if not p.endswith('_states.prism') ? + put somewhere else...

    /* TODO T: this is never used bc only used in: $("#controller-directory-load").click(function () {
function loadControllers(path) {
    console.log(path);

    var http = new XMLHttpRequest();
    var url = '/examples';
    var params = 'location=' + encodeURIComponent(path);
    http.open('POST', url, true);

    //Send the proper header information along with the request
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            let data1 = JSON.parse(http.responseText);
            if (data1["status"] == 1) {
                let select_menu = document.getElementById("controller");
                select_menu.innerHTML = "";
                let files = data1["files"];
                for (var i = 0; i < files.length; i++) {
                    const option = document.createElement('option');
                    let controller_name = files[i].replace(path, "");
                    if (controller_name.startsWith("/")) {
                        controller_name = controller_name.substr(1);
                    }
                    option.textContent = controller_name;
                    option.setAttribute('value', files[i]);
                    if (files[i] === '10rooms.scs') {
                        option.setAttribute('selected', 'selected');
                    }
                    select_menu.appendChild(option);
                }
            } else {
                console.log("Folder doesn't exist");
                const option = document.createElement("option");
                option.textContent = "Enter valid controller directory";
                option.setAttribute('selected', 'selected');
                let select_menu = document.getElementById("controller");
                select_menu.innerHTML = "";
                select_menu.appendChild(option);
            }
        }
    }
    http.send(params);
}
*/

// TODO T: not needed anymore
function getResultsTableRow(id) {
    let rows = $("#results-table tbody tr");
    for (let j = 0; j < rows.length; j++) {
        const experiment_id = rows[j].children[0].innerHTML;
        if (experiment_id == id) {
            return rows[j];
        }
    }
}

function addToResultsTable(id, result) {
    // This function is called both when
    // 1. a new experiment is started
    // 2. to populate the results table when results arrive from polling
    // 3. to populate the results table when the page is refreshed

    // Table columns
    // 0: experiment id
    // 1: controller
    // 2: nice_name     # TODO: what is this? get rid of it?
    // 3: preset
    // 4: status
    // 5: inner_nodes
    // 6: leaf_nodes
    // 7: construction_time
    function createRow(table_selector, id, row_data) {
        let experimentRow = table_selector.insertRow(-1);
        let firstCell = experimentRow.insertCell(-1);
        firstCell.outerHTML = "<th scope=\"row\">" + String(id) + "</th>";
        for (let j = 1; j <= 7; j++) {
            const cell = experimentRow.insertCell(-1);
            switch (j) {
                case 1:
                    cell.style = "display: none";
                    cell.innerHTML = row_data.controller;
                    break;
                case 2:
                    cell.innerHTML = row_data.nice_name;
                    break;
                case 3:
                    cell.innerHTML = row_data.preset;
                    break;
                case 4:
                    cell.innerHTML = row_data.status;
                    break;
                case 5:
                    cell.innerHTML = row_data.inner_nodes;
                    break;
                case 6:
                    cell.innerHTML = row_data.leaf_nodes;
                    break;
                case 7:
                    cell.innerHTML = row_data.construction_time.milliSecondsToHHMMSS();
                    break;
                default:
                    break;
            }
        }
        return experimentRow;
    }

    $("#results-table tr.special").hide();
    var table = document.getElementById("results-table").getElementsByTagName('tbody')[0];

    if (result.status === "Completed" || result.status === "Edited") {
        let experimentRow = getResultsTableRow(id);
        if (!experimentRow) {
            experimentRow = createRow(table, id, result);
        }

        experimentRow.children[4].innerHTML = result.status;
        if (result.status === "Completed") {
            experimentRow.children[5].innerHTML = result.inner_nodes;
            experimentRow.children[6].innerHTML = result.leaf_nodes;
            experimentRow.children[7].innerHTML = result.construction_time.milliSecondsToHHMMSS();
        }
        else {
            experimentRow.children[5].innerHTML = "";
            experimentRow.children[6].innerHTML = "";
            experimentRow.children[7].innerHTML = "";
        }

        if (experimentRow.children.length < 9) {
            let lastCell = experimentRow.insertCell(-1);
            lastCell.innerHTML = '<i class="fa fa-eye text-primary"></i>';
            $(experimentRow.children[8]).find('i.fa-eye').on('click', () => {
                $.post('/select', {runConfigIndex: id}, () => {
                    window.location.href = 'simulator'
                });
            });
        }
    }
    else if (result.status.startsWith("Error")) {
        let experimentRow = getResultsTableRow(id);
        if (experimentRow) {
            experimentRow.children[4].innerHTML = result.status;
        } else {
            experimentRow = createRow(table, id, result);
        }
    }
}

function startPolling() {
        console.log('start interval');
        const interval = setInterval(() => {
            $.get('/results', results => {
                console.log(results);
                let filtered = Object.fromEntries(Object.entries(results).filter(([, v]) => v.status === "Completed"));
                for (const [id, result] of Object.entries(filtered)) {
                    const row = getResultsTableRow(id);
                    if (row.children[3].innerHTML === 'Running...') {
                        addToResultsTable(result);
                    }
                }
                if (results.every(r => r[3] === 'Completed')) {
                    clearInterval(interval);
                }
            })
        }, 5000);
    }

$(document).ready(function () {
    // Disable Add-Button until controller directory is loaded
    // TODO T change here?
    document.getElementById("add-experiments-button").disabled = true;
    $(".runall").hide();

    //MJ load data and init listeners
    //$.get('/experiments', experiments => experiments.forEach(e => addToExperimentsTable(e)));.then(() => initTableListeners());
    $.get('/controllers', controllers => controllers.forEach(e => addToControllersTable(e))).then(() => initTableListeners());
    $.get('/results', results => {
        for (const [id, result] of Object.entries(results)) {
            addToResultsTable(id, result);
            if (result.status === "Running...") {
                startPolling();
            }
        }
    });

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
            }
        }
    });

    // Load Button pressed
    /* TODO T: this is never used bc id is in div in base.html that is commented out...
        delete? delete all the commented out html stuff?
    $("#controller-directory-load").click(function () {
        // Reactive Add-Button
        document.getElementById("add-experiments-button").disabled = false;
        loadControllers($("#controller-search-directory").val());
    });
    */

    function validControllerFile(fileName) {
        for (let i = 0; i < inputFormats.length; i++) {
            if (fileName.endsWith(inputFormats[i])) {
                return true;
            }
        }
        return false;
    }

    // add a controller file
    $('#add-controller-file').on("change", function (){
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (! validControllerFile(fileName)) {
            popupModal("Error: Invalid controller file", "Supported file formats: .scs, .dump, .csv, .prism, .storm.json")
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

    function initializeControllerTable(row_contents) {
        // Row contents at this point is [controller_name, nice_name]
        $.ajax('/controllers/initialize', {
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(row_contents[0]),
            success: function(cont_id) {
                row_contents = [cont_id].concat(row_contents)
                // Row contents is now [controller_id, controller_name, nice_name]

                var table = document.getElementById("controller-table");
                var thead = table.getElementsByTagName('thead')[0];
                var tbody = table.getElementsByTagName('tbody')[0];

                var row = tbody.insertRow(-1);
                addToControllersTable(row_contents, row);

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

    function addToControllersTable(row_contents, row=null) {
        $("#controller-table tr.special").hide();

        if (row == null) {
            var table = document.getElementById("controller-table");
            var tbody = table.getElementsByTagName('tbody')[0];
            row = tbody.insertRow(-1);
        } else {
            // delete everything currently in that row:
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
            var icon = row.insertCell(-1);
            var det_tree_button = makeButton(" deterministic", "det-build-button-cont-table", "fa-play text-success", "build a deterministic tree using the options 'axisonly' and 'linear-logreg' to find splits");
            var aa_permissive_tree_button = makeButton(" axis-aligned permissive", "aa-permissive-build-button-cont-table", "fa-play text-success", "build a permissive tree using only axis-aligned splits");
            var logreg_permissive_tree_button = makeButton(" logreg permissive", "logreg-permissive-build-button-cont-table", "fa-play text-success", "build non-deterministic tree using the options 'axisonly' and 'linear-logreg' to find splits");
            var advanced_settings_button = makeButton(" advanced", "advanced-button-cont-table", "fa-gears", "choose from the advanced settings");
            var edit_button =  makeButton(" tree builder", "edit-button-cont-table", "fa-wrench", "jump directly to the interactive tree builder");
            var delete_button = makeButton(" delete", "delete-button-cont-table", "fa-trash text-danger", "delete this controller file");
            // other nice icons from font-awesome: fa-tree, fa-sitemap (looks like a decision tree)
            icon.innerHTML = det_tree_button + aa_permissive_tree_button + logreg_permissive_tree_button +
                            advanced_settings_button +  edit_button + delete_button;
        }
    }

    function parseControllerFile(row_contents, row) {
        // Row contents at this point is [controller_id, controller_name, nice_name]
        //$(".runall").show();
        // TODO T: do we want that? yes i think so but not here

        $.ajax('/controllers', {
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(row_contents),
            // controller data is added to the backend table
        }).done(function(row_contents) {

            addToControllersTable(row_contents, row);

        });
    }

    $('#add-controller-metadata-button').on('click', function () {
        $('#upload-modal').modal('show');
    });

    // TODO T: refers to sidebar, delete when we get rid of it
    $('#controller-file').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
        $('#controller-file-upload-progress').attr({
            'aria-valuenow': 0
        })
            .width("0%");
        let formData = new FormData();
        formData.append("file", document.getElementById("controller-file").files[0]);
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
            beforeSend: () => {$('#add-experiments-button').text("Uploading...")},

            // Custom XMLHttpRequest
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            $('#controller-file-upload-progress').attr({
                                'aria-valuenow': Math.round(e.loaded * 100 / e.total)
                            })
                                .width(Math.round(e.loaded * 100 / e.total)+"%");
                        }
                    }, false);
                }
                return myXhr;
            }
        }).done(() => {
            document.getElementById("add-experiments-button").disabled = false;
            $('#add-experiments-button').text("Add");
        });
    });

    // add a controller file from modal where controller file and metadata file can be added
    $('#controller-file-upload').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (! validControllerFile(fileName)) {
            $('#controller-type-help')[0].style.visibility = 'visible';
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            document.getElementById("submit-file-button").disabled = true;
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

    $('#metadata-file-upload').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (!fileName.endsWith(".json")) {
            $('#metadata-type-help')[0].style.visibility = 'visible';
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            return ;
        } else {
            $('#metadata-type-help')[0].style.visibility = 'hidden';
            $(this).removeClass('is-invalid');
            $(this).addClass('is-valid');
        }
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
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

    // TODO: delete
    $('#metadata-file').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        if (!fileName.endsWith(".json")) {
            alert("Invalid metadata file. Expected a JSON file.");
            return ;
        }
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
        let formData = new FormData();
        formData.append("file", document.getElementById("metadata-file").files[0]);
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
                            $('#metadata-file-upload-progress').attr({
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

    // Add from sidenav
    // TODO T: delete when we delete sidebar
    $("input[name='add'], button[name='add']").on('click', function (event) {
        event.preventDefault();
        var controller = $("#controller-file").val().replace('C:\\fakepath\\', "");
        var nice_name = controller;
        if (nice_name.startsWith("/")) {
            nice_name = nice_name.substr(1);
        }
        var config = $('#config').val();
        var determinize = $('#determinize').val();
        var numeric_predicates = $('#numeric-predicates').val();
        var categorical_predicates = $('#categorical-predicates').val();
        var impurity = $('#impurity').val();
        var tolerance = $('#tolerance').val();
        var safe_pruning = $('#safe-pruning').val();
        var user_predicates = "";

        if (config == "algebraic") {
            config += " (Fallback: " + $("#fallback").val() + ")";
            numeric_predicates = [""];
            categorical_predicates = [""];
            user_predicates = $('#userPredicatesInput').val();
        }

        var row_contents = [controller, nice_name, config, determinize, numeric_predicates, categorical_predicates, impurity, tolerance, safe_pruning, user_predicates];

        $.ajax('/experiments', {
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(row_contents),
            success: () => addToExperimentsTable(row_contents)
        });
    });

    // TODO T: delete later
    function addToExperimentsTable(row_contents) {
        $("#experiments-table tr.special").hide();
        $(".runall").show();

        var table = document.getElementById("experiments-table").getElementsByTagName('tbody')[0];

        // Create an empty <tr> element and add it to the 1st position of the table:
        var row = table.insertRow(-1);
        var firstCell = row.insertCell(-1);
        firstCell.outerHTML = "<th scope=\"row\">" + String(table.rows.length - 2) + "</th>";

        // Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
        for (let j = 0; j < 10; j++) {
            var c = row.insertCell(-1);
            if (j == 0 || j == 9) {
                c.style = "display: none";
            }
            c.innerHTML = row_contents[j];
        }

        var icon = row.insertCell(-1);
        icon.innerHTML = "<i class=\"fa fa-trash text-danger\"></i>&nbsp;&nbsp;<i class=\"fa fa-play text-success\" aria-hidden=\"true\"></i>";
    }

    function makeButton(text, id, fa_symbol=null, description="", font_size=80) {
        // e.g. "fa-plus" as fa_symbol
        if (fa_symbol) {
            return "<button class=\"btn btn-light m-1 \"  data-toggle=\"tooltip\" title=\"" + String(description) + "\" id=\"" + String(id) + "\"> <i class=\"fa " + String(fa_symbol) +
                " \" style=\"font-size: " + String(font_size) + " % \"> </i>" + String(text) + "</button>";
        } else {
            return "<button class=\"btn btn-light \" id=\"" + String(id) + "\">" + String(text) + "</button>";
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

    // TODO: delete, rename other one
    function runSingleBenchmark(config) {
        console.log(config);
        $.ajax({
            data: JSON.stringify({
                id: config[0],
                controller: config[1],
                nice_name: config[2],
                config: config[3],
                determinize: config[4],
                numeric_predicates: config[5],
                categorical_predicates: config[6],
                impurity: config[7],
                tolerance: config[8],
                safe_pruning: config[9],
                user_predicates: config[10]
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/construct',
            beforeSend: initializeInResultsTable(config)
        }).done(data => addToResultsTable(config[0], data));
    }

    function runSingleBenchmark_new(config) {
        console.log(config);
        $.ajax({
            data: JSON.stringify(config),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/construct',
            beforeSend: initializeInResultsTable_new(config)
        }).done(data => addToResultsTable_new(config[0], data));
    }

    function initializeInResultsTable_new(config) {
        /*
                id: row_contents[0],
                controller: row_contents[1],
                nice_name: row_contents[2],
                config: row_contents[3],
                determinize: row_contents[4],
                numeric_predicates: row_contents[5],
                categorical_predicates: row_contents[6],
                impurity: row_contents[7],
                tolerance: row_contents[8],
                safe_pruning: row_contents[9]
             */
        // Create an empty <tr> element and add it to the 1st position of the table:
        $("#results-table-new tr.special").hide();
        let table = document.getElementById("results-table-new").getElementsByTagName('tbody')[0];
        let row = table.insertRow(-1);

        let firstCell = row.insertCell(-1);
        // TODO T: don't display id?
        console.log("config: ")
        console.log(config)
        firstCell.outerHTML = "<th scope=\"row\">" + config["id"] + "</th>";

        let cell_controller = row.insertCell(-1);
        cell_controller.innerHTML = config["controller"];
        cell_controller.style = "display: none";

        let cell_nice_name = row.insertCell(-1);
        cell_nice_name.innerHTML = config["nice_name"];

        let cell_det = row.insertCell(-1);
        cell_det.innerHTML = config["determinize"];

        let cell_preds = row.insertCell(-1);
        cell_preds.innerHTML = config["numeric_predicates"].join(', ');

        if ("categorical_predicates" in config) {
            cell_preds.innerHTML += ", " + config["categorical_predicates"];
        }

        let cell_nodes = row.insertCell(-1);
        let cell_construction_time = row.insertCell(-1);
        cell_construction_time.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...`;
        let cell_actions = row.insertCell(-1);

        /*
        for (let j = 1; j <= 7; j++) {
            if (j == 3) {
                continue;
            }
            const cell = row.insertCell(-1);
            if (j === 1) {
                cell.style = "display: none";
            }
            if (j <= 4) {
                cell.innerHTML = row_contents[j];
            }
            if (j === 5) {
                var spinner = $('<span>', {class: 'spinner-border spinner-border-sm', role: 'status', 'aria-hidden': 'true'});
                $(cell).html(spinner);
                $(cell).append(" Running...")
            }
        }
        */
    }

    function initializeInResultsTable(row_contents) {
        /*
                id: row_contents[0],
                controller: row_contents[1],
                nice_name: row_contents[2],
                config: row_contents[3],
                determinize: row_contents[4],
                numeric_predicates: row_contents[5],
                categorical_predicates: row_contents[6],
                impurity: row_contents[7],
                tolerance: row_contents[8],
                safe_pruning: row_contents[9]
             */
        // Create an empty <tr> element and add it to the 1st position of the table:
        $("#results-table tr.special").hide();
        let table = document.getElementById("results-table").getElementsByTagName('tbody')[0];
        let row = table.insertRow(-1);
        let firstCell = row.insertCell(-1);
        firstCell.outerHTML = "<th scope=\"row\">" + String(row_contents[0]) + "</th>";
        for (let j = 1; j <= 7; j++) {
            const cell = row.insertCell(-1);
            if (j === 1) {
                cell.style = "display: none";
            }
            if (j <= 3) {
                cell.innerHTML = row_contents[j];
            }
            if (j === 4) {
                cell.innerHTML = "Running...";
            }
        }
    }

    function initTableListeners() {
        // TODO T: delete
        $("#experiments-table").on("click", "i.fa-trash", function () {
            const row = $(this).parent().parent();
            const index = parseInt(row.find('th').textContent, 10) - 1;

            var row_items = $(this).parent().parent().find('th,td');
            var row_content = [];
            row_items.each(function (k, v) {
                row_content.push(v.innerHTML);
            });
            row_content = row_content.slice(1, -1); // Drop the index and the actions
            row_content[4] = row_content[4].split(","); // Numerical
            row_content[5] = row_content[5].split(","); // and categorical predicates as arrays

            $.ajax('/experiments/delete', {
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify(row_content),
                success: () => {
                    row.remove();
                    if (document.getElementById("experiments-table").getElementsByTagName('tbody')[0].children.length == 2) {
                        $(".runall").hide();
                        $("#experiments-table tr.special").show();
                    }
                }
            });
        });

        $("#controller-table").on("click", "#delete-button-cont-table", function () {
            const row = $(this).parent().parent();

            var row_items = $(this).parent().parent().find('th,td');
            var row_content = [];
            row_items.each(function (k, v) {
                row_content.push(v.innerHTML);
            });
            row_content = row_content.slice(0, -1); // Drop the actions

            row_content[4] = row_content[4].split(","); // convert the variable types to an array

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

        // TODO T: delete
        $("#experiments-table").on("click", "i.fa-play", function () {
            if ($(this).id === 'runall-icon') return;
            var row_items = $(this).parent().parent().find('th,td');
            var row_content = []
            row_items.each(function (k, v) {
                row_content.push(v.innerHTML);
            });
            runSingleBenchmark(row_content.slice(0, -1));
        });

        // TODO T: put these three blocks together?
        $("#controller-table").on("click", "#det-build-button-cont-table", function () {
            $(this).blur();
            var row_items = $(this).parent().parent().find('th,td');
            // TODO T: think about default choices, explain, only give cat preds if cat vars present
            let config = {
                id: row_items[0].innerHTML,
                controller: row_items[1].innerHTML,
                nice_name: row_items[2].innerHTML,
                determinize: "maxfreq",
                numeric_predicates: ["axisonly", "linear-logreg"],
                categorical_predicates: ["multisplit"],
                impurity: "multilabelentropy",
            };
            runSingleBenchmark_new(config);
        });

        $("#controller-table").on("click", "#aa-permissive-build-button-cont-table", function () {
            $(this).blur();
            var row_items = $(this).parent().parent().find('th,td');
            // TODO T: think about default choices, explain, only give cat preds if cat vars present
            let config = {
                id: row_items[0].innerHTML,
                controller: row_items[1].innerHTML,
                nice_name: row_items[2].innerHTML,
                determinize: "none",
                numeric_predicates: ["axisonly"],
                categorical_predicates: ["multisplit"],
                impurity: "multilabelentropy",
            };
            runSingleBenchmark_new(config);
        });

        $("#controller-table").on("click", "#logreg-permissive-build-button-cont-table", function () {
            $(this).blur();
            var row_items = $(this).parent().parent().find('th,td');
            // TODO T: think about default choices, explain, only give cat preds if cat vars present
            let config = {
                id: row_items[0].innerHTML,
                controller: row_items[1].innerHTML,
                nice_name: row_items[2].innerHTML,
                determinize: "none",
                numeric_predicates: ["axisonly", "linear-logreg"],
                categorical_predicates: ["multisplit"],
                impurity: "multilabelentropy",
            };
            runSingleBenchmark_new(config);
        });

        $('#controller-table').on('click', '#advanced-button-cont-table', function () {
            $('#advanced-options-modal').modal('show');
            var row_items = $(this).parent().parent().find('th,td');
            document.getElementById("hidden-controller-id").value = row_items[0].innerHTML;
            document.getElementById("hidden-controller-name").value = row_items[1].innerHTML;
            document.getElementById("modal-subtitle").innerHTML = row_items[2].innerHTML;
        });

        $('#controller-table').on('click', '#edit-button-cont-table', function () {
            console.log("jump to tree builder");
        });


        $("#option-categorical-predicates").on("change", "#valuegrouping", function () {
            console.log("sth changed about valuegrouping checkbox");
            if ($(this).prop('checked')) {
                console.log("valuegrouping checkbox is now checked");
                $('#tolerance-label').css('visibility', 'visible');
                $('#tolerance-field').css('visibility', 'visible');
            } else {
                $('#tolerance-label').css('visibility', 'hidden');
                $('#tolerance-field').css('visibility', 'hidden');
            }
        });

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

            var tolerance = 0;  // tolerance is always 0 if valuegrouping not checked
            if (selected_cat_predicates.includes('valuegrouping')) {
                tolerance = document.getElementById('#tolerance-field').value
            }

            // TODO T: think about default choices, explain, only give cat preds if cat vars present
            let config = {
                id: parseInt(document.getElementById("hidden-controller-id").value),
                controller: document.getElementById("hidden-controller-name").value,
                nice_name: document.getElementById("modal-subtitle").innerHTML,
                //config: "custom",
                determinize: document.getElementById("option-determinize").value,
                numeric_predicates: selected_num_predicates,
                categorical_predicates: selected_cat_predicates,
                impurity: "multilabelentropy",
                tolerance: tolerance,
                //safe_pruning: false,
                user_predicates: null // TODO
            };
            runSingleBenchmark_new(config);

            return false;
        });

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
        });

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
                    addToPredicateCollectionModal(pred);
                }
            });
        });

        function addToPredicateCollectionModal(pred) {
            var table_body = document.getElementById("user-pred-table-modal").getElementsByTagName('tbody')[0];
            var row = table_body.insertRow(-1);
            var pred_cell = row.insertCell(-1);
            pred_cell.innerHTML = pred;
            var icon = row.insertCell(-1);
            icon.innerHTML = "<i class=\"fa fa-trash text-danger\"></i>";
        }

        $("#user-pred-table-modal").on("click", "i.fa-trash", function () {
            const row = $(this).parent().parent();
            row.remove();
        });

        /*
        // TODO T: delete if we delete runall
        $('#runall').on('click', event => {
            $("table i.fa-play").each((_, btn) => {
                if (btn.id === 'runall-icon') return;
                console.log(btn);
                btn.click();
            });
        })
        */
    }
});