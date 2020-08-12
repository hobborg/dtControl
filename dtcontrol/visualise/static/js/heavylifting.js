// Total number of simulation till now
var totalSims;

// Current simulation index
var currentSim;

// List of all simulations
var x_current = [];

// List [lower_bound,upper_bound] elements for state varaibles
var x_bounds = [];

// List of all decisions
var u_current = [];

// Last path in tree for colouring (list of integers)
var lastPath = [];

// Stores interval as set by the time slider
var plpause;
var timeOfSlider = 50;

// Number of state varaibles and decision variables
var numVars;
var numResults;

// Stores all created chart variables
var chart = [];
var chartConfig = [];

// If readings go out of bounds this is toggled and all concerned buttons are disabled
var nextDisabled = false;

// Tree animation button toggles this variable
var treeAnimation = true;

// Tree eidt button toggles this varaible
var treeEdit = false;

// Used as addressing for selected node in tree edit button
var selectedNode = [];
var lastNode = null;

// Used for toggling custom construction behaviour
var customBuild = false;

const simTableDiv = document.getElementById('tableHere');

const app = document.getElementById('config');
const app_3 = document.getElementById('config_3');

var isSimulator;

// Stores default config in config.yml
var defConf;

// Union of all configs present in config.yml
var allConfig = {};

const app1 = document.getElementById('controller');

