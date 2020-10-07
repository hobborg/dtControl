// Stores default config in config.yml
var defConf;

// Union of all configs present in config.yml
var allConfig = {};

// preset data json
var preset_json;

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

function fillYML(preset_json) {
    // Uses DOM manipulation to populate required forms after reading config.yml

    defConf = (preset_json.presets.default);
    var iter = 0;
    for (y in defConf) {
        allConfig[y] = [];
    }

    for (x in preset_json.presets) {
        //loop over preset names
        for (y in defConf) {
            //loop over properties
            if (y in preset_json.presets[x]) {
                //if that preset contains that property
                var valu = preset_json.presets[x][y];
                if (Array.isArray(valu)) {
                    for (z in valu) {
                        if (!allConfig[y].includes(valu[z])) {
                            allConfig[y].push(valu[z]);
                        }
                    }
                } else {
                    if (!allConfig[y].includes(valu.toString())) {
                        allConfig[y].push(valu);
                    }
                }

            }
        }
        iter++;
    }

    var det = document.getElementById("determinize");
    for (var i = 0; i < allConfig['determinize'].length; i++) {
        var opt = document.createElement('option');
        opt.textContent = allConfig['determinize'][i];
        opt.setAttribute('value', allConfig['determinize'][i]);
        opt.setAttribute('id', allConfig['determinize'][i]);
        det.appendChild(opt);
    }
    var det = document.getElementById("determinize_3");
    if (det) {
        for (var i = 0; i < allConfig['determinize'].length; i++) {
            var opt = document.createElement('option');
            opt.textContent = allConfig['determinize'][i];
            opt.setAttribute('value', allConfig['determinize'][i]);
            opt.setAttribute('id', allConfig['determinize'][i] + "_3");
            det.appendChild(opt);
        }
    }

    var det = document.getElementById("numeric-predicates");
    for (var i = 0; i < allConfig['numeric-predicates'].length; i++) {
        var opt = document.createElement('option');
        opt.textContent = allConfig['numeric-predicates'][i];
        opt.setAttribute('value', allConfig['numeric-predicates'][i]);
        opt.setAttribute('id', allConfig['numeric-predicates'][i] + "_3");
        det.appendChild(opt);
    }
    var det = document.getElementById("numeric-predicates_3");
    if (det) {
        for (var i = 0; i < allConfig['numeric-predicates'].length; i++) {
            var opt = document.createElement('option');
            opt.textContent = allConfig['numeric-predicates'][i];
            opt.setAttribute('value', allConfig['numeric-predicates'][i]);
            opt.setAttribute('id', allConfig['numeric-predicates'][i]);
            det.appendChild(opt);
        }
    }

    var det = document.getElementById("categorical-predicates");
    for (var i = 0; i < allConfig['categorical-predicates'].length; i++) {
        var opt = document.createElement('option');
        opt.textContent = allConfig['categorical-predicates'][i];
        opt.setAttribute('value', allConfig['categorical-predicates'][i]);
        opt.setAttribute('id', allConfig['categorical-predicates'][i] + "_3");
        det.appendChild(opt);
    }

    var det = document.getElementById("categorical-predicates_3");
    if (det) {
        for (var i = 0; i < allConfig['categorical-predicates'].length; i++) {
            var opt = document.createElement('option');
            opt.textContent = allConfig['categorical-predicates'][i];
            opt.setAttribute('value', allConfig['categorical-predicates'][i]);
            opt.setAttribute('id', allConfig['categorical-predicates'][i]);
            det.appendChild(opt);
        }
    }

    var det = document.getElementById("impurity");
    for (var i = 0; i < allConfig['impurity'].length; i++) {
        var opt = document.createElement('option');
        opt.textContent = allConfig['impurity'][i];
        opt.setAttribute('value', allConfig['impurity'][i]);
        opt.setAttribute('id', allConfig['impurity'][i]);
        det.appendChild(opt);
    }
    var det = document.getElementById("impurity_3");
    if (det) {
        for (var i = 0; i < allConfig['impurity'].length; i++) {
            var opt = document.createElement('option');
            opt.textContent = allConfig['impurity'][i];
            opt.setAttribute('value', allConfig['impurity'][i]);
            opt.setAttribute('id', allConfig['impurity'][i] + "_3");
            det.appendChild(opt);
        }
    }

    $("#config").trigger("change");

}

