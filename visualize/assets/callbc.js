console.log("loaded")

var cyto_storage, node_positions_cache = {};
const personal_value_selector = "increase in physical violence"
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        update_storage_globals: function ( _cyto_storage) {
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
<pre id ="object_output"></pre>\
</div>
`
        }
    }
});



