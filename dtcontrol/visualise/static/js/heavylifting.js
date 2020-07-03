var totalSims;
var currentSim;
var x_current = [];
var x_bounds = [];
var u_current = [];
var lastPath = [];
var plpause;
var timeOfSlider = 50;
var numVars;
var numResults;
var chart = [];
var chartConfig = [];
var nextDisabled = false;
var isUser = false;

const simTableDiv = document.getElementById('tableHere');

const app = document.getElementById('config');
var defConf;
var allConfig = {};
const app1 = document.getElementById('controller');

function postload() {
    defConf = (data2.presets.default);
    var iter = 0;
    for (y in defConf) {
        allConfig[y] = [];
    }

    for (x in data2.presets) {
        //loop over preset names
        for (y in defConf) {
            //loop over properties
            if (y in data2.presets[x]) {
                //if that preset contains that property
                var valu = data2.presets[x][y];
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

    var myDiv0 = document.getElementById("numeric-predicates");
    for (var i = 0; i < allConfig['numeric-predicates'].length; i++) {
        var checkbox = document.createElement('input');
        checkbox.type = "checkbox";
        checkbox.name = 'numeric-predicates[]';
        checkbox.value = allConfig['numeric-predicates'][i];
        checkbox.id = allConfig['numeric-predicates'][i];
        var label = document.createElement('label');
        label.htmlFor = allConfig['numeric-predicates'][i];
        label.appendChild(document.createTextNode(allConfig['numeric-predicates'][i]));
        myDiv0.appendChild(checkbox);
        myDiv0.appendChild(label);
    }

    var myDiv1 = document.getElementById("categorical-predicates");
    for (var i = 0; i < allConfig['categorical-predicates'].length; i++) {
        var checkbox = document.createElement('input');
        checkbox.type = "checkbox";
        checkbox.name = 'categorical-predicates[]';
        checkbox.value = allConfig['categorical-predicates'][i];
        checkbox.id = allConfig['categorical-predicates'][i];
        var label = document.createElement('label');
        label.htmlFor = allConfig['categorical-predicates'][i];
        label.appendChild(document.createTextNode(allConfig['categorical-predicates'][i]));
        myDiv1.appendChild(checkbox);
        myDiv1.appendChild(label);
    }

    var det = document.getElementById("impurity");
    for (var i = 0; i < allConfig['impurity'].length; i++) {
        var opt = document.createElement('option');
        opt.textContent = allConfig['impurity'][i];
        opt.setAttribute('value', allConfig['impurity'][i]);
        opt.setAttribute('id', allConfig['impurity'][i]);
        det.appendChild(opt);
    }

    $("#config").trigger("change");

}

var xhr = new XMLHttpRequest();
xhr.open('GET', './yml', true);
xhr.onload = function() {
    data2 = JSON.parse(this.response);
    if (xhr.status >= 200 && xhr.status < 400) {
        for (x in data2.presets) {
            const option = document.createElement('option');
            option.textContent = x;
            option.setAttribute('value', x);
            app.appendChild(option);
        }
        const option = document.createElement('option');
        option.textContent = "custom";
        option.setAttribute('value', "custom");
        app.appendChild(option);
        postload();

    } else {
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

var modl = new XMLHttpRequest();
modl.open('GET', './examples', true);
modl.onload = function() {
    data1 = JSON.parse(this.response);
    for (var i = 0; i < data1.length; i++) {
        const option = document.createElement('option');
        option.textContent = data1[i];
        option.setAttribute('value', data1[i]);
        app1.appendChild(option);
    }
}
modl.setRequestHeader('cache-control', 'no-cache, must-revalidate, post-check=0, pre-check=0');
modl.setRequestHeader('cache-control', 'max-age=0');
modl.setRequestHeader('expires', '0');
modl.setRequestHeader('expires', 'Tue, 01 Jan 1980 1:00:00 GMT');
modl.setRequestHeader('pragma', 'no-cache');
modl.send();


var treeData = "",
    tree = "",
    diagonal = "",
    svg = "";

var i = 0,
    duration = 0,
    root;

var margin = { top: 20, right: 120, bottom: 20, left: 120 },
    width = 4560 - margin.right - margin.left,
    height = 1500 - margin.top - margin.bottom;



function myFunc() {
    // console.log("myFunc called");
    // ************** Generate the tree diagram	 *****************

    tree = d3.layout.tree()
        .size([height, width]);

    diagonal = d3.svg.diagonal()
        .projection(function(d) { return [d.y, d.x]; });

    svg = d3.select("#treeHere").append("svg")
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom)
        .attr("style", "overflow-x: auto; overflow-y: auto;")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    root = treeData[0];
    root.x0 = height / 2;
    root.y0 = 0;

    update(root);

    d3.select(self.frameElement).style("height", "500px");

}

// Toggle children on click.
function click(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
    } else {
        d.children = d._children;
        d._children = null;
    }
    update(d);
}

function update(source) {
    // Compute the new tree layout.
    var nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

    // Normalize for fixed-depth.
    nodes.forEach(function(d) { d.y = d.depth * 180; });

    // Update the nodes…
    var node = svg.selectAll("g.node")
        .data(nodes, function(d) { return d.id || (d.id = ++i); });

    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
        .on("click", click);

    nodeEnter.append("circle")
        .attr("r", 1e-6)
        .style("fill", function(d) { return d._children ? "lightsteelblue" : d.coleur; });

    nodeEnter.append("text")
        .attr("x", function(d) { return d.children || d._children ? -13 : 13; })
        .attr("dy", ".35em")
        .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
        .text(function(d) { return d.name; })
        .style("fill-opacity", 1e-6);

    // Transition nodes to their new position.
    var nodeUpdate = node.transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

    nodeUpdate.select("circle")
        .attr("r", 10)
        .style("fill", function(d) { return d._children ? "lightsteelblue" : d.coleur; });

    nodeUpdate.select("text")
        .style("fill-opacity", 1);

    // Transition exiting nodes to the parent's new position.
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
        .remove();

    nodeExit.select("circle")
        .attr("r", 1e-6);

    nodeExit.select("text")
        .style("fill-opacity", 1e-6);

    // Update the links…
    var link = svg.selectAll("path.link")
        .data(links, function(d) { return d.target.id; });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function(d) {
            var o = { x: source.x0, y: source.y0 };
            return diagonal({ source: o, target: o });
        });

    // Transition links to their new position.
    link.transition()
        .duration(duration)
        .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(duration)
        .attr("d", function(d) {
            var o = { x: source.x, y: source.y };
            return diagonal({ source: o, target: o });
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function(d) {
        d.x0 = d.x;
        d.y0 = d.y;
    });
}

var refreshTime = 10000;

function foldIt(od, nw) {
    if (!od.children || !nw.children)
        return;

    var len1 = od.children.length;
    var len2 = nw.children.length;
    var iter1 = 0;

    for (var it = 0; it < len2; it++) {
        if (iter1 == len1) {
            break;
        }
        if (od.children[iter1].name === nw.children[it].name) {
            if (od.children[iter1]._children) {
                //if some folded children
                nw.children[it]._children = nw.children[it].children;
                nw.children[it].children = null;
            } else {
                foldIt(od.children[iter1], nw.children[it]);
            }
            iter1++;
        }
    }
}

function colourPath(str) {
    root.coleur = "red";
    var dummy = root;
    for (var i = 0; i < str.length; i++) {
        if (dummy.children) {
            //hidden
            dummy.children[str[i]].coleur = "red";
            dummy = dummy.children[str[i]];
        } else {
            //visible
            dummy._children[str[i]].coleur = "red";
            dummy = dummy._children[str[i]];
        }
    }
    update(root);
}

function recolourPath() {
    root.coleur = "white";
    var dummy = root;
    for (var i = 0; i < lastPath[currentSim].length; i++) {
        if (dummy.children) {
            //hidden
            dummy.children[lastPath[currentSim][i]].coleur = "white";
            dummy = dummy.children[lastPath[currentSim][i]];
        } else {
            //visible
            dummy._children[lastPath[currentSim][i]].coleur = "white";
            dummy = dummy._children[lastPath[currentSim][i]];
        }
    }
    update(root);
}

function expandAll(nd) {
    if (nd == null) {
        expandAll(root);
        update(root);
        return;
    }
    if (!nd.children && !nd._children) {
        return;
    }
    if (!nd.children) {
        nd.children = nd._children;
        nd._children = null;

    }
    var len = nd.children.length;
    for (var it = 0; it < len; it++) {
        expandAll(nd.children[it]);
    }
    return;
}

function collapseAll(nd) {
    if (nd == null) {
        var len = root.children.length;
        for (var it = 0; it < len; it++) {
            collapseAll(root.children[it]);
        }
        update(root);
        return;
    }
    if (!nd.children && !nd._children) {
        return;
    }
    if (!nd._children) {
        nd._children = nd.children;
        nd.children = null;
    }
    var len = nd._children.length;
    for (var it = 0; it < len; it++) {
        collapseAll(nd._children[it]);
    }
    return;
}

function drawCanvas() {
    if ($('#controller').val() == "controller.scs") {
        var lineLength = 100;
        var canvas = document.getElementById("cartCanvas");
        var c = canvas.getContext("2d");

        c.clearRect(0, 0, 450, 250);

        c.fillStyle = "#000000";
        // to fill 450x250
        c.fillRect(150, 160, 150, 60);

        c.beginPath();
        c.moveTo(225, 160);
        c.lineWidth = 7;
        c.strokeStyle = "#802b00";
        var currentAngle = parseFloat(x_current[0][currentSim]);
        c.lineTo(225 + lineLength * Math.cos(currentAngle - (Math.PI / 2)), 160 - lineLength * Math.sin(currentAngle - (Math.PI / 2)));
        c.stroke();
    }


}

function checkBounds() {
    for (var i = 0; i < numVars; i++) {
        if (x_current[i][currentSim] < x_bounds[i][0] || x_current[i][currentSim] > x_bounds[i][1]) {
            return false;
        }
    }
    return true;
}

function renderChart(id, data, labels, ub, lb) {
    var chartIndex = parseInt(id);

    const canvas = document.getElementById('chartContainer' + chartIndex);
    var ctx = document.getElementById('chartContainer' + id).getContext('2d');
    chartConfig[chartIndex] = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                    label: 'Value of x' + chartIndex,
                    data: data,
                    borderColor: "#3e95cd",
                    fill: false
                },
                {
                    label: 'UB of x' + chartIndex,
                    data: ub,
                    backgroundColor: "rgb(75, 192, 255, 0.5)",
                    borderColor: "transparent",
                    pointRadius: 0,
                    fill: 0,
                    tension: 0
                },
                {
                    label: 'LB of x' + chartIndex,
                    data: lb,
                    backgroundColor: "rgb(75, 192, 255, 0.5)",
                    borderColor: "transparent",
                    pointRadius: 0,
                    fill: 0,
                    tension: 0
                },
                {
                    label: 'UBD of x' + chartIndex,
                    data: [ub[0] + 0.2 * (Math.abs(ub[0]))],
                    backgroundColor: "rgb(75, 192, 255, 0.5)",
                    borderColor: "transparent",
                    pointRadius: 0,
                    fill: false,
                    tension: 0
                },
                {
                    label: 'LBD of x' + chartIndex,
                    data: [lb[0] - 0.2 * (Math.abs(lb[0]))],
                    backgroundColor: "rgb(75, 192, 255, 0.5)",
                    borderColor: "transparent",
                    pointRadius: 0,
                    fill: false,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Values of x' + chartIndex
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true,
                animationDuration: 0
            },
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Simulation'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'x' + chartIndex
                    },
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            animation: {
                duration: 0, // general animation time
            },
            responsiveAnimationDuration: 0, // animation duration after a resize
        },
    };
    chart[chartIndex] = new Chart(ctx, chartConfig[chartIndex]);
}

