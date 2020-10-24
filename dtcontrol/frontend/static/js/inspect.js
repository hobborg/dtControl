// Total number of simulation till now
var totalSims;

// Current simulation index
var currentSim;

// List of all simulations
var xCurrent = [];

// List [lower_bound,upper_bound] elements for state variables
var xBoundsOuter = [];
var xBoundsInner = [];

// List of all decisions
var uCurrent = [];

// Last path in tree for colouring (list of integers)
var lastPath = [];

// Stores interval as set by the time slider
var plpause;
var timeOfSlider = 500;

// Number of state variables and decision variables
var stateDimension;
var actionDimension;

// Stores all created chart variables
var chart = [];
var chartConfig = [];

// If readings go out of bounds this is toggled and all concerned buttons are disabled
var nextDisabled = false;

// Tree animation button toggles this variable
var treeAnimation = true;

var nodeSelect = false;

// Used as addressing for selected node in tree edit button
var selectedNode = null;
var lastNode = null;

// Used for toggling custom construction behaviour
var customBuild = false;

const simTableDiv = document.getElementById('tableHere');

var isSimulator;

var idUnderInspection;

// Edit Mode activated?
var editMode = false;

// Global variables that store tree data for rendering
var treeData = "",
    tree = "",
    nodeLayer = {},
    linkLayer = {},
    controllerFile = "",
    svg = "";

var i = 0,
    duration = 0,
    root;

var margin = {top: 20, right: 120, bottom: 20, left: 120},
    width = 1560 - margin.right - margin.left,
    height = 800 - margin.top - margin.bottom,
    zoom = "",
    dTcontainer;

// var width, height;

function svgSetup() {
    zoom = d3.zoom()
        .on("zoom", ({transform}) => {
            dTcontainer.attr("transform", transform);
        });

    const parentBoundingRect = d3.select("#treeHere").node().getBoundingClientRect();
    svg = d3.select("#treeHere").append("svg")
        .attr("width", parentBoundingRect.width)
        .attr("height", parentBoundingRect.height)
        // .attr("viewBox", `0 0 300 600`)
        .attr("style", "overflow-x: auto; overflow-y: auto;");


    dTcontainer = svg.append("g")
        .attr("id", "mainDtContainer");
    svg.call(zoom);

    link_layer = d3.select("svg g").append("g");
    node_layer = d3.select("svg g").append("g");
}

function constructTree(data) {
    // Generates the tree diagram
    // const parentBoundingRect = d3.select("#treeHere").node().getBoundingClientRect();
    // console.log("treeHere bounding rect", parentBoundingRect);
    tree = d3.tree()
        .size([height, width]);

    root = d3.hierarchy(data);

    root.descendants().forEach((d, i) => {
        d.id = i;
        d._children = d.children;
    });

    root.x0 = 0;
    root.y0 = 0;
}

function setSelectedNode(d) {
    selectedNode = d;
    document.getElementById("nodeSelectInfo").innerText = "Selected " + selectedNode.data.name;
    document.getElementById("retrain-button").disabled = false;
    document.getElementById("interactive-button").disabled = false;
}

function unsetSelectedNode() {
    if (selectedNode) {
        selectedNode.coleur = "";
        update(selectedNode);
        document.getElementById("retrain-button").disabled = true;
        document.getElementById("interactive-button").disabled = true;
    }
    selectedNode = null;
    document.getElementById("nodeSelectInfo").innerText = "";
}

// Toggle children on click.
function click(d) {
    if (customBuild) {
        if (lastNode != null)
            lastNode.coleur = "white";

        d.coleur = "red";
        update(root);

        selectedNode = d.data.address;
        lastNode = d;

        $.ajax({
            data: JSON.stringify({
                address: (d.data.address)
            }),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/refreshImpurities'
        })
            .done(function (data) {
                // TODO see what all to refresh here
                $("#computedPredicatesTableFull > tbody").html("");
                for (let i = 0; i < data.computed_predicates.length; i++) {
                    const dumrow = document.createElement('tr');

                    const drc_inp = document.createElement('td');
                    const drc0_inp = document.createElement('input');

                    drc0_inp.setAttribute('type', 'radio');
                    drc0_inp.setAttribute('name', 'buildPredicate');

                    // Value set to index passed
                    drc0_inp.setAttribute('value', data.computed_predicates[i][0]);

                    drc_inp.appendChild(drc0_inp);
                    dumrow.appendChild(drc_inp);

                    for (let j = 0; j < data.computed_predicates[i].length; j++) {
                        const drc0 = document.createElement('td');
                        drc0.textContent = data.computed_predicates[i][j];
                        if (j === data.computed_predicates[i].length - 1) {
                            drc0.id = "expression" + data.computed_predicates[i][0];
                        }
                        dumrow.appendChild(drc0);
                    }

                    document.getElementById("computedPredicatesTable").appendChild(dumrow);
                }

                for (let i = 0; i < data.updated_impurities.length; i++) {
                    document.getElementById('domainImpurity' + i).textContent = data.updated_impurities[i];
                }

                document.getElementById("splitNodeButton").style.visibility = "visible";
            })
    } else if (nodeSelect) {
        // If a node is already selected, reset its color
        if (selectedNode) {
            selectedNode.coleur = "#fff";
            update(selectedNode);
        }
        // And then select the new node and change its color
        d.coleur = "#e77943";
        setSelectedNode(d);
        update(d);
    } else {
        d.children = d.children ? null : d._children;
        update(d);

        if (d._children) {
            // zoom onto node after collapsing its children
            let adr = d.data.address.toString();
            if (adr == "") {
                timedResetFocus("root");
            } else {
                timedResetFocus(adr);
            }
        }

        // Might need the below call
        // update(root);
    }
}

