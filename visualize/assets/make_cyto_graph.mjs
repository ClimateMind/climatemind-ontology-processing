import cytoscape from 'https://unpkg.com/cytoscape@3.18.1/dist/cytoscape.esm.min.js'

var cy;


function save_func(personal_value, storage_index = 1) {
    localStorage.setItem(`cytoscape_graph_cache_${personal_value}_${storage_index}`, JSON.stringify(cy.json()))
    document.title = `saved ${storage_index}`
}


export function make_cyto(personal_value, storage_index = 0) {
    if (cy) {
        cy.destroy()
    }


    console.log("Making new graph")
    cy = cytoscape({
        container: document.getElementById('cyto-graph-container'), // container to render in
        // Moving nodes around will actually change data in cyto_storage.
        // Cytoscape owns all objects given to it. Maybe we should create a deep copy?
        elements: cyto_storage[personal_value],
        style: [ // the stylesheet for the graph
            {
                selector: "edge",
                style: {
                    'width': 1,
                    'line-color': 'black',
                    'target-arrow-color': 'red',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 2
                }
            }, {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-wrap': 'wrap',
                    // 'text-max-width': '12em', //TODO: check whether this is necessary?
                    'color': 'hsla(215,0%,19%,1)',
                    'text-halign': 'center',
                    'text-valign': 'center',
                    'width': 'data(cyto_width)',
                    'height': 'data(cyto_height)',
                    'font-size': 20,
                    'shape': 'round-rectangle',
                    'background-color': 'hsl(27,55%,64%)',
                    'padding': '15px 3px 15px 3px'
                }
            }, {
                selector: '.tree_root',
                style: {
                    'background-color': 'hsla(215, 64%, 67%, 1)'
                }
            }, {
                selector: '.risk-solution',
                style: {
                    'background-color': 'hsla(73, 64%, 67%, 1)'
                }
            }, {
                selector: '.solution-edge',
                style: {
                    'line-color': 'green'
                }
            }, {
                selector: '.is-highlighted',
                style: {
                    'background-blacken': 0.15
                }
            }, {
                selector: ".filter-view-one",
                style: {
                    'background-blacken': 0.25
                }
            }],
        layout: {
            name: 'preset'
        }
    });

    let local_storage_key = `cytoscape_graph_cache_${personal_value}_${storage_index}`
    if (localStorage.getItem(local_storage_key) && storage_index) {
        console.log("Reusing old graph: ", local_storage_key)
        const cytoscape_graph_cache = JSON.parse(localStorage.getItem(local_storage_key))
        cy.json(cytoscape_graph_cache)
    }
    register_cy_callbacks(cy)

    // For console debugging only.
    window.cy = cy;

}

function register_cy_callbacks(cy) {
    cy.listen('click', 'edge', function (evt) {
        document.getElementById('object_output').textContent = JSON.stringify(evt.target.data(), undefined, 2)
    })

    cy.listen('click', 'node', function (evt) {
        document.getElementById('object_output').textContent = JSON.stringify(evt.target.data(), undefined, 2)
        document.getElementById('object_output').setAttribute("web_protege_iri", evt.target.data('iri'))
    })
    cy.listen('mouseover', 'node', function (evt) {
        const mouseover_node_data = evt.target.data();
        const outer_edges = []
        const inner_edges = []
        const solutions = []


        evt.target.outgoers('edge').forEach(function (ele, _unused, _unused1) {
            if (ele.classes().includes("solution-edge")) {
                solutions.push(ele.data("target"))
            } else {
                outer_edges.push(ele.data("target"))
            }
        })

        evt.target.incomers('edge').forEach(function (ele, _unused, _unused1) {
            if (ele.classes().includes("solution-edge")) {
                solutions.push(ele.data("source"))
            } else {
                inner_edges.push(ele.data("source"))
            }
        })


        document.getElementById('outer_edges_output').innerHTML = outer_edges.join('.\n\n')
        document.getElementById('inner_edges_output').innerHTML = inner_edges.join('.\n\n')
        document.getElementById('solutions_output').innerHTML = solutions.join('.\n\n')


        // Add is_highlighted attribute to all nodes
        evt.target.closedNeighbourhood().addClass('is-highlighted')
    })
    cy.listen('mouseout', 'node', function (evt) {
        // Remove is-higlighted attribute to all nodes
        evt.target.closedNeighbourhood().removeClass("is-highlighted")
    })

    document.addEventListener('keydown', function (key) {
        if (key.code == "KeyS" && key.altKey) {
            const filter_text = document.getElementById('filter-code').value
            document.getElementById("errors-output").textContent = 'Processing ' + filter_text + '\n'

            cy.nodes('.filter-view-one').removeClass('filter-view-one')

            cy.nodes().forEach(function (ele, _unused, _unused1) {
                key.preventDefault()
                const node = ele.data()

                let filter_passes = false
                try {
                    filter_passes = eval(filter_text)
                } catch (err) {
                    document.getElementById("errors-output").textContent += err + ' ' + filter_passes + '\n';
                }
                document.getElementById("errors-output").textContent += filter_passes + '\n'
                if (filter_passes) {
                    ele.addClass('filter-view-one')
                }
            })
        }
    })
}


document.addEventListener('keydown', function (key) {
    if (key.code == "Digit1" && key.shiftKey) save_func("increase in physical violence", 1)
    else if (key.code == "Digit2" && key.shiftKey) save_func("increase in physical violence", 2)
    else if (key.code == "Digit3" && key.shiftKey) save_func("increase in physical violence", 3)
    else if (key.code == "Digit1") make_cyto("increase in physical violence", 1)
    else if (key.code == "Digit2") make_cyto("increase in physical violence", 2)
    else if (key.code == "Digit3") make_cyto("increase in physical violence", 3)
    else if (key.code == "KeyR") {
        localStorage.clear() // Clear local storage
        console.log("Cleared local storage")
    }

})
window.make_cyto = make_cyto;