function loadPresets() {
    const app = document.getElementById('config');

    // All presets available for fallback
    const  fallback_app = document.getElementById("fallback");

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/yml', true);
    xhr.onload = function () {
        // Reads the config.yml file
        preset_json = JSON.parse(this.response);
        if (xhr.status >= 200 && xhr.status < 400) {
            for (x in preset_json.presets) {
                const option = document.createElement('option');
                option.textContent = x;
                option.setAttribute('value', x);
                if (x === 'mlentropy') {
                    option.setAttribute('selected', 'selected');
                }

                app.appendChild(option);
                const option_copy = option.cloneNode(true);
                fallback_app.appendChild(option_copy);

            }

            // Add custom to preset
            const option = document.createElement('option');
            option.textContent = "custom";
            option.setAttribute('value', "custom");
            app.appendChild(option);

            // Add interactive mode to preset
            const option2 = document.createElement('option');
            option2.textContent = "interactive";
            option2.setAttribute('value', "interactive");
            app.appendChild(option2);

            // Add automatic mode to preset
            const option3 = document.createElement('option');
            option3.textContent = "automatic";
            option3.setAttribute('value', "automatic");
            app.appendChild(option3);

            fillYML(preset_json);

        } else {
            console.log("YML not working");
            const errorMessage = document.createElement('marquee');
            errorMessage.textContent = `Gah, it's not working!`;
            app.appendChild(errorMessage);
        }
    }
    xhr.setRequestHeader('cache-control', 'no-cache, must-revalidate, post-check=0, pre-check=0');
    xhr.setRequestHeader('cache-control', 'max-age=0');
    xhr.setRequestHeader('expires', '0');
    xhr.setRequestHeader('expires', 'Tue, 01 Jan 1980 1:00:00 GMT');
    xhr.setRequestHeader('pragma', 'no-cache');
    xhr.send();
}

