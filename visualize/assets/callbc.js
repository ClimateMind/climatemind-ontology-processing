console.log("loaded")

var cyto_storage, node_positions_cache = {};
let old_filter_value = "none"
const personal_value_selector = "increase in physical violence"
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        search_nodes: function (search_term) {
            filter_exported.search_node(search_term)
        },
        update_personal_value: function (personal_value) {
            make_cyto(personal_value)
        },
        update_storage_globals: function (_cyto_storage) {
            cyto_storage = _cyto_storage;
            make_cyto("increase in physical violence")
        },
        fill_output_div: function (dummy) {
            // Initialize output box
            output_div = document.getElementById('output')
            output_div.className = "output_parent"
            output_div.innerHTML = `
<div id='outer_edges' class = "output_child">\
<strong>Effects:</strong>\
<p id="outer_edges_output">Mouse over any node to get its relationships</p>\
</div>\
<div id='inner_edges' class = "output_child">\
<strong>Caused by:</strong>\
<p id="inner_edges_output">Mouse over any node to get its relationships</p>\
</div>\
<h1 id = "node_name_output"></h1>

`

            document.getElementById('right_controls').innerHTML = `
<pre id ="object_output" title="Double click to go to WebProtege">Click on any node to view its JSON properties</pre>` + document.getElementById('right_controls').innerHTML
            document.getElementById('object_output').addEventListener('dblclick', (event) => {
                formattted_iri = event.target.getAttribute("web_protege_iri").slice(24)
                window.open(`https://webprotege.stanford.edu/#projects/de9e0a93-66a8-40c6-bce8-b972847d362f/edit/Individuals?selection=NamedIndividual(%3Chttp://webprotege.stanford.edu/${formattted_iri}%3E)`)
            })
        },

        update_filter: function (filter_value) {
            if (filter_value == "__use_old") {
                filter_value = old_filter_value
            }
            if (filter_value == "no_long_desc") window.filter_exported.apply_no_long_descs()
            else if (filter_value == "no_sources") window.filter_exported.apply_no_sources()
            else if (filter_value == "none") window.filter_exported.apply_none()
            else if (filter_value == "personal_values") window.filter_exported.apply_personal_values()

            old_filter_value = filter_value

        }
    }
});