async function oneStep() {
    recolourPath();

    if (currentSim == totalSims) {

        if (nextDisabled) {
            clearInterval(plpause);
            return;
        }

        var x_toPass = [];
        for (var i = 0; i < numVars; i++) {
            x_toPass.push(x_current[i][currentSim]);
        }
        var u_toPass = [];
        for (var i = 0; i < numResults; i++) {
            u_toPass.push(u_current[i][currentSim]);
        }

        $.ajax({
                data: JSON.stringify({
                    x_pass: x_toPass,
                    u_pass: u_toPass
                }),
                type: 'POST',
                contentType: "application/json; charset=utf-8",
                url: '/stepRoute'
            })
            .done(function(data) {

                const tab = document.getElementById('simTable');
                const dumrow = document.createElement('tr');

                const drc0 = document.createElement('td');
                const drc0_inp = document.createElement('input');

                drc0_inp.setAttribute('type', 'radio');
                drc0_inp.setAttribute('name', 'indexers');
                drc0_inp.setAttribute('id', totalSims + 1);
                drc0_inp.setAttribute('value', (totalSims + 1));
                drc0_inp.setAttribute('checked', 'checked');

                drc0.appendChild(drc0_inp);
                dumrow.appendChild(drc0);

                for (var i = 0; i < numVars; i++) {
                    const drc1 = document.createElement('td');
                    drc1.textContent = data.x_new[0][i];
                    dumrow.appendChild(drc1);
                }

                for (var i = 0; i < numResults; i++) {
                    const drc2 = document.createElement('td');
                    drc2.textContent = data.x_new[1][i];
                    dumrow.appendChild(drc2);
                }

                tab.appendChild(dumrow);
                colourPath(data.x_new[2]);

                for (var i = 0; i < numVars; i++) {
                    x_current[i].push(data.x_new[0][i]);
                }
                for (var i = 0; i < numResults; i++) {
                    u_current[i].push(data.x_new[1][i]);
                }

                lastPath.push(data.x_new[2]);
                totalSims++;
                currentSim = totalSims;
                console.log("update complete");

                for (var i = 0; i < numVars; i++) {
                    chart[i].data.labels.push(totalSims);
                    chart[i].data.datasets[1].data.push(x_bounds[i][1]);
                    chart[i].data.datasets[2].data.push(x_bounds[i][0]);
                    chart[i].update();
                }

                if (!checkBounds()) {
                    console.log("disabling now");
                    nextDisabled = true;
                    clearInterval(plpause);
                }

            });
    } else {
        currentSim++;
        $("input[name=indexers][value=" + currentSim + "]").trigger('click');

    }

    drawCanvas();

}