function fillYML() {
    // Uses DOM manipulation to populate required forms after reading config.yml

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

var xhr = new XMLHttpRequest();
xhr.open('GET', '/yml', true);
xhr.onload = function () {
    if (isSimulator) return;
    // Reads the config.yml file
    data2 = JSON.parse(this.response);
    if (xhr.status >= 200 && xhr.status < 400) {
        for (x in data2.presets) {
            const option = document.createElement('option');
            option.textContent = x;
            option.setAttribute('value', x);
            if (x === 'mlentropy') {
                option.setAttribute('selected', 'selected');
            }
            app.appendChild(option);
        }
        const option = document.createElement('option');
        option.textContent = "custom";
        option.setAttribute('value', "custom");
        app.appendChild(option);

        if (app_3) {
            for (x in data2.presets) {
                const option_3 = document.createElement('option');
                option_3.textContent = x;
                option_3.setAttribute('value', x);
                app_3.appendChild(option_3);
            }
            const option_3 = document.createElement('option');
            option_3.textContent = "custom";
            option_3.setAttribute('value', "custom");
            app_3.appendChild(option_3);
        }

        fillYML();

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

var modl = new XMLHttpRequest();
modl.open('GET', './examples', true);
modl.onload = function () {
    if (isSimulator) return;
    // Reades example folder and populates controller section in first form
    data1 = JSON.parse(this.response);
    for (var i = 0; i < data1.length; i++) {
        const option = document.createElement('option');
        option.textContent = data1[i];
        option.setAttribute('value', data1[i]);
        if (data1[i] === '10rooms.scs') {
            option.setAttribute('selected', 'selected');
        }
        app1.appendChild(option);
    }
}
modl.setRequestHeader('cache-control', 'no-cache, must-revalidate, post-check=0, pre-check=0');
modl.setRequestHeader('cache-control', 'max-age=0');
modl.setRequestHeader('expires', '0');
modl.setRequestHeader('expires', 'Tue, 01 Jan 1980 1:00:00 GMT');
modl.setRequestHeader('pragma', 'no-cache');
modl.send();

// GLobal variables that store tree data for rendering
var treeData = "",
    tree = "",
    diagonal = "",
    svg = "";

var i = 0,
    duration = 0,
    root;

var margin = {top: 20, right: 120, bottom: 20, left: 120},
    width = 1560 - margin.right - margin.left,
    height = 500 - margin.top - margin.bottom;
var width, height;

function constructTree() {
    // Generates the tree diagram

    tree = d3.layout.tree()
        .size([height, width]);

    diagonal = d3.svg.diagonal()
        .projection(function (d) {
            return [d.y, d.x];
        });   // Flip this to go horizontal layout

    var row_width = $("#treeHere").parent().width();
    var row_height = $("#treeHere").parent().height();
    svg = d3.select("#treeHere").append("svg")
        .attr("width", row_width)
        .attr("height", row_height)
        .attr("style", "overflow-x: auto; overflow-y: auto;")
        .call(d3.zoom().on("zoom", function () {
            svg.attr("transform", d3.event.transform)
        }))
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    root = treeData[0];
    root.x0 = height / 2;
    root.y0 = 0;

    update(root);

    d3.select(self.frameElement).style("height", "500px");

}

// Called by clicking a node when edit tree toggle is on
function openThirdForm(address) {
    $('#formThirdModal').modal('toggle');
    console.log(address);
    selectedNode = address;
}

// Toggle children on click.
function click(d) {
    if (customBuild) {
        if (lastNode != null)
            lastNode.coleur = "white";

        d.coleur = "red";
        update(root);

        selectedNode = d.address;
        lastNode = d;

        $.ajax({
            data: JSON.stringify({
                address: (d.address)
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/refreshImpurities'
        })
            .done(function (data) {
                // TODO see what all to refresh here
                $("#computedPredicatesTableFull > tbody").html("");
                for (var i = 0; i < data.computed_predicates.length; i++) {
                    const dumrow = document.createElement('tr');

                    const drc_inp = document.createElement('td');
                    const drc0_inp = document.createElement('input');

                    drc0_inp.setAttribute('type', 'radio');
                    drc0_inp.setAttribute('name', 'buildPredicate');

                    // Value set to index passed
                    drc0_inp.setAttribute('value', data.computed_predicates[i][0]);

                    drc_inp.appendChild(drc0_inp);
                    dumrow.appendChild(drc_inp);

                    for (var j = 0; j < data.computed_predicates[i].length; j++) {
                        const drc0 = document.createElement('td');
                        drc0.textContent = data.computed_predicates[i][j];
                        if (j == data.computed_predicates[i].length - 1) {
                            drc0.id = "expression" + data.computed_predicates[i][0];
                        }
                        dumrow.appendChild(drc0);
                    }

                    document.getElementById("computedPredicatesTable").appendChild(dumrow);
                }

                for (var i = 0; i < data.updated_impurities.length; i++) {
                    document.getElementById('domainImpurity' + i).textContent = data.updated_impurities[i];
                }

                document.getElementById("splitNodeButton").style.visibility = "visible";
            })
    } else if (treeEdit) {
        openThirdForm(d.address);
    } else {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        update(d);
        update(root);
    }
}

// Updates the svg generated according to changes in tree data
function update(source) {
    // Compute the new tree layout.
    var nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

    // Normalize for fixed-depth.
    // Horizontal layout: drop d.x = d.x * 12
    nodes.forEach(function (d) {
        d.y = d.depth * 180; /* d.x = d.x * 12; */
    });

    // Update the nodes…
    var node = svg.selectAll("g.node")
        .data(nodes, function (d) {
            return d.id || (d.id = ++i);
        });

    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function (d) {
            return "translate(" + source.y0 + "," + source.x0 + ")";
        })  // Horizontal layout: flip x, y
        .on("click", click);

    nodeEnter.append("circle")
        .attr("r", 1e-6)
        .style("fill", function (d) {
            return d._children ? "lightsteelblue" : d.coleur;
        });

    nodeEnter.append("text")
        .attr("x", function (d) {
            return d.children || d._children ? -13 : 13;
        })
        .attr("dy", ".35em")
        .attr("text-anchor", function (d) {
            return d.children || d._children ? "end" : "start";
        })
        .attr("id", function (d) {
            return "addr" + d.address.toString();
        })
        .text(function (d) {
            return d.name;
        })
        .style("fill-opacity", 1e-6);

    // Transition nodes to their new position.
    var nodeUpdate = node.transition()
        .duration(duration)
        .attr("transform", function (d) {
            return "translate(" + d.y + "," + d.x + ")";
        });  // Horizontal layout: flip x, y

    nodeUpdate.select("circle")
        .attr("r", 10)
        .style("fill", function (d) {
            return d._children ? "lightsteelblue" : d.coleur;
        });

    nodeUpdate.select("text")
        .style("fill-opacity", 1);

    // Transition exiting nodes to the parent's new position.
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function (d) {
            return "translate(" + source.y + "," + source.x + ")";
        })  // Horizontal layout: flip x, y
        .remove();

    nodeExit.select("circle")
        .attr("r", 1e-6);

    nodeExit.select("text")
        .style("fill-opacity", 1e-6);

    // Update the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) {
            return d.target.id;
        });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function (d) {
            var o = {x: source.x0, y: source.y0};
            return diagonal({source: o, target: o});
        });

    // Transition links to their new position.
    link.transition()
        .duration(duration)
        .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(duration)
        .attr("d", function (d) {
            var o = {x: source.x, y: source.y};
            return diagonal({source: o, target: o});
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function (d) {
        d.x0 = d.x;
        d.y0 = d.y;
    });
}

// Not used anymore, useful when trying to preserve toggled state of nodes when refreshing the tree (might be useful in tree edit later)
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

// Makes nodes red along the path given as 'str'
function colourPath(str) {
    if (treeAnimation) {
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
}

// Returns all nodes in tree to white colour
function recolourPath() {
    if (treeAnimation) {
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
}

// Returns height of tree
function getDepth(depthNode) {
    if (depthNode.children) {
        var ans = 0;
        for (var i = 0; i < depthNode.children.length; i++) {
            ans = Math.max(ans, getDepth(depthNode.children[i]));
        }
        return ans + 1;
    } else {
        return 0;
    }

}

// Returns number of tree leaves
function getLeaves(depthNode) {
    if (depthNode.children) {
        if (depthNode.children.length == 0) {
            return 1;
        }
        var ans = 0;
        for (var i = 0; i < depthNode.children.length; i++) {
            ans += getLeaves(depthNode.children[i]);
        }
        return ans;
    } else {
        return 1;
    }
}

// Expands all tree nodes
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

}

// Collapses all tree nodes
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

}

// If cartpole model used, draws it
function drawCanvas() {
    if ($('#controller').val() == "cartpole.scs") {
        var lineLength = 100;
        var canvas = document.getElementById("cartCanvas");
        var c = canvas.getContext("2d");

        c.clearRect(0, 0, 450, 250);

        c.fillStyle = "#000000";
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

// Checks if state variables go out of bounds at any point
function checkBounds() {
    for (var i = 0; i < numVars; i++) {
        if (x_current[i][currentSim] < x_bounds[i][0] || x_current[i][currentSim] > x_bounds[i][1]) {
            return false;
        }
    }
    return true;
}

// Renders all the charts using Chart.js
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

// Called every time when 'Next' or 'Play' button is used
async function oneStep() {
    console.log('oneStep is called');
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
            .done(function (data) {

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
                tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                scrollToEndOfTable();


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

function openNav() {
    if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "310px";
    document.getElementById("main").style.paddingLeft = "310px";
}

/* Set the width of the side navigation to 0 and the left margin of the page content to 0 */
function closeNav() {
    if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.paddingLeft = "0";
}

function scrollToEndOfTable() {
    var elem = document.querySelector("#simTable");
    elem.scrollTop = elem.scrollHeight;
}

$(document).ready(function () {
    isSimulator = $('.simulator').length > 0;
    var numChanges = 0;

    if (!isSimulator) {
        openNav();
        document.getElementById("navbar-hamburger").className += " is-active";
    }

    $('button.hamburger').on('click', function (event) {
        if ($(this).hasClass("is-active")) {
            closeNav();
        } else {
            openNav();
        }

        $(this).toggleClass("is-active");
    });

    const accordionButton = $('#accordionButton');
    accordionButton.on('click', event => {
        const wasCollapsed = accordionButton.hasClass('collapsed');
        accordionButton.find('span').text(`${wasCollapsed ? 'Hide' : 'Show'} advanced options`);
        accordionButton.find('svg').css({'transform': 'rotate(' + (wasCollapsed ? 90 : 0) + 'deg)'});
    });

    $("#openSecondFormButton").on("click", function (event) {
        if ($(this).hasClass("btn-primary")) {
            $(this).removeClass("btn-primary");
            $(this).addClass("btn-secondary");
            triggerDynamicsInput();
            $(this).html("Simulate off");
        } else {
            $(this).removeClass("btn-secondary");
            $(this).addClass("btn-primary");
            document.getElementById("mainRow2").style.visibility = "hidden";
            document.getElementById("mainRow3").style.visibility = "hidden";
            //document.getElementById("expandThisDiv").style.height = "450px";
            document.getElementById("playerDiv").style.visibility = "hidden";
            document.getElementById("timeRange").style.visibility = "hidden";
            document.getElementById("instep").style.visibility = "hidden";
            document.getElementById("animationDiv").style.visibility = "hidden";

            $("#dynamics-body").show();
            $("#initial-values").hide();
            $("#formSecond-next-button").show();
            $("#formSecond-randomize-button").hide();
            $("#formSecond-submit-button").hide();
            $("#exampleModalLongTitle").html("Enter system dynamics");

            //document.getElementById("hideThisDiv").style.display = "block";
            // TODO: Reset tree colors
            $(this).html("Simulate");
        }

    });

    if (isSimulator) {
        $.get('/computed', (data) => {
            document.getElementById("openSecondFormButton").style.visibility = "visible";
            document.getElementById("mainRow1").style.visibility = "visible";
            // document.getElementById("editTreeDiv").style.visibility = "visible";

            treeData = data.classi;
            numVars = data.numVars;
            numResults = data.numResults;

            console.log(treeData);

            // height = 50 * getLeaves(treeData[0]);
            height = 25 * getLeaves(treeData[0]);
            // height = 650;
            width = 200 * getDepth(treeData[0]);

            for (var i = 0; i < numVars; i++) {
                x_current.push([]);
                chart.push([]);
                chartConfig.push([]);
            }
            for (var i = 0; i < numResults; i++) {
                u_current.push([]);
            }

            if (numChanges == 0)
                constructTree();
            numChanges++;

            root = treeData[0];
            root.x0 = height / 2;
            root.y0 = 0;

            update(root);

            const tab = document.getElementById('simTable');

            // Header row
            const dumrow = document.createElement('tr');
            const drc0 = document.createElement('th');
            drc0.setAttribute("scope", "col");
            drc0.textContent = "Index";
            dumrow.appendChild(drc0);

            const chartsDiv0 = document.getElementById('chartsHere0');
            const chartsDiv1 = document.getElementById('chartsHere1');

            for (var i = 0; i < numVars; i++) {
                const drc1 = document.createElement('th');
                drc1.setAttribute("scope", "col");
                drc1.textContent = "x" + i;
                dumrow.appendChild(drc1);

                const someChartDiv = document.createElement('div');
                someChartDiv.style.width = "100%";
                someChartDiv.style.float = 'left';
                someChartDiv.style.height = someChartDiv.style.width;
                const someChart = document.createElement('canvas');
                someChart.setAttribute('id', 'chartContainer' + i.toString());
                someChartDiv.appendChild(someChart);

                const heir0 = document.createElement('div');
                heir0.setAttribute('class', "card shadow mb-4");

                const heir1 = document.createElement('div');
                heir1.setAttribute('class', "card-body");

                const heir2 = document.createElement('div');
                heir2.setAttribute('style', "text-align:center;");

                heir2.appendChild(someChartDiv);
                heir1.appendChild(heir2);
                heir0.appendChild(heir1);
                if (i % 2 == 0) {
                    chartsDiv0.appendChild(heir0);
                } else {
                    chartsDiv1.appendChild(heir0);
                }

            }

            if (numResults == 1) {
                const drc2 = document.createElement('th');
                drc2.setAttribute("scope", "col");
                drc2.textContent = "u";
                dumrow.appendChild(drc2);
            } else {
                for (var i = 0; i < numResults; i++) {
                    const drc2 = document.createElement('th');
                    drc2.setAttribute("scope", "col");
                    drc2.textContent = "u" + i;
                    dumrow.appendChild(drc2);
                }
            }
            tab.deleteRow(-1);
            tab.tHead.appendChild(dumrow);
            simTableDiv.appendChild(tab);

            const opt = document.getElementById("formSecondBody");
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
        });
    }

    // Add from sidenav
    $("input[name='add'], button[name='add']").on('click', function (event) {
        event.preventDefault();
        var controller = $('#controller').val();
        var config = $('#config').val();
        var determinize = $('#determinize').val();
        var numeric_predicates = $('#numeric-predicates').val();
        var categorical_predicates = $('#categorical-predicates').val();
        var impurity = $('#impurity').val();
        var tolerance = $('#tolerance').val();
        var safe_pruning = $('#safe-pruning').val();
        var row_contents = [controller, config, determinize, numeric_predicates, categorical_predicates, impurity, tolerance, safe_pruning];

        $("#experiments-table tr.special").hide();

        var table = document.getElementById("experiments-table").getElementsByTagName('tbody')[0];

        // Create an empty <tr> element and add it to the 1st position of the table:
        var row = table.insertRow(-1);
        var fisrtCell = row.insertCell(-1);
        fisrtCell.outerHTML = "<th scope=\"row\">" + String(table.rows.length - 1) + "</th>";

        // Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
        for (let j = 0; j < 8; j++) {
            var c = row.insertCell(-1);
            c.innerHTML = row_contents[j];
        }

        var icon = row.insertCell(-1);
        icon.innerHTML = "<i class=\"fa fa-trash text-danger\"></i>&nbsp;&nbsp;<i class=\"fa fa-play text-success\" aria-hidden=\"true\"></i>";
    });

    $("table").on("click", "i.fa-trash", function () {
        $(this).parent().parent().remove();
        if (document.getElementById("experiments-table").getElementsByTagName('tbody')[0].children.length == 1) {
            $("#experiments-table tr.special").show();
        }
    });

    var constructionTimes = {};
    Number.prototype.milliSecondsToHHMMSS = function () {
        var sec_num = this / 1000;
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
        constructionTimes[config[0]] = new Date().getTime();
        $.ajax({
            data: JSON.stringify({
                controller: config[1],
                config: config[2],
                determinize: config[3],
                numeric_predicates: config[4],
                categorical_predicates: config[5],
                impurity: config[6],
                tolerance: config[7],
                safe_pruning: config[8]
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/simRoute',
            beforeSend: function (jqXHR) {
                $("#results-table tr.special").hide();
                var table = document.getElementById("results-table").getElementsByTagName('tbody')[0];

                // Create an empty <tr> element and add it to the 1st position of the table:
                var row = table.insertRow(-1);
                var firstCell = row.insertCell(-1);
                firstCell.outerHTML = "<th scope=\"row\">" + String(config[0]) + "</th>";

                // Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
                // Set controller
                var c = row.insertCell(-1);
                c.innerHTML = config[1];

                // Set preset
                c = row.insertCell(-1);
                c.innerHTML = config[2];

                // Set status
                c = row.insertCell(-1);
                c.innerHTML = "Running...";

                for (let j = 0; j < 4; j++) {
                    row.insertCell(-1);
                }
            }
        }).done(function (data) {
            let experimentRow;
            let rows = $("#results-table tbody tr");
            for (let j = 0; j < rows.length; j++) {
                experiment_id = rows[j].children[0].innerHTML;
                if (experiment_id === config[0]) {
                    experimentRow = rows[j];
                }
            }
            console.assert(experimentRow);
            experimentRow.children[3].innerHTML = "Completed";
            experimentRow.children[4].innerHTML = data['inner nodes'];
            experimentRow.children[5].innerHTML = data['nodes'] - data['inner nodes'];
            const elapsedTime = new Date().getTime() - constructionTimes[config[0]];
            experimentRow.children[6].innerHTML = elapsedTime.milliSecondsToHHMMSS();
            experimentRow.children[7].innerHTML = '<i class="fa fa-eye text-primary"></i>';

            $(experimentRow.children[7]).find('i.fa-eye').on('click', (event) => {
                $.post('/select', {runConfigIndex: config[0]}, () => {
                    window.location.href = 'simulator'
                });
            });
        });
    }

    $("table").on("click", "i.fa-play", function (event) {
        // Write code to call simRoute
        var row_items = $(this).parent().parent().find('th,td');
        row_content = []
        row_items.each(function (k, v) {
            row_content.push(v.innerHTML);
        });
        run_single_benchmark(row_content);
    });

    // Submits popup modal form (for passing initial values of state variables)
    $('#formSecond').on('submit', function (event) {
        console.log('form is submitted');
        var x_toPass = [];
        for (var i = 0; i < numVars; i++) {
            x_toPass.push(parseFloat($('#x' + i).val())); // TODO generalize this - x all the time might not work
        }
        $.ajax({
            data: JSON.stringify({pass: x_toPass, dynamics: $("#dynamics-input").val()}),
            contentType: "application/json; charset=utf-8",
            type: 'POST',
            url: '/initRoute'
        })
            .done(function (data) {
                document.getElementById("mainRow2").style.visibility = "visible";
                document.getElementById("mainRow3").style.visibility = "visible";
                document.getElementById("expandThisDiv").style.height = "450px";
                document.getElementById("playerDiv").style.visibility = "visible";
                document.getElementById("timeRange").style.visibility = "visible";
                document.getElementById("instep").style.visibility = "visible";
                document.getElementById("animationDiv").style.visibility = "visible";

                var mini = document.getElementsByClassName("card-body");
                for (var i = 0; i < mini.length; i++) {
                    mini[i].style.height = "425px";
                }

                // resizing to get largest space for tree
                if ($('#controller').val() == "cartpole.scs") {
                    document.getElementById("expandThisDiv").className = "col-lg-6";
                    document.getElementById("hideThisDiv").style.display = "block";
                } else {
                    document.getElementById("hideThisDiv").remove();
                }

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
                tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                scrollToEndOfTable();
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
                $('#formSecondModal').modal('hide');

                // Alert when dynamics.txt file not present
                if (!data.dynamics) {
                    alert('The dynamics.txt file seems to be in an incorrect format or is missing from the examples folder. Please try again with a valid dynamics file');
                    nextDisabled = true;
                }

            });

        event.preventDefault();
    });

    $("#formSecond-next-button").on("click", function (event) {
        $("#dynamics-body").hide();
        $("#initial-values").show();
        $("#formSecond-next-button").hide();
        $("#formSecond-randomize-button").show();
        $("#formSecond-submit-button").show();
        $("#exampleModalLongTitle").html("Enter initial values");
    });

    // Form that collects edit tree data
    $('#formThird').on('submit', function (event) {
        $.ajax({
            data: JSON.stringify({
                controller: $('#controller_3').val(),
                config: $('#config_3').val(),
                determinize: $('#determinize_3').val(),
                numeric_predicates: $('#numeric-predicates_3').val(),
                categorical_predicates: $('#categorical-predicates_3').val(),
                impurity: $('#impurity_3').val(),
                tolerance: $('#tolerance_3').val(),
                safe_pruning: $('#safe-pruning_3').val()
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/reconstructRoute1'
        })
            .done(function (data) {
                // Add tree appending functions here
                // Consult formFirst submit function
                // ########################################################### Edit here ###########################################################
            })
        event.preventDefault();
    })

    // Form that collects edit tree data (User text predicates)
    $('#formFourth').on('submit', function (event) {
        $.ajax({
            data: JSON.stringify({
                predicate: $('#user_pred').val()
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/reconstructRoute2'
        })
            .done(function (data) {
                // Add tree appending functions here
                // ########################################################### Edit here ###########################################################
            })
        event.preventDefault();
    })

    $('#evaluatePredicateImpurityForm').on('submit', function (event) {
        $.ajax({
            data: JSON.stringify({
                predicate: $('#init_domain_knowledge').val()
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/evaluatePredicateImpurity'
        })
            .done(function (data) {
                document.getElementById("computedImpurity").textContent = data.impurity;
                document.getElementById('addToDomainKnowledgeTableButton').style.visibility = 'visible';
            })
        event.preventDefault();
    })

    // Handles the instep function
    $('#instep button').on('click', function (event) {

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
            var steps = $('#steps').val();
            if (steps === "") {
                $('#steps').val("1");
                steps = 1;
            }
            $.ajax({
                data: JSON.stringify({
                    steps: steps,
                    x_pass: (x_toPass),
                    u_pass: (u_toPass)

                }),
                type: 'POST',
                contentType: "application/json; charset=utf-8",
                url: '/inStepRoute'
            })
                .done(function (data) {
                    const tab = document.getElementById('simTable');

                    for (var i = 0; i < steps; i++) {
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
                        tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                        $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                        scrollToEndOfTable();

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


    // Handles the player inputs
    $(document).on("click", "input[name=player]", function (event) {
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

    // Handles selection of different rows in simulation table
    $(document).on("change", "input[name=indexers]", function () {
        var ind = parseInt($("input[name='indexers']:checked").val());
        recolourPath();
        currentSim = ind;
        colourPath(lastPath[ind]);
        drawCanvas();

    });

    // Handles changing of form selections when different configs are changed
    $("#config").change(function () {
        if ($(this).val() != "custom") {
            // clearCheckBoxes();
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
                            } else {
                                $("#" + y).val(data2.presets["default"][y]);
                            }
                        }
                    }

                    break;

                }
            }
        }


    });

    // Handles changing of form selections when different configs are changed (For edit tree popup)
    $("#config_3").change(function () {
        if ($(this).val() != "custom") {
            // clearCheckBoxes();
            for (x in data2.presets) {
                //x is  preset names
                if ($(this).val() == x) {
                    //x is now selected preset
                    for (y in defConf) {
                        //y is  property names
                        if (y in data2.presets[x]) {
                            if (y == "tolerance") {
                                document.getElementById("tolerance_3").value = data2.presets[x][y];
                            } else if (y == "safe-pruning") {
                                if (data2.presets[x]["safe-pruning"]) {
                                    $('#safe-pruning_3').val("true");
                                } else {
                                    $('#safe-pruning_3').val("false");
                                }
                            } else {
                                $("#" + y + "_3").val(data2.presets[x][y]);
                            }
                        } else {
                            if (y == "tolerance") {
                                document.getElementById("tolerance_3").value = defConf[y];
                            } else if (y == "safe-pruning") {
                                if (data2.presets["default"]["safe-pruning"]) {
                                    $('#safe-pruning_3').val("true");
                                } else {
                                    $('#safe-pruning_3').val("false");
                                }
                            } else {
                                $("#" + y + "_3").val(data2.presets["default"][y]);
                            }
                        }
                    }

                    break;

                }
            }
        }


    });

    // The 4 functions handle changing the 'config' of form to custom whenever there's a change in finer controls
    $(".propList").change(function () {
        document.getElementById("config").value = "custom";
    });
    $(".propList_3").change(function () {
        document.getElementById("config_3").value = "custom";
    });
    $("#tolerance").on("input", function () {
        document.getElementById("config").value = "custom";
    });
    $("#tolerance_3").on("input", function () {
        document.getElementById("config_3").value = "custom";
    });
    // Simple .change() does not work here because it is dynamically added
});

// Handles play speed slider
var slider = document.getElementById("timeRange");
if (slider) {
    slider.oninput = function () {
        if (parseInt($("input[name=player]:checked").val()) == 0) {
            timeOfSlider = this.value;
            clearInterval(plpause);
            plpause = setInterval(oneStep, timeOfSlider);
        } else {
            timeOfSlider = this.value;
        }
    }
}


// Christoph's additional functionality
function customTree() {
    closeNav();
    document.getElementById("sideNavOpener").disabled = true;
    document.getElementById("mainRow1").style.visibility = "visible";
    document.getElementById("mainRow1.1").style.display = "flex";
    document.getElementById("mainRow1.2").style.display = "flex";
    $('#initialCustomTreeModal').modal('toggle');
}

var numDomainKnowledge = 0;

// Contains [impurity,predicate] type objects
var finalDomainKnowledge = [];


function addToDomainKnowledgeTable() {
    const dumrow = document.createElement('tr');
    const drc0 = document.createElement('td');
    const drc0_inp = document.createElement('input');

    drc0_inp.setAttribute('type', 'radio');
    drc0_inp.setAttribute('name', 'buildPredicate');
    drc0_inp.setAttribute('value', numDomainKnowledge);

    drc0.appendChild(drc0_inp);
    dumrow.appendChild(drc0);

    const drc1 = document.createElement('td');
    drc1.textContent = numDomainKnowledge;
    dumrow.appendChild(drc1);

    const drc2 = document.createElement('td');
    drc2.textContent = document.getElementById('computedImpurity').textContent;
    drc2.id = "domainImpurity" + numDomainKnowledge;
    dumrow.appendChild(drc2);

    const drc3 = document.createElement('td');
    drc3.textContent = $('#init_domain_knowledge').val();
    drc3.id = "expression" + numDomainKnowledge;
    dumrow.appendChild(drc3);

    numDomainKnowledge++;

    document.getElementById("domainKnowledgeTable").appendChild(dumrow);
    finalDomainKnowledge.push([drc2.textContent, drc3.textContent]);

    document.getElementById('computedImpurity').textContent = "";
    document.getElementById('init_domain_knowledge').value = "";
    document.getElementById('addToDomainKnowledgeTableButton').style.visibility = 'hidden';
}

function closeInitialCustomTreeModal() {
    $.ajax({
        data: JSON.stringify({
            domainKnowledge: (finalDomainKnowledge)
        }),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/featureLabelSpecifications'
    })
        .done(function (data) {
            for (var i = 0; i < data.feature_specifications.length; i++) {
                const dumrow = document.createElement('tr');

                for (var j = 0; j < data.feature_specifications[i].length; j++) {
                    const drc0 = document.createElement('td');
                    drc0.textContent = data.feature_specifications[i][j];
                    dumrow.appendChild(drc0);
                }

                document.getElementById("featureSpecificationTable").appendChild(dumrow);
            }
            for (var i = 0; i < data.label_specifications.length; i++) {
                const dumrow = document.createElement('tr');

                for (var j = 0; j < data.label_specifications[i].length; j++) {
                    const drc0 = document.createElement('td');
                    drc0.textContent = data.label_specifications[i][j];
                    dumrow.appendChild(drc0);
                }

                document.getElementById("labelSpecificationTable").appendChild(dumrow);
            }
            $('#initialCustomTreeModal').modal('hide');

            // Drawing out initial tree now
            treeData = [{"name": "Build", "parent": null, "coleur": "white", "children": [], "address": []}]
            height = 400;
            width = 1000;

            constructTree();

            root = treeData[0];
            root.x0 = height / 2;
            root.y0 = 0;
            update(root);
            customBuild = true;
        })
}

function splitNode() {
    var toSendPredicate = $('input[name="buildPredicate"]:checked').val();
    console.log(toSendPredicate);
    $.ajax({
        data: JSON.stringify({
            address: (selectedNode),
            predicate: toSendPredicate
        }),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/splitNode'
    })
        .done(function (data) {
            // returns number of splits only
            var numSplits = data.number_splits;
            lastNode.children = [];
            for (var i = 0; i < numSplits; i++) {
                lastNode.children.push({
                    "name": "Build",
                    "parent": lastNode.name,
                    "coleur": "white",
                    "children": [],
                    "address": lastNode.address.concat([i])
                });
            }
            lastNode.coleur = "white";
            lastNode.name = document.getElementById('expression' + toSendPredicate).textContent;
            document.getElementById('addr' + lastNode.address).textContent = lastNode.name;
            update(lastNode);
            update(root);
            document.getElementById("splitNodeButton").style.visibility = "hidden";
        })
}

// Randomize button in Modal for selecting inital values of state variables
function randomizeInputs() {
    for (var i = 0; i < numVars; i++) {
        var range = x_bounds[i][1] - x_bounds[i][0];
        document.getElementById('x' + i).value = x_bounds[i][0] + (Math.random() * range);
    }
}

// Opens second form (for initial state variable selection)
function triggerDynamicsInput() {
    $('#formSecondModal').modal('show');
}

// Have to select dynamically created elements like this
// Handles colouring of table rows when clicked
$(document).on("click", "#simTable tbody tr", function () {
    $(this).addClass('selected').siblings().removeClass('selected');
    var value = $(this).find('td:first').children()[0].getAttribute("value")
    console.log(value);
    $(this).find('td input[type=radio]').prop('checked', true);
    // var ind = parseInt($("input[name='indexers']:checked").val());
    var ind = parseInt(value);
    recolourPath();
    currentSim = ind;
    colourPath(lastPath[ind]);
    drawCanvas();
});

document.getElementById("simTable").addEventListener("scroll", function(){
   var translate = "translate(0,"+this.scrollTop+"px)";
   this.querySelector("thead").style.transform = translate;
});

// 'Animate tree' button and 'Edit tree' button

$(document).on("change", "#animateTree", function () {
    treeAnimation = !treeAnimation;
    console.log(treeAnimation);
});
$(document).on("change", "#editTree", function () {
    treeEdit = !treeEdit;
    console.log(treeEdit);
});