// Updates the svg generated according to changes in tree data
// Inspired by https://bl.ocks.org/d3noob/8375092 and https://observablehq.com/@d3/collapsible-tree
function update(source) {
    // Compute the new tree layout.
    tree(root);

    let nodes = root.descendants().reverse();
    let links = root.links();

    let diagonal = d3.linkVertical().x(d => d.x).y(d => d.y);
    // let diagonal = (d) => {console.log(d)};

    // Normalize for fixed-depth.
    nodes.forEach(d => {
        d.y = d.depth * 200;
        d.x = d.x * 10;
    });

    // Update the nodes…
    let node = node_layer.selectAll("g.node")
        .data(nodes, function(d) { return d.id; });

    // Enter any new nodes at the parent's previous position.
    let nodeEnter = node.enter().append("g")
        .attr("class", d => {
            // questionmark cursor appears when hovering over too large predicates
            return (d.data.name.length > 20) ? "node scaled" : "node";
        })
        .attr("id", d => {
            return (d.data.address.length == 0) ? "node-at-root" : "node-at-" + d.data.address;
        })
        // .attr("transform", d => {
        //     return "translate(" + source.x0 + "," + source.y0 + ")";
        // })  // Horizontal layout: flip x, y
        .on("click", (event, d) => { click(d); })
        .attr("transform", d => {
            return (d.data.address.length == 0) ? "translate(0,0)" : "";
        });

    nodeEnter.append("circle")
        .attr("r", 1e-6);

    // TODO P: use https://bl.ocks.org/mbostock/1424037 instead of text to allow CSS features such as
    nodeEnter.append("text")
        .attr("x", "-13")
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .attr("id", d => {
            return "addr" + d.data.address.toString();
        })
        .attr("class", "node-text")
        .text(d => {
            return d.data.name;
        })
        .style("fill-opacity", 1e-6);

    // title element contains whole predicate (uncut)
    nodeEnter.append("title");

    // Transition nodes to their new position.
    let nodeUpdate = node.merge(nodeEnter).transition()
        .duration(duration)
        .attr("transform", d => {
            return "translate(" + d.x + "," + d.y + ")";
        });  // Horizontal layout: flip x, y

    nodeUpdate.select("circle")
        .attr("r", 10)
        .style("fill", d => {
            return d.children || !d._children ? d.coleur : "lightsteelblue";
        });

    nodeUpdate.select("text")
        .attr("x", "-13")
        .attr('dy', '.35em')
        .attr("text-anchor", "end")
        .attr("id", d => {
            return "addr" + d.data.address.toString();
        })
        .text(function (d) {
            let nodeText = d.data.name;

            // scales predicate down, if too large
            if (nodeText.length > 20 && (d.data.children.length != 0 || d.data._children)) {
                // nodeText is a predicate with children which is too long
                let sliced_pred, rel;

                if (nodeText.includes("<=")){
                    sliced_pred = nodeText.split("<=");
                    rel = "<=";
                }else if (nodeText.includes(">=")){
                    sliced_pred = nodeText.split(">=");
                    rel = ">=";
                }else if (nodeText.includes(">")){
                    sliced_pred = nodeText.split(">");
                    rel = ">";
                }else if (nodeText.includes("<")){
                    sliced_pred = nodeText.split("<");
                    rel = "<";
                }else if (nodeText.includes("=")){
                    sliced_pred = nodeText.split("=");
                    rel = "=";
                }
                else {
                    // Edge Case: No valid relation found within predicate
                    console.log("Could not reduce size of predicate " + nodeText);
                    return nodeText;
                }
                if (nodeText.substring(0, 10).lastIndexOf(" ") === -1) {
                    nodeText = sliced_pred[0].substring(0, 10) + " ... " + rel + sliced_pred[1];
                } else {
                    nodeText = sliced_pred[0].substring(0, nodeText.substring(0, 10).lastIndexOf(" ")) + " ... " + rel + sliced_pred[1];
                }

            }else if (nodeText.length > 20) {
                // nodeText is a leaf node without children
                let sliced_leaf = nodeText.split(", ");
                nodeText = sliced_leaf[0] + ", ... ," + sliced_leaf[sliced_leaf.length - 1];
            }

            return nodeText;
        })
        .style("fill-opacity", 1);

    // title containing the whole predicate which can be shown by hovering over the element
    nodeUpdate.select("title")
        .text(function (d) {
            return d.data.name;
        });

    // Transition exiting nodes to the parent's new position.
    let nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", d => {
            return "translate(" + source.x + "," + source.y + ")";
        })  // Horizontal layout: flip x, y
        .remove();

    nodeExit.select("circle")
        .attr("r", 1e-6);

    nodeExit.select("text")
        .style("fill-opacity", 1e-6);

    // Update the links…
    let link = link_layer.selectAll("path.link")
        .data(links, d => { d.target.id });

    // Enter any new links at the parent's previous position.
    const linkEnter = link.enter().insert("path", "g")
        .attr("class", "link")
        .style("stroke-dasharray", d => {
            let foo = d.target.data.address[d.target.data.address.length - 1];
            return (foo == 1) ? "10,10" : "1,0";
        })
        .attr("d", d => {
            const o = {x: source.x0, y: source.y0};
            return diagonal({source: o, target: o});
        });

    // Transition links to their new position.
    link.merge(linkEnter).transition()
        .duration(duration)
        .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(duration)
        .attr("d", d => {
            const o = {x: source.x, y: source.y};
            return diagonal({source: o, target: o});
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(d => {
        d.x0 = d.x;
        d.y0 = d.y;
    });

}

function timedResetFocus(idDestination){
    setTimeout(function () {
                resetFocus(idDestination);
            }, 100);
}

function resetFocus(idDestination) {

    let foo = document.getElementById("node-at-" + idDestination).attributes.transform.value;
    let cWidth = document.getElementById("treeHere").clientWidth;
    let cHeight = document.getElementById("treeHere").clientHeight;

    if (foo){
        let xVal = getTransformation(foo).translateX;
        let yVal = getTransformation(foo).translateY;
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate((xVal - cWidth*0.5)*(-1), (yVal - cHeight*0.5)*(-1)));
    }
}

