// Stores default config in config.yml
var defConf;

// Union of all configs present in config.yml
var allConfig = {};

// preset data json
var preset_json;

function popupModal(title, msg) {
    $("#messageModal h5.modal-title").text(title);
    $("#messageModal div.modal-body").text(msg);
    $("#messageModal").modal({"show": true});
}

function openNav() {
    // if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "310px";
    document.getElementById("main").style.paddingLeft = "310px";
}

/* Set the width of the side navigation to 0 and the left margin of the page content to 0 */
function closeNav() {
    // if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.paddingLeft = "0";
}

function loadPresets() {
    const app = document.getElementById('config');

    // All presets available for fallback
    const  fallback_app = document.getElementById("fallback");

    let xhr = new XMLHttpRequest();
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

            // Add algebraic/user-defined mode to preset
            const option2 = document.createElement('option');
            option2.textContent = "algebraic / user-defined";
            option2.setAttribute('value', "algebraic");
            app.appendChild(option2);

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

$(document).ready(function () {
    openNav();
    document.getElementById("navbar-hamburger").className += " is-active";
    loadPresets();

    // Handles changing of form selections when different configs are changed
    $("#config").change(function () {
        if ($(this).val() != "custom" && $(this).val() != "algebraic") {
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
        else if ($(this).val() == "custom") {
            // In case custom is selected
            $('#accordionButton').click();
        }
        else if ($(this).val() == "algebraic") {
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
});