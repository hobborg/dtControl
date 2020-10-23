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
            data1 = JSON.parse(http.responseText);
            if (data1["status"] == 1) {
                select_menu = document.getElementById("controller");
                select_menu.innerHTML = "";
                files = data1["files"];
                for (var i = 0; i < files.length; i++) {
                    const option = document.createElement('option');
                    controller_name = files[i].replace(path, "");
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
                select_menu = document.getElementById("controller");
                select_menu.innerHTML = "";
                select_menu.appendChild(option);
            }
        }
    }
    http.send(params);
}

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
    // 0: id
    // 1: controller
    // 2: nice_name
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
            $(experimentRow.children[8]).find('i.fa-eye').on('click', (event) => {
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
                let filtered = Object.fromEntries(Object.entries(results).filter(([k, v]) => v.status === "Completed"));
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
    document.getElementById("add-experiments-button").disabled = true;
    $(".runall").hide();

    //MJ load data and init listeners
    $.get('/experiments', experiments => experiments.forEach(e => addToExperimentsTable(e))).then(() => initTableListeners());
    $.get('/results', results => {
        for (const [id, result] of Object.entries(results)) {
            addToResultsTable(id, result);
            if (result.status === "Running...") {
                startPolling();
            }
        }
    });

    // Load Button pressed
    $("#controller-directory-load").click(function () {
        // Reactive Add-Button
        document.getElementById("add-experiments-button").disabled = false;
        loadControllers($("#controller-search-directory").val());
    });

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

    function run_single_benchmark(config) {
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
        $("table").on("click", "i.fa-trash", function () {
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

        $("table").on("click", "i.fa-play", function (event) {
            if ($(this).id === 'runall-icon') return;
            var row_items = $(this).parent().parent().find('th,td');
            var row_content = []
            row_items.each(function (k, v) {
                row_content.push(v.innerHTML);
            });
            run_single_benchmark(row_content.slice(0, -1));
        });

        $('#runall').on('click', event => {
            $("table i.fa-play").each((_, btn) => {
                if (btn.id === 'runall-icon') return;
                console.log(btn);
                btn.click();
            });
        })
    }
});