// extracted from https://stackoverflow.com/questions/38224875/replacing-d3-transform-in-d3-v4
function getTransformation(transform) {
    // Create a dummy g for calculation purposes only. This will never
    // be appended to the DOM and will be discarded once this function
    // returns.
    var g = document.createElementNS("http://www.w3.org/2000/svg", "g");

    // Set the transform attribute to the provided string value.
    g.setAttributeNS(null, "transform", transform);

    // consolidate the SVGTransformList containing all transformations
    // to a single SVGTransform of type SVG_TRANSFORM_MATRIX and get
    // its SVGMatrix.
    var matrix = g.transform.baseVal.consolidate().matrix;

    // Below calculations are taken and adapted from the private function
    // transform/decompose.js of D3's module d3-interpolate.
    var {a, b, c, d, e, f} = matrix;   // ES6, if this doesn't work, use below assignment
    // var a=matrix.a, b=matrix.b, c=matrix.c, d=matrix.d, e=matrix.e, f=matrix.f; // ES5
    var scaleX, scaleY, skewX;
    if (scaleX = Math.sqrt(a * a + b * b)) a /= scaleX, b /= scaleX;
    if (skewX = a * c + b * d) c -= a * skewX, d -= b * skewX;
    if (scaleY = Math.sqrt(c * c + d * d)) c /= scaleY, d /= scaleY, skewX /= scaleY;
    if (a * d < b * c) a = -a, b = -b, skewX = -skewX, scaleX = -scaleX;
    return {
        translateX: e,
        translateY: f,
        rotate: Math.atan2(b, a) * 180 / Math.PI,
        skewX: Math.atan(skewX) * 180 / Math.PI,
        scaleX: scaleX,
        scaleY: scaleY
    };
}

