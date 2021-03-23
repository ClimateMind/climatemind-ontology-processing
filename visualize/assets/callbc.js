console.log("loaded")

let cyto_storage;
let old_filter_value = "none"
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {

        // All these functions will be called by Dash.
        search_nodes: function (search_term) {
            filter_exported.search_node(search_term)
        },
        update_personal_value: function (personal_value) {
            if (personal_value == undefined) {
                personal_value = "downstream_mitigations"
            }
            make_cyto(personal_value, cyto_storage)
        },
        update_storage_globals: function (_cyto_storage) {
            cyto_storage = _cyto_storage;
            make_cyto("increase in physical violence", cyto_storage)
        },
        fill_output_div: function (_) {
            // Initialize output box
            output_div = document.getElementById('bottom-controls')
            output_div.innerHTML = `
<div id='effects-output'>\
<strong>Effects:</strong>\
<pre id="outer_edges_output">Mouse over any node to get its relationships</pre>\
</div>\
<div id='causes-output'>\
<strong>Caused by:</strong>\
<pre id="inner_edges_output">Mouse over any node to get its relationships</pre>\
</div>\
<h1 id = "big-node-name"></h1>`
            document.getElementById('right-controls').innerHTML =
                `
<div id = "parent-object-output"><pre id ="object-output" title="Double click to go to WebProtege">Click on any node to view its JSON properties</pre></div> 
<select id = "filter-select">
    <option value="" disabled selected hidden>Select filter</option>
    <option value="no_long_desc">Personal value nodes/solutions without long descriptions</option> 
    <option value="no_sources">Personal value nodes/edges without sources</option> 
    <option value="personal_values">All personal values</option> 
    <option value="none">None</option>
</select>
`

            document.getElementById('object-output').addEventListener('dblclick', (event) => {
                const formattted_iri = event.target.getAttribute("web_protege_iri").slice(24)
                window.open(`
            https://webprotege.stanford.edu/#projects/de9e0a93-66a8-40c6-bce8-b972847d362f/edit/Individuals?selection=NamedIndividual(%3Chttp://webprotege.stanford.edu/${formattted_iri}%3E)`)
            })

            document.getElementById('filter-select').addEventListener('change', (event) => {
                window.filter_exported.apply_filter(event.target.value)
            })

        }
    }
});