function clearCheckBoxes() {
    for (var i = 0; i < allConfig["numeric-predicates"].length; i++) {
        if ($('#' + allConfig["numeric-predicates"][i]).prop("checked")) {
            $('#' + allConfig["numeric-predicates"][i]).trigger('click');
        }
    }
    for (var i = 0; i < allConfig["categorical-predicates"].length; i++) {
        if ($('#' + allConfig["categorical-predicates"][i]).prop("checked")) {
            $('#' + allConfig["categorical-predicates"][i]).trigger('click');
        }
    }
}

$(document).ready(function() {

    var numChanges = 0;

    $('#formFirst').on('submit', function(event) {
        var num_preds_toPass = [];
        $('input[name="numeric-predicates[]"]:checked').each(function() {
            num_preds_toPass.push(this.value);
        });
        var cat_preds_toPass = [];
        $('input[name="categorical-predicates[]"]:checked').each(function() {
            cat_preds_toPass.push(this.value);
        });

        $.ajax({
                data: JSON.stringify({
                    controller: $('#controller').val(),
                    config: $('#config').val(),
                    determinize: $('#determinize').val(),
                    numeric_predicates: (num_preds_toPass),
                    categorical_predicates: (cat_preds_toPass),
                    impurity: $('#impurity').val(),
                    tolerance: $('#tolerance').val(),
                    safe_pruning: $('#safe-pruning').val()
                }),
                type: 'POST',
                contentType: "application/json; charset=utf-8",
                url: '/simRoute'
            })
            .done(function(data) {

                treeData = data.classi;
                numVars = data.numVars;
                numResults = data.numResults;

                for (var i = 0; i < numVars; i++) {
                    x_current.push([]);
                    chart.push([]);
                    chartConfig.push([]);
                }
                for (var i = 0; i < numResults; i++) {
                    u_current.push([]);
                }

                if (numChanges == 0)
                    myFunc();
                numChanges++;

                root = treeData[0];
                root.x0 = height / 2;
                root.y0 = 0;

                update(root);

                const tab = document.createElement('table');
                tab.setAttribute('id', "simTable");
                const dumrow = document.createElement('tr');
                const drc0 = document.createElement('th');
                drc0.textContent = "Index";
                dumrow.appendChild(drc0);

                const chartsDiv = document.getElementById('chartsHere');
                // var chartShare = (100/(numVars%3));
                var chartShare = 33;

                for (var i = 0; i < numVars; i++) {
                    const drc1 = document.createElement('th');
                    drc1.textContent = "x" + i;
                    dumrow.appendChild(drc1);

                    const someChartDiv = document.createElement('div');
                    someChartDiv.style.width = chartShare.toString() + "%";
                    someChartDiv.style.float = 'left';
                    someChartDiv.style.height = "80%";
                    const someChart = document.createElement('canvas');
                    someChart.setAttribute('id', 'chartContainer' + i.toString());
                    someChartDiv.appendChild(someChart);
                    chartsDiv.appendChild(someChartDiv);
                }

                if (numResults == 1) {
                    const drc2 = document.createElement('th');
                    drc2.textContent = "u";
                    dumrow.appendChild(drc2);
                } else {
                    for (var i = 0; i < numResults; i++) {
                        const drc2 = document.createElement('th');
                        drc2.textContent = "u" + i;
                        dumrow.appendChild(drc2);
                    }
                }

                tab.appendChild(dumrow);
                simTableDiv.appendChild(tab);

                const opt = document.getElementById("formSecond");
                for (var i = 0; i < numVars; i++) {
                    const dumDiv = document.createElement('div');

                    const dumLabel = document.createElement('label');
                    dumLabel.setAttribute('for', 'x' + i);
                    dumLabel.textContent = "Choose an x" + i + ":";

                    const dumInput = document.createElement('input');
                    dumInput.setAttribute('type', 'text');
                    dumInput.setAttribute('id', 'x' + i);
                    dumInput.setAttribute('name', 'x' + i);

                    dumDiv.appendChild(dumLabel);
                    dumDiv.appendChild(dumInput);

                    opt.appendChild(dumDiv);

                    x_bounds.push([data.bound[0][i], data.bound[1][i]]);
                }

                const dumSubmit = document.createElement('input');
                dumSubmit.setAttribute('type', 'submit');
                dumSubmit.setAttribute('value', 'Send');
                opt.appendChild(dumSubmit);

            });

        event.preventDefault();

    });

    $('#formSecond').on('submit', function(event) {
        var x_toPass = [];
        for (var i = 0; i < numVars; i++) {
            x_toPass.push(parseFloat($('#x' + i).val()));
        }
        $.ajax({
                data: JSON.stringify({ pass: x_toPass }),
                contentType: "application/json; charset=utf-8",
                type: 'POST',
                url: '/initRoute'
            })
            .done(function(data) {
                //data .decision changed to array
                const tab = document.getElementById('simTable');
                const dumrow = document.createElement('tr');

                const drc0 = document.createElement('td');
                const drc0_inp = document.createElement('input');

                drc0_inp.setAttribute('type', 'radio');
                drc0_inp.setAttribute('name', 'indexers');
                drc0_inp.setAttribute('id', '0');
                drc0_inp.setAttribute('value', '0');
                drc0_inp.setAttribute('checked', 'checked');

                drc0.appendChild(drc0_inp);
                dumrow.appendChild(drc0);

                for (var i = 0; i < numVars; i++) {
                    const drc1 = document.createElement('td');
                    drc1.textContent = $('#x' + i).val();
                    dumrow.appendChild(drc1)
                }
                for (var i = 0; i < numResults; i++) {
                    const drc2 = document.createElement('td');
                    drc2.textContent = data.decision[i];
                    dumrow.appendChild(drc2);
                }

                tab.appendChild(dumrow);
                colourPath(data.path);

                for (var i = 0; i < numVars; i++) {
                    x_current[i].push(parseFloat($('#x' + i).val()));
                }
                for (var i = 0; i < numResults; i++) {
                    u_current[i].push(data.decision[i]);
                }

                lastPath.push(data.path);
                totalSims = 0;
                currentSim = 0;

                if (!checkBounds()) {
                    console.log("disabling now");
                    nextDisabled = true;
                }

                for (var i = 0; i < numVars; i++) {
                    renderChart(i, x_current[i], [...Array(currentSim + 1).keys()], [x_bounds[i][1]], [x_bounds[i][0]]);
                }

                drawCanvas();

            });

        event.preventDefault();
    });

    $('#instep').on('submit', function(event) {

        if (!nextDisabled) {
            recolourPath();
            var x_toPass = [];
            for (var i = 0; i < numVars; i++) {
                x_toPass.push(x_current[i][currentSim]);
            }
            var u_toPass = [];
            for (var i = 0; i < numResults; i++) {
                u_toPass.push(u_current[i][currentSim]);
            }
            $.ajax({
                    data: JSON.stringify({
                        steps: $('#steps').val(),
                        x_pass: (x_toPass),
                        u_pass: (u_toPass)

                    }),
                    type: 'POST',
                    contentType: "application/json; charset=utf-8",
                    url: '/inStepRoute'
                })
                .done(function(data) {
                    const tab = document.getElementById('simTable');
                    var numSteps = parseInt($('#steps').val());

                    for (var i = 0; i < numSteps; i++) {
                        const dumrow = document.createElement('tr');
                        const drc0 = document.createElement('td');
                        const drc0_inp = document.createElement('input');
                        drc0_inp.setAttribute('type', 'radio');
                        drc0_inp.setAttribute('name', 'indexers');
                        drc0_inp.setAttribute('id', totalSims + 1);
                        drc0_inp.setAttribute('value', (totalSims + 1));
                        drc0_inp.setAttribute('checked', 'checked');
                        drc0.appendChild(drc0_inp);
                        dumrow.appendChild(drc0);

                        for (var j = 0; j < numVars; j++) {
                            const drc1 = document.createElement('td');
                            drc1.textContent = data.x_new[i][0][j];
                            dumrow.appendChild(drc1);
                        }
                        for (var j = 0; j < numResults; j++) {
                            const drc2 = document.createElement('td');
                            drc2.textContent = data.x_new[i][1][j];
                            dumrow.appendChild(drc2);
                        }

                        tab.appendChild(dumrow);

                        for (var j = 0; j < numVars; j++) {
                            x_current[j].push(data.x_new[i][0][j]);
                        }
                        for (var j = 0; j < numResults; j++) {
                            u_current[j].push(data.x_new[i][1][j]);
                        }

                        lastPath.push(data.x_new[i][2]);
                        totalSims++;
                        currentSim = totalSims;

                        for (var j = 0; j < numVars; j++) {
                            chart[j].data.labels.push(totalSims);
                            chart[j].data.datasets[1].data.push(x_bounds[j][1]);
                            chart[j].data.datasets[2].data.push(x_bounds[j][0]);
                        }

                        if (!checkBounds()) {
                            console.log("disabling now");
                            nextDisabled = true;
                            clearInterval(plpause);
                            break;
                        }
                    }

                    for (var i = 0; i < numVars; i++) {
                        chart[i].update();
                    }
                    colourPath(lastPath[totalSims]);

                    drawCanvas();

                });
        }
        event.preventDefault();
    });


    $(document).on("click", "input[name=player]", function() {
        var option = parseInt($("input[name=player]:checked").val());
        //play pause next back
        if (option == 0) {
            plpause = setInterval(oneStep, timeOfSlider);

        } else if (option == 1) {
            clearInterval(plpause);
        } else if (option == 2) {
            oneStep();
        } else if (option == 3) {
            if (currentSim > 0) {
                recolourPath();
                currentSim--;
                $("input[name=indexers][value=" + currentSim + "]").trigger('click');
            }
        }

        event.preventDefault();
    });

    $(document).on("change", "input[name=indexers]", function() {
        var ind = parseInt($("input[name='indexers']:checked").val());
        recolourPath();
        currentSim = ind;
        colourPath(lastPath[ind]);
        drawCanvas();

    });

    $("#config").change(function() {
        if ($(this).val() != "custom") {
            clearCheckBoxes();
            isUser = false;
            for (x in data2.presets) {
                //x is  preset names
                if ($(this).val() == x) {
                    //x is now selected preset
                    for (y in defConf) {
                        //y is  property names
                        if (y in data2.presets[x]) {
                            if (y == "tolerance") {
                                document.getElementById("tolerance").value = data2.presets[x][y];
                            } else if (y == "safe-pruning") {
                                if (data2.presets[x]["safe-pruning"]) {
                                    $('#safe-pruning').val("true");
                                } else {
                                    $('#safe-pruning').val("false");
                                }
                            } else if (y == "numeric-predicates") {
                                for (var z = 0; z < data2.presets[x][y].length; z++) {
                                    $("#" + data2.presets[x][y][z]).trigger('click');
                                }
                            } else if (y == "categorical-predicates") {
                                for (var z = 0; z < data2.presets[x][y].length; z++) {
                                    $("#" + data2.presets[x][y][z]).trigger('click');
                                }
                            } else {
                                $("#" + y).val(data2.presets[x][y]);
                            }
                        } else {
                            if (y == "tolerance") {
                                document.getElementById("tolerance").value = defConf[y];
                            } else if (y == "safe-pruning") {
                                if (data2.presets["default"]["safe-pruning"]) {
                                    $('#safe-pruning').val("true");
                                } else {
                                    $('#safe-pruning').val("false");
                                }
                            } else if (y == "numeric-predicates") {
                                for (var z = 0; z < data2.presets["default"][y].length; z++) {
                                    $("#" + data2.presets["default"][y][z]).trigger('click');
                                }
                            } else if (y == "categorical-predicates") {
                                for (var z = 0; z < data2.presets["default"][y].length; z++) {
                                    $("#" + data2.presets["default"][y][z]).trigger('click');
                                }
                            } else {
                                $("#" + y).val(data2.presets["default"][y]);
                            }
                        }
                    }

                    break;

                }
            }
            isUser = true;
        }


    });

    $(".propList").change(function() {
        console.log("change done by user");
        document.getElementById("config").value = "custom";
    });
    $("#tolerance").on("input", function() {
        console.log("change done by user to text");
        document.getElementById("config").value = "custom";
    });
    // Simple .change() does not work here because it is dynamically added
    $(document).on("click", 'input[name="numeric-predicates[]"]', function(e) {
        if (isUser) {
            console.log("change done by user to numpre");
            document.getElementById("config").value = "custom";
        }
    });
    $(document).on("click", 'input[name="categorical-predicates[]"]', function(e) {
        if (isUser) {
            console.log("change done by user to catpre");
            document.getElementById("config").value = "custom";
        }
    });


});


var slider = document.getElementById("timeRange");
slider.oninput = function() {
    timeOfSlider = this.value;
    clearInterval(plpause);
    plpause = setInterval(oneStep, timeOfSlider);
}