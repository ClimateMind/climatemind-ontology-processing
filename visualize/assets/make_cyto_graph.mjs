// noinspection JSFileReferences,JSFileReferences,JSFileReferences,JSFileReferences,JSFileReferences,JSFileReferences
import cytoscape from 'https://unpkg.com/cytoscape@3.18.1/dist/cytoscape.esm.min.js'

let cy, dijkstra, old_filter_value;


function save_func(personal_value, storage_index = 1) {
    localStorage.setItem(`cytoscape_graph_cache_${personal_value}_${storage_index}`, JSON.stringify(cy.json()))
    document.title = `saved ${storage_index}`
}

var filter_exported = {
    apply_no_long_descs: function () {
        cy.$('.problem-view').removeClass('problem-view')
        cy.nodes('node[properties].personal-value,.risk-solution').forEach(function (node) {
            if (node.data('properties')['schema_longDescription'].length === 0) {
                node.addClass('problem-view')
            }
        })
    },
    apply_no_sources: function () {
        cy.$('.problem-view').removeClass('problem-view')
        cy.nodes('node[properties].personal-value, .risk-solution').forEach(function (node) {
            const node_props = node.data('properties')
            if (!(node_props['dc_source'].length ||
                node_props['schema_academicBook'].length ||
                node_props['schema_academicSourceNoPaywall'].length ||
                node_props['schema_academicSourceWithPaywall'].length ||
                node_props['schema_governmentSource'].length ||
                node_props['schema_mediaSource'].length ||
                node_props['schema_mediaSourceForConservatives'].length ||
                node_props['schema_organizationSource'].length)) {
                node.addClass('problem-view')
            }
        })

        cy.edges('.edge-no-source').addClass('problem-view')
    },
    apply_personal_values: function () {
        cy.$('.problem-view').removeClass('problem-view')
        cy.nodes('.personal-value').addClass('problem-view')
    },
    apply_none: function () {
        cy.$('.problem-view').removeClass('problem-view')
    },

    search_node(search_term) {
        cy.$('.filter-view-two').removeClass('filter-view-two')
        cy.getElementById(search_term).flashClass("filter-view-two", 800)
    },
    apply_filter(filter_value = old_filter_value) {
        if (filter_value === "no_long_desc") this.apply_no_long_descs()
        else if (filter_value === "no_sources") this.apply_no_sources()
        else if (filter_value === "none") this.apply_none()
        else if (filter_value === "personal_values") this.apply_personal_values()

        old_filter_value = filter_value
    }
}


export function make_cyto(personal_value, cyto_storage, storage_index = 0) {
    if (cy) {
        cy.destroy()
    }
    console.log("Making new graph")
    cy = cytoscape({
            container: document.getElementById('cytoscape-graph-container'), // container to render in
            // Moving nodes around will actually change data in cyto_storage.
            // Cytoscape owns all objects given to it. Maybe we should create a deep copy?
            elements: cyto_storage[personal_value],
            style: [ // the stylesheet for the graph
                {
                    selector: "edge",
                    style: {
                        'width': 2,
                        'line-color': 'hsl(1, 0%, 60%)',
                        'target-arrow-shape': 'triangle',
                        "target-arrow-color": "hsl(1, 0%, 60%)",
                        'curve-style': 'bezier',
                        'arrow-scale': 2
                    }
                }, {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-wrap': 'wrap',
                        // 'text-max-width': '12em', //TODO: check whether this is necessary?
                        'text-halign': 'center',
                        'text-valign': 'center',
                        'width': 'data(__cyto_width)',
                        'height': 'data(__cyto_height)',
                        'font-size': 24,
                        'font-family': 'Segoe UI',
                        'shape': 'round-rectangle',
                        'background-color': 'hsl(25,60%,81%)',
                        'border-width': '2px',
                        'border-color': 'hsl(18,33%,32%)'
                    }
                }, {
                    selector: '.tree_root',
                    style: {
                        'background-color': 'hsl(213,65%,82%)'
                    }
                }, {
                    selector: '.risk-solution',
                    style: {
                        'background-color': 'hsl(77,52%,79%)'
                    }
                }, {
                    selector: '.solution-edge',
                    style: {
                        "target-arrow-shape": 'none',
                        "source-arrow-shape": "tee"
                    }
                }, {
                    selector: '.is-highlighted',
                    style: {
                        'background-blacken': 0.15
                    }
                }, {
                    selector: "node.filter-view-one",
                    style: {
                        'background-blacken': 0.1
                    }
                }, {
                    selector: "edge.filter-view-one",
                    style: {
                        'width': 4,
                        'line-color': 'black',
                        "target-arrow-color": "black"
                    }
                }, {
                    selector: '.filter-view-two',
                    style: {
                        'border-width': '5px',
                        'border-color': 'hsl(31,92%,23%)',
                        'background-color': "hsl(154,9%,69%)"
                    }
                }, {
                    selector: '.problem-view',
                    style: {
                        'background-blacken': 0.2,
                        'border-width': '10px',
                        'border-color': 'hsl(0,86%,25%)',
                        'line-color': 'red'
                    }
                }],
            layout: {
                name: 'preset'
            },
            wheelSensitivity: 0.15
        });

    let local_storage_key = `cytoscape_graph_cache_${personal_value}_${storage_index}`
    if (localStorage.getItem(local_storage_key) && storage_index) {
        console.log("Reusing old graph: ", local_storage_key)
        const cytoscape_graph_cache = JSON.parse(localStorage.getItem(local_storage_key))
        cy.json(cytoscape_graph_cache)
    }
    register_cy_callbacks(cy)
    filter_exported.apply_filter()
