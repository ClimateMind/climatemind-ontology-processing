console.log("loaded")

var cyto_storage, node_positions_cache = {};
const personal_value_selector = "increase in physical violence"
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
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
<strong>Causes:</strong>\
<p id="outer_edges_output">Mouse over any node to get its relationships</p>\
</div>\
<div id='inner_edges' class = "output_child">\
<strong>Caused by:</strong>\
<p id="inner_edges_output">Mouse over any node to get its relationships</p>\
</div>\
<div id='solutions_box' class = "output_child">\
<strong>Solutions:</strong>\
<p id="solutions_output">Mouse over any node to get its relationships</p>\
</div>\
<div id='data_box' class = "output_child">\
<pre id ="object_output" title="Double click to go to WebProtege">Click on any node to view its JSON properties</pre>\
</div>

<div class = "output_child" id="filter-div">
<textarea type="text" id="filter-code"></textarea>
<pre id="errors-output">Enter any code that evaluates to a truthy value or falsey value to filter. The "node" object allows you to access node properties. Any error evaluates to false.
Example: node["properties"]["dc_source"]
Example: node["direct classes"].includes("adaptation")
</pre>
</div>
`

            document.getElementById('object_output').addEventListener('dblclick', (event) => {
                window.open(`https://webprotege.stanford.edu/#projects/de9e0a93-66a8-40c6-bce8-b972847d362f/edit/Individuals?selection=NamedIndividual(%3Chttp://webprotege.stanford.edu/${event.target.getAttribute("web_protege_iri")}%3E)`)
            })
        }
    }
});



