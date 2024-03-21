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
    let xhr = new XMLHttpRequest();
    xhr.open('GET', '/yml', true);
    xhr.onload = function () {
        // Reads the config.yml file
        preset_json = JSON.parse(this.response);
        if (xhr.status >= 200 && xhr.status < 400) {
            fillAdvancedOptionsModal(preset_json);

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

function makeCheckbox(options, parent_div, default_option=null){
    for (let option of options) {
        var checkbox = document.createElement('input');
        checkbox.classList.add('form-check-input');
        checkbox.type = 'checkbox';
        checkbox.name = option;
        checkbox.id = option;
        if(option == default_option){
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

function fillAdvancedOptionsModal(preset_json) {
    // fill the modal with all options available in config.yml

    defConf = (preset_json.presets.default);
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
    
    // fill determinize drop-down
    // TODO T: only show if not deterministic
    var det_dropdown = document.getElementById("option-determinize");
    console.log("det options: ", allConfig.determinize)
    for (let det of allConfig.determinize) {
        // don't add the "auto" option, use maxfreq as default:
        console.log("det: ", det)
        if (det != "auto") {
            let opt = document.createElement('option');
            opt.textContent = det;
            opt.setAttribute('value', det);
            opt.setAttribute('id', det);
            if (det == "maxfreq") {
                opt.setAttribute('selected', 'selected');
            }
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
        opt.setAttribute('id', det);
        det_dropdown.appendChild(opt);
    } 

    // make checkbox for numerical predicates
    var div_num_pred = document.getElementById("option-numeric-predicates");
    makeCheckbox(allConfig['numeric-predicates'], div_num_pred, "axisonly");

    // make checkbox for categorical predicates
    var div_cat_pred = document.getElementById("cat-pred-div");
    makeCheckbox(allConfig['categorical-predicates'], div_cat_pred, "multisplit");
    
    // add tolerance field
    var valuegrouping_checkbox = document.getElementById("valuegrouping");
    var div_tolerance = document.getElementById("cat-pred-col2");
    if (valuegrouping_checkbox) {
        // create input box
        var tolerance_textfield = document.createElement('input');
        tolerance_textfield.classList.add('form-control');
        tolerance_textfield.type = 'number';
        tolerance_textfield.value = '0.00001';
        tolerance_textfield.id = 'tolerance-field';
        tolerance_textfield.step = 'any';
        // create label
        var tolerance_label = document.createElement('label');
        tolerance_label.id = 'tolerance-label';
        tolerance_label.setAttribute('for', 'tolerance-field');
        tolerance_label.textContent = "Tolerance";
        // insert text field, then label
        div_tolerance.appendChild(tolerance_textfield);
        div_tolerance.insertBefore(tolerance_label, tolerance_textfield);
        if (! valuegrouping_checkbox.checked) {
            // only show if "valuegrouping" checked (by default not checked)
            $('#tolerance-field').css('visibility', 'hidden');
            $('#tolerance-label').css('visibility', 'hidden');
        // ^ use this instead of hide() / show() to set visibility property instead of display property
        }
    } else {
        console.error("No checkbox for valuegrouping was created, so cannot create tolerance field.")
    }
}

$(document).ready(function () {
    openNav();
    document.getElementById("navbar-hamburger").className += " is-active";
    loadPresets();

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