// Makes nodes red along the path given as 'str'
function colourPath(str) {
    if (treeAnimation) {
        root.coleur = "red";
        let dummy = root;
        for (let i = 0; i < str.length; i++) {
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
    if (treeAnimation && lastPath && currentSim >= 0) {
        root.coleur = "white";
        let dummy = root;
        for (let i = 0; i < lastPath[currentSim].length; i++) {
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
        let ans = 0;
        for (let i = 0; i < depthNode.children.length; i++) {
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
        let ans = 0;
        for (let i = 0; i < depthNode.children.length; i++) {
            ans += getLeaves(depthNode.children[i]);
        }
        return ans;
    } else {
        return 1;
    }
}

// Expands all tree nodes
function expandAll() {
    function expandRecursive(node) {
        node.descendants().forEach((d, i) => {
            if (d._children && !d.children) {
                d.children = d._children;
                expandRecursive(d);
            }
        });
    }
    expandRecursive(root);
    update(root);
}

// Collapses all tree nodes
function collapseAll() {
    root.descendants().forEach((d, i) => {
       d.children = null;
    });
    update(root);
}

function enableNodeSelect() {
    unsetSelectedNode();
    nodeSelect = true;
    document.getElementById("nodeSelectInfo").innerText = "Click on a node to select.";
}

function disableNodeSelect() {
    unsetSelectedNode();
    nodeSelect = false;
    document.getElementById("nodeSelectInfo").innerText = "";
}

// If cartpole model used, draws it
function drawCanvas() {
    if (controllerFile == "cartpole.scs") {
        let lineLength = 100;
        let canvas = document.getElementById("cartCanvas");
        let c = canvas.getContext("2d");

        c.clearRect(0, 0, 450, 250);

        c.fillStyle = "#000000";
        c.fillRect(150, 160, 150, 60);

        c.beginPath();
        c.moveTo(225, 160);
        c.lineWidth = 7;
        c.strokeStyle = "#802b00";
        let currentAngle = parseFloat(xCurrent[0][currentSim]);
        c.lineTo(225 + lineLength * Math.cos(currentAngle - (Math.PI / 2)), 160 - lineLength * Math.sin(currentAngle - (Math.PI / 2)));
        c.stroke();
    }


}

// Checks if state variables go out of bounds at any point
function checkBounds() {
    for (let i = 0; i < stateDimension; i++) {
        // console.log("Current bounds: ", xCurrent[i][currentSim]);
        // console.log("Outer bounds: ", xBoundsOuter[i][0], ", ", xBoundsOuter[i][1]);
        if (xCurrent[i][currentSim] < xBoundsOuter[i][0] || xCurrent[i][currentSim] > xBoundsOuter[i][1]) {
            return false;
        }
    }
    return true;
}

function tableScroller () {
    tab.querySelector("thead").style.transform = "translate(0," + this.scrollTop + "px)";
}

function initializeSimulatorTablesAndCharts(stateDimension, actionDimension, ) {
    // TODO P: Find all the global variables used here and allow to reset them
    for (let i = 0; i < stateDimension; i++) {
        xCurrent.push([]);
        chart.push([]);
        chartConfig.push([]);
    }
    for (let i = 0; i < actionDimension; i++) {
        // console.log(`Pushing [] to uCurrent`);
        uCurrent.push([]);
    }
    const tab = document.getElementById('simTable');

    tab.addEventListener("scroll", tableScroller);

    // Header row
    const dumrow = document.createElement('tr');
    const drc0 = document.createElement('th');
    drc0.setAttribute("scope", "col");
    drc0.textContent = "Index";
    dumrow.appendChild(drc0);

    const chartsDiv0 = document.getElementById('chartsHere0');
    const chartsDiv1 = document.getElementById('chartsHere1');

    for (let i = 0; i < stateDimension; i++) {
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
        if (i % 2 === 0) {
            chartsDiv0.appendChild(heir0);
        } else {
            chartsDiv1.appendChild(heir0);
        }

    }

    if (actionDimension === 1) {
        const drc2 = document.createElement('th');
        drc2.setAttribute("scope", "col");
        drc2.textContent = "u";
        dumrow.appendChild(drc2);
    } else {
        for (let i = 0; i < actionDimension; i++) {
            const drc2 = document.createElement('th');
            drc2.setAttribute("scope", "col");
            drc2.textContent = "u" + i;
            dumrow.appendChild(drc2);
        }
    }
    tab.deleteRow(-1);
    tab.tHead.appendChild(dumrow);
    // simTableDiv.appendChild(tab);
}

function destroySimulatorTablesAndCharts() {
    xCurrent = [];
    chart = [];
    chartConfig = [];
    uCurrent = [];
    nextDisabled = false;

    const tab = document.getElementById('simTable');
    tab.removeEventListener("scroll", tableScroller);

    // Empty table
    $("#simTable tr").remove();

    // Empty charts
    document.getElementById("chartsHere0").innerHTML = "";
    document.getElementById("chartsHere1").innerHTML = "";
}

// Renders all the charts using Chart.js
function renderChart(id, data, labels, ub, lb) {
    let chartIndex = parseInt(id);

    let ctx = document.getElementById('chartContainer' + id).getContext('2d');
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
    // console.log((currentSim+1) + ': oneStep is called');
    recolourPath();

    if (currentSim == totalSims) {

        if (nextDisabled) {
            popupModal("Error", "Simulation trace out of bounds. Refresh page and try different initial values.");
            clearInterval(plpause);
            return;
        }

        let x_toPass = [];
        for (let i = 0; i < stateDimension; i++) {
            x_toPass.push(xCurrent[i][currentSim]);
        }
        let u_toPass = [];
        for (let i = 0; i < actionDimension; i++) {
            u_toPass.push(uCurrent[i][currentSim]);
        }

        $.ajax({
            data: JSON.stringify({
                id: idUnderInspection,
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

                for (let i = 0; i < stateDimension; i++) {
                    const drc1 = document.createElement('td');
                    drc1.textContent = data.x_new[0][i];
                    dumrow.appendChild(drc1);
                }

                for (let i = 0; i < actionDimension; i++) {
                    const drc2 = document.createElement('td');
                    drc2.textContent = data.x_new[1][i];
                    dumrow.appendChild(drc2);
                }
                tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                scrollToEndOfTable();


                colourPath(data.x_new[2]);

                for (let i = 0; i < stateDimension; i++) {
                    xCurrent[i].push(data.x_new[0][i]);
                }
                for (let i = 0; i < actionDimension; i++) {
                    // console.log(`Pushing ${data.x_new[1][i]} to uCurrent[${i}]`);
                    uCurrent[i].push(data.x_new[1][i]);
                }

                lastPath.push(data.x_new[2]);
                totalSims++;
                currentSim = totalSims;
                console.log("update complete");

                for (let i = 0; i < stateDimension; i++) {
                    chart[i].data.labels.push(totalSims);
                    chart[i].data.datasets[1].data.push(xBoundsOuter[i][1]);
                    chart[i].data.datasets[2].data.push(xBoundsOuter[i][0]);
                    chart[i].update();
                }

                if (!checkBounds()) {
                    console.log("Simulation trace out of bounds, disabling further steps.");
                    popupModal("Error", "Simulation trace out of bounds, disabling further steps. Refresh page and try different initial values.");
                    nextDisabled = true;
                    clearInterval(plpause);
                }

            });         ``
    } else {
        currentSim++;
        $("input[name=indexers][value=" + currentSim + "]").trigger('click');

    }

    drawCanvas();

}

function scrollToEndOfTable() {
    let elem = document.querySelector("#simTable");
    elem.scrollTop = elem.scrollHeight;
}

function assignParentsDfs(node, parent, address_prefix) {
    node.parent = parent;
    node.data.address = address_prefix.concat(node.data.address);
    if (node.children) {
        node.children.forEach((child) => {
            assignParentsDfs(child, node, address_prefix);
        });
    }
}

function replaceInTree(selected, replacementData) {
    // Inspired by https://stackoverflow.com/a/43368677

    //Creates a Node from newNode object using d3.hierarchy(.)
    let newNode = d3.hierarchy(replacementData);
    newNode.descendants().forEach((d, i) => {
        d.id = 10 + i;
        d.depth = selected.depth + d.depth;
        d.height = selected.height - 1;
        d._children = d.children;
    });

    let root_address = selected.data.address;
    // Assign parents and address properly
    // not updating parents breaks the tree on update
    assignParentsDfs(newNode, selected, root_address);
    // console.log("newNode", newNode);

    //Selected is a node, to which we are adding the new node as a child
    selected.children = newNode.children;
    selected.data = newNode.data;
    if (selected.children) {
        selected.children.forEach((child) => {
            child.parent = selected;
        });
    }

    // Render tree in the canvas properly
    console.log("Updating tree render...");
    if (root_address.length > 0) {
        update(selected.parent);
    } else {
        update(selected);
    }
}

function run_partial_construction(configuration) {
    $.ajax({
        data: JSON.stringify(configuration),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/construct-partial/from-preset',
        beforeSend: () => {
            $("body").css("cursor", "progress");
            document.getElementById("retrain-button").disabled = "true";
            document.getElementById("interactive-button").disabled = "true";
        },
    }).done(data => {
        // Change existing tree data at the necessary position to data
        console.log("Return from partial construct");

        // console.log("newData: ", data);
        let pointer = root;
        configuration.selected_node.forEach((pos) => {
            pointer = pointer.children[pos]
        });

        treeData = data["full_json"];
        height = 25 * getLeaves(treeData);
        width = 200 * getDepth(treeData);

        // TODO: In place replacement
        // replaceInTree(pointer, data["partial_json"]);

        constructTree(treeData);
        update(root);

        // console.log(configuration.selected_node.toString());

        let adr = configuration.selected_node.toString();
        if (adr === "") {
            timedResetFocus("root");
        } else {
            timedResetFocus(adr);
        }

        // console.log(treeData);

        $("body").css("cursor", "default");

        document.getElementById("retrain-button").removeAttribute("disabled");
        document.getElementById("interactive-button").removeAttribute("disabled");

    });
}

function start_interactive_construction(configuration) {
    $.ajax({
        data: JSON.stringify(configuration),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/construct-partial/interactive',
        beforeSend: () => {
            document.getElementById("retrain-button").disabled = "true";
            document.getElementById("interactive-button").disabled = "true";},
    }).done(data => {
        // Change existing tree data at the necessary position to data
        console.log("Return from interactive construct");

        let pointer = root;
        configuration.selected_node.forEach((pos) => {
            pointer = pointer.children[pos]
        });

        treeData = data["full_json"];
        height = 25 * getLeaves(treeData);
        width = 200 * getDepth(treeData);

        // TODO: In place replacement
        // replaceInTree(pointer, data["partial_json"]);

        constructTree(treeData);
        update(root);

        // console.log(configuration.selected_node.toString());

        let adr = configuration.selected_node.toString();
        if (adr === "") {
            timedResetFocus("root");
        } else {
            timedResetFocus(adr);
        }

        $("body").css("cursor", "default");

        document.getElementById("retrain-button").removeAttribute("disabled");
        document.getElementById("interactive-button").removeAttribute("disabled");
    });
}

function titleCase(str) {
  return str.toLowerCase().split(' ').map(function(word) {
    return word.replace(word[0], word[0].toUpperCase());
  }).join(' ');
}

function generate_html_table(table_selector, body_index, header, body, add_radio=false, radio_name=null) {
    /*
    For certain tables, we have two tbodys. The body_index allows to choose which tbody to insert the data into.
     */
    let thead = table_selector.tHead;
    thead.innerHTML = "";
    let row = thead.insertRow();
    if (add_radio) {
        let th = document.createElement("th");
        th.setAttribute("scope", "col");
        row.appendChild(th);
    }
    for (let key of header) {
        let th = document.createElement("th");
        th.setAttribute("scope", "col");
        let text = document.createTextNode(titleCase(key));
        th.appendChild(text);
        row.appendChild(th);
    }

    let tbody = table_selector.getElementsByTagName('tbody')[body_index];
    tbody.innerHTML = "";
    for (let index in body) {
        let row = tbody.insertRow();

        if (add_radio) {
            let radio = document.createElement('td');
            let radio_inp = document.createElement('input');

            radio_inp.setAttribute('type', 'radio');
            radio_inp.setAttribute('name', radio_name);
            radio_inp.setAttribute('value', body[index][0]);
            radio_inp.setAttribute('checked', 'checked');

            radio.appendChild(radio_inp);
            row.appendChild(radio);
        }

        for (let val of body[index]) {
            let cell = row.insertCell();
            let text = document.createTextNode(val);
            cell.appendChild(text);
        }
    }
}

function process_interaction_response(data) {
    if (data.type === "error") {
        popupModal("Error", data.body);
        // Show error in a modal?
    }
    else if (data.type === "success") {
        if (data.body.includes("use")) {
            // Use succeeded
            document.getElementById("mainRow1").scrollIntoView({ behavior: 'smooth', block: "start"});
        }
    }
    else if (data.type === "update") {
        if (data.body.feature_information || data.body.feature_specification) {
            let feature_specification = data.body.feature_information ? data.body.feature_information : data.body.feature_specification;
            generate_html_table(document.getElementById("feature-specification-table"),
                0, feature_specification.header, feature_specification.body);
        } else {
            // If return object doesn't contain this key-value pair, remove from table (1st tbody)
            document.getElementById("feature-specification-table").getElementsByTagName("tbody")[0].innerHTML = "";
        }
        if (data.body.label_specification) {
            let label_specification = data.body.label_specification;
            generate_html_table(document.getElementById("label-specification-table"),
                0, label_specification.header, label_specification.body);
        } else {
            // If return object doesn't contain this key-value pair, remove from table (1st tbody)
            document.getElementById("label-specification-table").getElementsByTagName("tbody")[0].innerHTML = "";
        }
        if (data.body.label_statistics) {
            let label_statistics = data.body.label_statistics;
            generate_html_table(document.getElementById("label-statistics-table"),
                0, label_statistics.header, label_statistics.body);
        }
        if (data.body.standard_alt_predicates) {
            let standard_alt_predicates = data.body.standard_alt_predicates;
            generate_html_table(document.getElementById("computed-predicates-table"),
                0, standard_alt_predicates.header, standard_alt_predicates.body,
                true, "instantiated-predicate");
        } else {
            // If return object doesn't contain this key-value pair, remove from table (1st tbody)
            document.getElementById("computed-predicates-table").getElementsByTagName("tbody")[0].innerHTML = "";
        }
        if (data.body.recently_added_predicates) {
            let recently_added_predicates = data.body.recently_added_predicates;
            generate_html_table(document.getElementById("computed-predicates-table"),
                1, recently_added_predicates.header, recently_added_predicates.body,
                true, "instantiated-predicate");
        } else {
            // If return object doesn't contain this key-value pair, remove from table (2nd tbody)
            document.getElementById("computed-predicates-table").getElementsByTagName("tbody")[1].innerHTML = "";
        }
        if (data.body.standard_predicates_collection) {
            let standard_predicates_collection = data.body.standard_predicates_collection;
            generate_html_table(document.getElementById("standard-predicates-collection"),
                0, standard_predicates_collection.header, standard_predicates_collection.body,
                true, "abstract-predicate");
        } else {
            // If return object doesn't contain this key-value pair, remove from table (1st tbody)
            document.getElementById("standard-predicates-collection").getElementsByTagName("tbody")[0].innerHTML = "";
        }
        if (data.body.recently_added_predicates_collection) {
            let recently_added_predicates_collection = data.body.recently_added_predicates_collection;
            generate_html_table(document.getElementById("standard-predicates-collection"),
                1, recently_added_predicates_collection.header, recently_added_predicates_collection.body,
                true, "abstract-predicate");
            // console.log(recently_added_predicates_collection.length);
            document.getElementById("delete-predicate-button").disabled = (recently_added_predicates_collection.length === 0);
        } else {
            // If return object doesn't contain this key-value pair, remove from table (2nd tbody)
            document.getElementById("standard-predicates-collection").getElementsByTagName("tbody")[1].innerHTML = "";
            document.getElementById("delete-predicate-button").disabled = true;
        }
    }
    else if (data.type === "error") {
        console.error(data.body);
    }
    $("body").css("cursor", "default");
}

function add_predicate()
{
    let predicate = window.prompt("Enter predicate", "x_0 + 3*x_1 <= c_0; c_0 in {20, 40, 60, 80}");
    $.ajax({
        data: JSON.stringify({"action": "add", "body": predicate}),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/interact',
        beforeSend: () => {
            $("body").css("cursor", "progress")
        },
    }).done(data => {
        console.log("Return from add");
        // console.log(data);
        try {
            let response = JSON.parse(data);
            process_interaction_response(response);
        }
        catch (error) {
            console.error(error);
        }
    });
}

function remove_predicate() {
    let selected_predicate_id = +document.querySelector('input[name = "abstract-predicate"]:checked').value;
    $.ajax({
        data: JSON.stringify({"action": "del", "body": selected_predicate_id}),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/interact',
        beforeSend: () => {
            $("body").css("cursor", "progress")
        },
    }).done(data => {
        console.log("Return from del");
        // console.log(data);
        try {
            let response = JSON.parse(data);
            process_interaction_response(response);
        }
        catch (error) {
            console.error(error);
        }
    });
}

function use_predicate() {
    let selected_predicate_id = +document.querySelector('input[name = "instantiated-predicate"]:checked').value;
    if (selectedNode) {
        $.ajax({
            data: JSON.stringify({"action": "use", "body": selected_predicate_id}),
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: '/interact',
            beforeSend: () => {
                $("body").css("cursor", "progress");

                // Empty the all tables
                document.getElementById("feature-specification-table").childNodes[3].innerHTML = "";
                document.getElementById("label-specification-table").childNodes[3].innerHTML = "";
                document.getElementById("label-statistics-table").childNodes[3].innerHTML = "";

                // // Disable Add/Del/Use Buttons
                document.getElementById("use-predicate-button").disabled = true;
                document.getElementById("add-predicate-button").disabled = true;
                document.getElementById("delete-predicate-button").disabled = true;
            },
        }).done(data => {
            console.log("Return from use");
            // console.log(data);
            try {
                let response = JSON.parse(data);
                process_interaction_response(response);
            } catch (error) {
                console.error(error);
            }
        });
    }
}

function refresh_interactive_tables() {
    $.ajax({
        data: JSON.stringify({"action": "refresh"}),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/interact',
        beforeSend: () => {
            $("body").css("cursor", "progress");
        },
    }).done(data => {
        console.log("Return from refresh");
        // console.log(data);
        // Unhide the cards related to interactive tree builder
        document.getElementById("mainRow-interactive").classList.remove("d-none");
        try {
            let response = JSON.parse(data);
            process_interaction_response(response);
        }
        catch (error) {
            console.error(error);
        }
        // Scroll the interactive tree builder cards into view
        document.getElementById("mainRow-interactive").scrollIntoView({ behavior: 'smooth', block: "start"});

        // // Reactivate Add/Del/Use Buttons
        document.getElementById("use-predicate-button").removeAttribute("disabled");
        document.getElementById("add-predicate-button").removeAttribute("disabled");
        document.getElementById("delete-predicate-button").removeAttribute("disabled");
    });
}

function deactivateSimulator() {
    // Return node colors to white
    recolourPath();
    destroySimulatorTablesAndCharts();
    isSimulator = false;
    document.getElementById("mainRow2").classList.add("d-none");
    document.getElementById("mainRow3").classList.add("d-none");
    //document.getElementById("expandThisDiv").style.height = "450px";
    document.getElementById("playerDiv").classList.add("d-none");
    document.getElementById("timeRangeContainer").classList.add("d-none");
    document.getElementById("instep").classList.add("d-none");
    document.getElementById("animationDiv").classList.add("d-none");

    $("#dynamics-body").show();
    $("#initial-values").hide();
    $("#formSecond-next-button").show();
    $("#formSecond-randomize-button").hide();
    $("#formSecond-submit-button").hide();
    $("#exampleModalLongTitle").html("Enter system dynamics");

    // document.getElementById("hideThisDiv").style.display = "block";
}

function deactivateEdit()
{
    document.getElementById("expandAllButton").removeAttribute("disabled");
    document.getElementById("collapseAllButton").removeAttribute("disabled");

    document.getElementById("retrain-button").classList.add("d-none");
    document.getElementById("interactive-button").classList.add("d-none");

    // editMode = false;
    disableNodeSelect();
    // update(root);
}

function deactivateInspect()
{
    // Nothing here
}

$(document).ready(function () {

    // If we are in the inspect/edit/simulate screen, there is no need for having the "load controller directory" etc available
    document.getElementById("controller-upload-row").remove();
    document.getElementById("metadata-upload-row").remove();
    document.getElementById("add-experiments-button").remove();

    // Retrain from sidenav
    $("input[name='retrain'], button[name='retrain']").on('click', function (event) {
        event.preventDefault();
        let configuration = {};
        configuration.id = idUnderInspection;
        configuration.controller = controllerFile;
        configuration.config = $('#config').val();
        configuration.determinize = $('#determinize').val();
        configuration.numeric_predicates = $('#numeric-predicates').val();
        configuration.categorical_predicates = $('#categorical-predicates').val();
        configuration.impurity = $('#impurity').val();
        configuration.tolerance = $('#tolerance').val();
        configuration.safe_pruning = $('#safe-pruning').val();
        configuration.user_predicates = "";

        if (configuration.config === "algebraic") {
            configuration.config += " (Fallback: " + $("#fallback").val() + ")";
            configuration.numeric_predicates = [""];
            configuration.categorical_predicates = [""];
            configuration.user_predicates = $('#userPredicatesInput').val();
        }

        if (selectedNode) {
            configuration.selected_node = selectedNode.data.address;
            run_partial_construction(configuration);
        }
        else {
            // Nothing to do if node is not selected
            // Control must not come here
            console.assert(selectedNode);
        }
     });

    // Retrain from sidenav
    $("input[name='interact'], button[name='interact']").on('click', function (event) {
        event.preventDefault();
        let configuration = {};
        configuration.id = idUnderInspection;
        configuration.controller = controllerFile;

        if (selectedNode) {
            configuration.selected_node = selectedNode.data.address;

            // Populate the tree builder cards

            // The following call will trigger fit() in dtcontrol
            // and also makes the backend connect to the websocket.
            start_interactive_construction(configuration);

            console.log("Started interactive mode from " + selectedNode.data.address);
            // Send the refresh command to fetch the tables
            setTimeout(refresh_interactive_tables, 2000);

            // Add button in recent predicates collection
        }
        else {
            // Nothing to do if node is not selected
            // Control must not come here
            console.assert(selectedNode);
        }
     });


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

    // Simulate Button
    $("#operation-selector input").on("click", function (event) {
        let option = $("#operation-selector input:checked")[0].id;
        console.log("Selected " + option);
        if (option === "option-simulate") {
            isSimulator = true;
            initializeSimulatorTablesAndCharts();
            deactivateInspect();
            deactivateEdit();
            triggerDynamicsInput();
            document.getElementById("mainRow2").classList.remove("d-none");
            document.getElementById("mainRow3").classList.remove("d-none");
            //document.getElementById("expandThisDiv").style.height = "450px";
            document.getElementById("playerDiv").classList.remove("d-none");
            document.getElementById("timeRangeContainer").classList.remove("d-none");
            document.getElementById("instep").classList.remove("d-none");
            // document.getElementById("animationDiv").classList.remove("d-none");
        }
        else if (option === "option-edit") {
            deactivateSimulator();
            deactivateInspect();
            // Activate Edit Mode
            document.getElementById("retrain-button").classList.remove("d-none");
            document.getElementById("interactive-button").classList.remove("d-none");

            document.getElementById("expandAllButton").disabled = "true";
            document.getElementById("collapseAllButton").disabled = "true";

            // editMode = true;
            enableNodeSelect();
            // update(root);
        }
        else {
            // Inspect
            deactivateSimulator();
            deactivateEdit();
        }

    });

    $.get('/computed', (data) => {
        document.getElementById("mainRow1").style.visibility = "visible";
        // document.getElementById("editTreeDiv").style.visibility = "visible";

        idUnderInspection = data.idUnderInspection
        treeData = data.classifier;
        // console.log("Tree Data", treeData);
        stateDimension = data.numVars;
        actionDimension = data.numResults;
        controllerFile = data.controllerFile;

        // console.log(treeData);

        // TODO C: Check if these two lines affect the tree layout (see the svgSetup() and constructTree() below)
        // height = 50 * getLeaves(treeData);
        height = 25 * getLeaves(treeData);
        // height = 650;
        width = 200 * getDepth(treeData);

        svgSetup();
        constructTree(treeData);
        update(root);

        timedResetFocus("root");

        const opt = document.getElementById("formSecondBody");
        for (let i = 0; i < stateDimension; i++) {
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

            // console.log(i + ": pushing outer bounds " + [data.boundOuter[0][i], data.boundOuter[1][i]]);
            // console.log(i + ": pushing inner bounds " + [data.boundInner[0][i], data.boundInner[1][i]]);
            xBoundsOuter.push([data.boundOuter[0][i], data.boundOuter[1][i]]);
            xBoundsInner.push([data.boundInner[0][i], data.boundInner[1][i]])
        }
    });

    // Submits popup modal form (for passing initial values of state variables)
    $('#formSecond').on('submit', function (event) {
        // console.log('form is submitted');
        initializeSimulatorTablesAndCharts(stateDimension, actionDimension)
        let x_toPass = [];
        for (let i = 0; i < stateDimension; i++) {
            x_toPass.push(parseFloat($('#x' + i).val())); // TODO generalize this - x all the time might not work
        }
        $.ajax({
            data: JSON.stringify({id: idUnderInspection, pass: x_toPass, dynamics: $("#dynamics-input").val()}),
            contentType: "application/json; charset=utf-8",
            type: 'POST',
            url: '/initRoute'
        })
            .done(function (data) {
                document.getElementById("mainRow2").classList.remove("d-none");
                document.getElementById("mainRow3").classList.remove("d-none");
                document.getElementById("expandThisDiv").style.height = "450px";
                document.getElementById("playerDiv").classList.remove("d-none");
                document.getElementById("timeRangeContainer").classList.remove("d-none");
                document.getElementById("instep").classList.remove("d-none");
                document.getElementById("animationDiv").classList.remove("d-none"); // TODO Animate button, enable this again

                let mini = document.getElementsByClassName("card-body");
                for (let i = 0; i < mini.length; i++) {
                    mini[i].style.height = "425px";
                }
                document.getElementById("treeHere").style.height = "85%";
                document.querySelector("#mainRow2 .card-body").style.height = "350px";

                // resizing to get largest space for tree
                // if (controllerFile == "cartpole.scs") {
                //     document.getElementById("expandThisDiv").className = "col-lg-6";
                //     document.getElementById("hideThisDiv").classList.remove("d-none");
                // } else {
                //     document.getElementById("hideThisDiv").classList.add("d-none");
                // }

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

                for (let i = 0; i < stateDimension; i++) {
                    const drc1 = document.createElement('td');
                    drc1.textContent = $('#x' + i).val();
                    dumrow.appendChild(drc1)
                }
                for (let i = 0; i < actionDimension; i++) {
                    const drc2 = document.createElement('td');
                    drc2.textContent = data.decision[i];
                    dumrow.appendChild(drc2);
                }
                tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                scrollToEndOfTable();
                colourPath(data.path);

                for (let i = 0; i < stateDimension; i++) {
                    xCurrent[i].push(parseFloat($('#x' + i).val()));
                }
                for (let i = 0; i < actionDimension; i++) {
                    uCurrent[i].push(data.decision[i]);
                }

                lastPath.push(data.path);
                totalSims = 0;
                currentSim = 0;

                if (!checkBounds()) {
                    console.log("Simulation trace out of bounds, disabling further steps.");
                    popupModal("Error", "Simulation trace out of bounds, disabling further steps. Refresh page and try different initial values.");
                    nextDisabled = true;
                }

                for (let i = 0; i < stateDimension; i++) {
                    renderChart(i, xCurrent[i], [...Array(currentSim + 1).keys()], [xBoundsOuter[i][1]], [xBoundsOuter[i][0]]);
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
            let x_toPass = [];
            for (let i = 0; i < stateDimension; i++) {
                x_toPass.push(xCurrent[i][currentSim]);
            }
            let u_toPass = [];
            for (let i = 0; i < actionDimension; i++) {
                u_toPass.push(uCurrent[i][currentSim]);
            }
            let steps = $('#steps').val();
            if (steps === "") {
                $('#steps').val("1");
                steps = 1;
            }
            $.ajax({
                data: JSON.stringify({
                    id: idUnderInspection,
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

                    for (let i = 0; i < steps; i++) {
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

                        for (let j = 0; j < stateDimension; j++) {
                            const drc1 = document.createElement('td');
                            drc1.textContent = data.x_new[i][0][j];
                            dumrow.appendChild(drc1);
                        }
                        for (let j = 0; j < actionDimension; j++) {
                            const drc2 = document.createElement('td');
                            drc2.textContent = data.x_new[i][1][j];
                            dumrow.appendChild(drc2);
                        }
                        tab.getElementsByTagName('tbody')[0].appendChild(dumrow);
                        $("#simTable tbody tr:last-child").addClass('selected').siblings().removeClass('selected');
                        scrollToEndOfTable();

                        for (let j = 0; j < stateDimension; j++) {
                            xCurrent[j].push(data.x_new[i][0][j]);
                        }
                        for (let j = 0; j < actionDimension; j++) {
                            uCurrent[j].push(data.x_new[i][1][j]);
                        }

                        lastPath.push(data.x_new[i][2]);
                        totalSims++;
                        currentSim = totalSims;

                        for (let j = 0; j < stateDimension; j++) {
                            chart[j].data.labels.push(totalSims);
                            chart[j].data.datasets[1].data.push(xBoundsOuter[j][1]);
                            chart[j].data.datasets[2].data.push(xBoundsOuter[j][0]);
                        }

                        if (!checkBounds()) {
                            console.log("Simulation trace out of bounds, disabling further steps.");
                            popupModal("Error", "Simulation trace out of bounds, disabling further steps. Refresh page and try different initial values.");
                            nextDisabled = true;
                            clearInterval(plpause);
                            break;
                        }
                    }

                    for (let i = 0; i < stateDimension; i++) {
                        chart[i].update();
                    }
                    colourPath(lastPath[totalSims]);

                    drawCanvas();

                });
        } else {
            popupModal("Error", "Simulation trace out of bounds. Refresh page and try different initial values.");
        }
        event.preventDefault();
    });


    // Handles the player inputs
    $(document).on("click", "input[name=player]", function (event) {
        let option = parseInt($("input[name=player]:checked").val());
        //play pause next back
        if (option === 0) {
            plpause = setInterval(oneStep, timeOfSlider);
        } else if (option === 1) {
            clearInterval(plpause);
        } else if (option === 2) {
            oneStep();
        } else if (option === 3) {
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
        let ind = parseInt($("input[name='indexers']:checked").val());
        recolourPath();
        currentSim = ind;
        colourPath(lastPath[ind]);
        drawCanvas();

    });

    // Simple .change() does not work here because it is dynamically added
    $('#dynamics-file').on('change', function () {
        //get the file name
        let fileName = $(this).val().replace('C:\\fakepath\\', "");
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
        let file = document.getElementById("dynamics-file").files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            // The file's text will be printed here
            $("#dynamics-input").val(e.target.result);
        };
        reader.readAsText(file);
    });
});

// Handles play speed slider
let slider = document.getElementById("timeRange");
if (slider) {
    slider.oninput = function () {
        // 1x = 500ms
        if (parseInt($("input[name=player]:checked").val()) == 0) {
            timeOfSlider = 500 / this.value;
            clearInterval(plpause);
            plpause = setInterval(oneStep, timeOfSlider);
        } else {
            timeOfSlider = 500 / this.value;
        }
        document.getElementById("timeRate").innerText = parseFloat(this.value).toFixed(2) + "x";
    }
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

function splitNode() {
    let toSendPredicate = $('input[name="buildPredicate"]:checked').val();
    // console.log(toSendPredicate);
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
            let numSplits = data.number_splits;
            lastNode.children = [];
            for (let i = 0; i < numSplits; i++) {
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

// Randomize button in Modal for selecting initial values of state variables
function randomizeInputs() {
    // console.log(idUnderInspection);
    $.ajax({
        data: JSON.stringify({
            id: idUnderInspection
        }),
        type: 'POST',
        contentType: "application/json; charset=utf-8",
        url: '/random'
    })
        .done(function (data) {
            console.log("Received random point " + data);
            for (let i = 0; i < stateDimension; i++) {
                document.getElementById('x' + i).value = data[i];
            }
        });
}

// Opens second form (for initial state variable selection)
function triggerDynamicsInput() {
    $('#formSecondModal').modal('show');
}

// Have to select dynamically created elements like this
// Handles colouring of table rows when clicked
$(document).on("click", "#simTable tbody tr", function () {
    $(this).addClass('selected').siblings().removeClass('selected');
    let value = $(this).find('td:first').children()[0].getAttribute("value")
    $(this).find('td input[type=radio]').prop('checked', true);
    // let ind = parseInt($("input[name='indexers']:checked").val());
    let ind = parseInt(value);
    recolourPath();
    currentSim = ind;
    colourPath(lastPath[ind]);
    drawCanvas();
});

// 'Animate tree' button and 'Edit tree' button

$(document).on("change", "#animateTree", function () {
    treeAnimation = !treeAnimation;
    // console.log(treeAnimation);
});