// For console debugging only.
    window.cy = cy;


    dijkstra = cy.elements().dijkstra(cy.getElementById("increase in greenhouse effect"), () => {
        return 1
    }, true)
}


// Export these functions because we're running this as a module.
window.filter_exported = filter_exported


function register_cy_callbacks(cy) {
    cy.listen('click', 'edge', function (evt) {
        document.getElementById('object_output').textContent = JSON.stringify(evt.target.data(), undefined, 2)
    })

    cy.listen('click', 'node', function (evt) {
        document.getElementById('object-output').textContent = JSON.stringify(evt.target.data(), undefined, 2)
        document.getElementById('object-output').setAttribute("web_protege_iri", evt.target.data('iri'))
    })
    cy.listen('mouseover', 'node', function (evt) {
        cy.$('.filter-view-one').removeClass('filter-view-one')

        const outer_edges = []
        const inner_edges = []
        evt.target.outgoers('edge').forEach(function (ele, _unused, _unused1) {
            outer_edges.push(ele.data("target"))
        })

        evt.target.incomers('edge').forEach(function (ele, _unused, _unused1) {
            inner_edges.push(ele.data("source"))
        })


        document.getElementById('outer_edges_output').innerHTML = outer_edges.join('.\n\n')
        document.getElementById('inner_edges_output').innerHTML = inner_edges.join('.\n\n')
        document.getElementById('big-node-name').innerText = evt.target.id()


        // Add is_highlighted attribute to all nodes
        // evt.target.closedNeighbourhood().addClass('is-highlighted')

        dijkstra.pathTo(evt.target).addClass("filter-view-one")
    })
    cy.listen('mouseout', 'node', function (evt) {
        // Remove is-higlighted attribute to all nodes
        // evt.target.closedNeighbourhood().removeClass("is-highlighted")
        dijkstra.pathTo(evt.target).removeClass("filter-view-one")

    })
}


document.addEventListener('keydown', function (key) {
    if (key.code === "Digit1" && key.shiftKey) save_func("increase in physical violence", 1)
    else if (key.code === "Digit2" && key.shiftKey) save_func("increase in physical violence", 2)
    else if (key.code === "Digit3" && key.shiftKey) save_func("increase in physical violence", 3)
    else if (key.code === "Digit1") make_cyto("increase in physical violence", 1)
    else if (key.code === "Digit2") make_cyto("increase in physical violence", 2)
    else if (key.code === "Digit3") make_cyto("increase in physical violence", 3)
    else if (key.code === "KeyR") {
        localStorage.clear() // Clear local storage
        console.log("Cleared local storage")
    }
})
window.make_cyto = make_cyto;