function startPolling() {
        console.log('start interval');
        const interval = setInterval(() => {
            $.get('/results', results => {
                console.log(results);
                results.filter(r => r[3] === 'Completed').forEach(r => {
                    const row = getResultsTableRow(r[0]);
                    if (row.children[3].innerHTML === 'Running...') {
                        addToResultsTable(r);
                    }
                });
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

    loadPresets();

    //MJ load data and init listeners
    $.get('/experiments', experiments => experiments.forEach(e => addToExperimentsTable(e))).then(() => initTableListeners());
    $.get('/results', results => {
        results.forEach(e => addToResultsTable(e));
        if (results.some(r => r[3] === 'Running...')) {
            startPolling();
        }
    });

    // Load Button pressed
    $("#controller-directory-load").click(function () {
        // Reactive Add-Button
        document.getElementById("add-experiments-button").disabled = false;
        loadControllers($("#controller-search-directory").val());
    });

    // Handles changing of form selections when different configs are changed
    $("#config").change(function () {
        if ($(this).val() != "custom" && $(this).val() != "interactive" && $(this).val() != "automatic") {
            // clearCheckBoxes();
            for (x in preset_json.presets) {
                //x is  preset names
                if ($(this).val() == x) {
                    //x is now selected preset
                    for (y in defConf) {
                        //y is  property names
                        if (y in preset_json.presets[x]) {
                            if (y == "tolerance") {
                                document.getElementById("tolerance").value = preset_json.presets[x][y];
                            } else if (y == "safe-pruning") {
                                if (preset_json.presets[x]["safe-pruning"]) {
                                    $('#safe-pruning').val("true");
                                } else {
                                    $('#safe-pruning').val("false");
                                }
                            } else {
                                $("#" + y).val(preset_json.presets[x][y]);
                            }
                        } else {
                            if (y == "tolerance") {
                                document.getElementById("tolerance").value = defConf[y];
                            } else if (y == "safe-pruning") {
                                if (preset_json.presets["default"]["safe-pruning"]) {
                                    $('#safe-pruning').val("true");
                                } else {
                                    $('#safe-pruning').val("false");
                                }
                            } else {
                                $("#" + y).val(preset_json.presets["default"][y]);
                            }
                        }
                    }

                    break;

                }
            }
        }
        else if ($(this).val() == "custom"){
            // In case custom is selected
            $('#accordionButton').click();
        }
        else if ($(this).val() == "interactive"){
            // In case interactive mode is selected
        }
        else if ($(this).val() == "automatic"){


            document.getElementById("userPredicatesInputRow").classList.remove("collapse");
            document.getElementById("fallbackSelectRow").classList.remove("collapse");

            document.getElementById("numericPredicatesSelectRow").classList.add("collapse");
            document.getElementById("categoricalPredicatesSelectRow").classList.add("collapse");
            document.getElementById("tolerance").value = 0.00001;
        }


    });

    // The 4 functions handle changing the 'config' of form to custom whenever there's a change in finer controls
    $(".propList").change(function () {
        document.getElementById("config").value = "custom";
    });

    $("#tolerance").on("input", function () {
        document.getElementById("config").value = "custom";
    });

    // Add from sidenav
    $("input[name='add'], button[name='add']").on('click', function (event) {
        event.preventDefault();
        var controller = $("#controller").val();
        var nice_name = $("#controller").val().replace($("#controller-search-directory").val(), "");
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

        if (config == "automatic") {
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
            beforeSend: addToResultsTable(config)
        }).done(data => addToResultsTable(data));
    }

    function getResultsTableRow(id) {
        let rows = $("#results-table tbody tr");
        for (let j = 0; j < rows.length; j++) {
            const experiment_id = rows[j].children[0].innerHTML;
            if (parseInt(experiment_id, 10) === id) {
                return rows[j];
            }
        }
    }

    function addToResultsTable(row_contents) {
        // This function is called both when
        // 1. a new experiment is started
        // 2. to populate the results table when results arrive from polling
        // 3. to populate the results table when the page is refreshed

        $("#results-table tr.special").hide();
        var table = document.getElementById("results-table").getElementsByTagName('tbody')[0];

        if (row_contents[4] == "Completed") {
            let experimentRow = getResultsTableRow(row_contents[0]);
            if (experimentRow) {
                for (let j = 4; j <= 7; j++) {
                    experimentRow.children[j].innerHTML = row_contents[j];
                }
                experimentRow.children[7].innerHTML = row_contents[7].milliSecondsToHHMMSS();
            } else {
                experimentRow = table.insertRow(-1);
                var firstCell = experimentRow.insertCell(-1);
                firstCell.outerHTML = "<th scope=\"row\">" + String(row_contents[0]) + "</th>";
                for (let j = 1; j <= 7; j++) {
                    const cell = experimentRow.insertCell(-1);
                    if (j == 1) {
                        cell.style = "display: none";
                    }
                    if (j <= 6) {
                        cell.innerHTML = row_contents[j];
                    }
                    if (j == 7) {
                        cell.innerHTML = row_contents[j].milliSecondsToHHMMSS();
                    }
                }
            }
            if (experimentRow.children.length < 9) {
                let lastCell = experimentRow.insertCell(-1);
                lastCell.innerHTML = '<i class="fa fa-eye text-primary"></i>';
                $(experimentRow.children[8]).find('i.fa-eye').on('click', (event) => {
                    $.post('/select', {runConfigIndex: row_contents[0]}, () => {
                        window.location.href = 'simulator'
                    });
                });
            }
        } else if (row_contents[4].startsWith("Error")) {
            let experimentRow = getResultsTableRow(row_contents[0]);
            if (experimentRow) {
                experimentRow.children[4].innerHTML = row_contents[4];
            } else {
                experimentRow = table.insertRow(-1);
                firstCell = experimentRow.insertCell(-1);
                firstCell.outerHTML = "<th scope=\"row\">" + String(row_contents[0]) + "</th>";
                for (let j = 1; j <= 7; j++) {
                    const cell = experimentRow.insertCell(-1);
                    if (j === 1) {
                        cell.style = "display: none";
                    }
                    if (j <= 3) {
                        cell.innerHTML = row_contents[j];
                    }
                    if (j === 4) {
                        cell.innerHTML = row_contents[j];
                    }
                }
            }
        } else { // This is the case where a new controller is added
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
            var row = table.insertRow(-1);
            var firstCell = row.insertCell(-1);
            firstCell.outerHTML = "<th scope=\"row\">" + String(row_contents[0]) + "</th>";
            for (let j = 1; j <= 7; j++) {
                const cell = row.insertCell(-1);
                if (j == 1) {
                    cell.style = "display: none";
                }
                if (j <= 3) {
                    cell.innerHTML = row_contents[j];
                }
                if (j == 4) {
                    cell.innerHTML = "Running...";
                }
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