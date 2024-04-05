// Stores default config in config.yml
var defConf;



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

function makeCheckbox(options, parent_div, default_options=[], custom=true, append_id=""){
    // custom checkboxes provided by bootstrap: prettier, blue, fade effect etc
    if (custom) {
        options.forEach((opt) => {
            var isChecked = (default_options.includes(opt)) ? 'checked' : '';
            var checkboxHtml = '<div class="custom-control custom-checkbox">' +
                                '<input type="checkbox" class="custom-control-input" name="' + opt + '" id="' + opt + append_id + '"' + isChecked + '>' +
                                '<label class="custom-control-label" for="' + opt + append_id + '">' + opt + '</label>' +
                              '</div>';
            parent_div.innerHTML += checkboxHtml;
          });
    } else {
        for (let option of options) {
            var checkbox = document.createElement('input');
            checkbox.classList.add('form-check-input');
            checkbox.type = 'checkbox';
            checkbox.name = option;
            checkbox.id = option;
            if(option in default_options){
                checkbox.checked = true;
            }

            var label = document.createElement('label');
            label.classList.add('form-check-label');
            label.htmlFor = option;
            label.innerHTML = option;

            var container = document.createElement('div');
            container.classList.add("form-check");
            container.appendChild(checkbox);
            container.appendChild(label);
            parent_div.appendChild(container);
        }
    }
}


// new GUI: we could move this to inspect.js
function loadPresets() {

    let xhr = new XMLHttpRequest();
    xhr.open('GET', '/yml', true);
    xhr.onload = function () {
        // Reads the config.yml file
        preset_json = JSON.parse(this.response);
        if (xhr.status >= 200 && xhr.status < 400) {

            fillYML(preset_json);

        } else {
            console.error("YML to get presets not working");
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

    // Stores default config in config.yml
    defConf = preset_json.presets.default;
    // Union of all configs present in config.yml
    let allConfig = {}
    for (let y in defConf) {
        allConfig[y] = [];
    }

    for (let x in preset_json.presets) {
        // loop over preset names
        for (let y in defConf) {
            // loop over properties
            if (y in preset_json.presets[x]) {
                // if that preset contains that property
                var valu = preset_json.presets[x][y];
                if (Array.isArray(valu)) {
                    for (let z in valu) {
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
    }

    // fill preset drop down
    let presets_in_use = ["deterministic", "axisonly-permissive", "logreg-permissive", "custom"]
    const app = document.getElementById('config');
    for (let x of presets_in_use) {
        const option = document.createElement('option');
        option.textContent = x;
        option.setAttribute('value', x);
        if (x === 'deterministic') {
            // set as default, advanced options are automatically selected accordingly
            option.setAttribute('selected', 'selected');
        }
        app.appendChild(option);
    }

    // fill determinize drop-down
    var det_dropdown = document.getElementById("determinize");
    for (let det of allConfig.determinize) {
        // don't add the "auto" option:
        if (det != "auto") {
            let opt = document.createElement('option');
            opt.textContent = det;
            opt.setAttribute('value', det);
            opt.setAttribute('id', det + "_edit");
            det_dropdown.appendChild(opt);
        }
    }
    // add safe-pruning and multilabelentropy as a determinizer:
    // TODO: does this make sense?
    let other_determinizers = ["safe-pruning", "multilabelentropy"];
    for (let det of other_determinizers) {
        let opt = document.createElement('option');
        opt.textContent = det;
        opt.setAttribute('value', det);
        opt.setAttribute('id', det + "_edit");
        det_dropdown.appendChild(opt);
    } 

    // make checkbox for numeric predicates
    var div_num_pred = document.getElementById("numeric-predicates");
    makeCheckbox(allConfig['numeric-predicates'], div_num_pred, [], true, "_edit");

    // make checkbox for categorical predicates
    var div_cat_pred = document.getElementById("categorical-predicates");
    makeCheckbox(allConfig['categorical-predicates'], div_cat_pred, [], true, "_edit");

    $("#config").trigger("change");

}

$(document).ready(function () {
    if (window.location.href.endsWith("simulator")) {
        // TODO T: maybe refactor this whole common.js bc this stuff is only for simulator page
        loadPresets();
        openNav();
        document.getElementById("navbar-hamburger").className += " is-active";
    }

    // Handles changing of form selections when different configs are changed
    $("#config").change(function () {
        let selected_preset = $(this).val();
        if (selected_preset == "custom") {
            if ($('#accordionButton').hasClass('collapsed')) {
                $('#accordionButton').click();
            }
        } else {
            for (let prop in defConf) {
                selected_preset = $(this).val();
                if (!(prop in preset_json.presets[selected_preset])) {
                    // if presets[selected_preset] has no entry for this property: use the default option for property
                    selected_preset = "default";                       
                }
                switch (prop) {
                    case "determinize":
                        if (preset_json.presets[selected_preset][prop] == "auto") {
                            if (preset_json.presets[selected_preset]["impurity"] != "multilabelentropy") {
                                console.error("'determinize: auto' can only be used in combination with 'impurity: multilabelentropy'.");
                            }
                            // new GUI uses displays multilabelentropy as a determinizer because it determinizes automatically
                            $("#" + prop).val("multilabelentropy");
                        } else {
                            $("#" + prop).val(preset_json.presets[selected_preset][prop]);
                        }
                        break;
                    case "tolerance":
                        $("tolerance").val(preset_json.presets[selected_preset][prop]);
                        break;
                    case "safe-pruning":
                        $('#safe-pruning').val(preset_json.presets[selected_preset][prop] + "");    // needs to be a String
                        break;
                    case "categorical-predicates":
                    case "numeric-predicates":
                        // numeric and categorical predicates are chosen with checkboxes bc can be more than one
                        $("#" + prop + " input[type='checkbox']").each(function() {
                            var checkboxId = $(this).attr("id");  
                            if (preset_json.presets[selected_preset][prop].includes(checkboxId.split("_edit")[0])) {
                                $(this).prop("checked", true);
                            } else {
                                $(this).prop("checked", false);
                            }
                        });
                }
            }
        }
        if ($("valuegrouping_edit").checked) {
            $('#tolerance-box').removeClass('disabled-row');
            $('#tolerance').removeClass('disabled-input');
        } else {
            $('#tolerance-box').addClass('disabled-row');
            $('#tolerance').addClass('disabled-input');
        }
    });

    // These functions handle changing the 'config' of form to custom whenever there's a change in finer controls
    $(".propList").change(function () {
        document.getElementById("config").value = "custom";
    });

    $("#tolerance").on("input", function () {
        document.getElementById("config").value = "custom";
    });

    // check if we need to show tolerance box now
    $("#categorical-predicates").on("change", "#valuegrouping_edit", function () {
        if ($(this).prop('checked')) {
            $('#tolerance-box').removeClass('disabled-row');
            $('#tolerance').removeClass('disabled-input');
        } else {
            $('#tolerance-box').addClass('disabled-row');
            $('#tolerance').addClass('disabled-input');
        }
    });

    $('button.hamburger').on('click', function () {
        if ($(this).hasClass("is-active")) {
            closeNav();
        } else {
            openNav();
        }

        $(this).toggleClass("is-active");
    });

    const accordionButton = $('#accordionButton');
    accordionButton.on('click', function () {
        const wasCollapsed = accordionButton.hasClass('collapsed');
        accordionButton.find('span').text(`${wasCollapsed ? 'Hide' : 'Show'} advanced options`);
        accordionButton.find('svg').css({'transform': 'rotate(' + (wasCollapsed ? 90 : 0) + 'deg)'});
    });
});