console.log("loaded")
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        mouse_over_func: function (mouseover_node_data, node_data, edge_data) {
            if (mouseover_node_data == undefined) {
                // Dash by default runs callbacks with null parameters at load time. We don't want to do anything in this case.
                return
            }

            let all_edges = edge_data[mouseover_node_data['id']]
            let outer_edges = []
            let inner_edges = []

            for (const edge in all_edges) {
                // If we want to modify the text in any way. e.g. bold, italics, underline.
                let text_modifier_begin = "", text_modifier_end = ""

                // Solutions should be italicized.
                if ('risk solution' in node_data[edge]) {
                    text_modifier_begin = "<em>"
                    text_modifier_end = "</em>"
                }
                if (all_edges[edge].direction == "reverse") {
                    inner_edges.push(text_modifier_begin + edge + text_modifier_end)
                } else if (all_edges[edge].direction == "forward") {
                    outer_edges.push(text_modifier_begin + edge + text_modifier_end)
                }
            }

            document.getElementById('outer_edges_output').innerHTML = outer_edges.join('.\n\n')
            document.getElementById('inner_edges_output').innerHTML = inner_edges.join('.\n\n')

        },
        fill_output_div: function (dummy) {
            console.log("onload function called")
            // Initialize output box
            output_div = document.getElementById('output')
            output_div.className = "output_parent"
            output_div.innerHTML = `
<div id='outer_edges'> 
<strong>Causes:</strong>
<p id="outer_edges_output" class="output_child">Mouse over any node to get its relationships</p>
</div>
<div id='inner_edges'> 
<strong>Caused by:</strong>
<p id="inner_edges_output" class="output_child">Mouse over any node to get its relationships</p>
</div>
`
        }
    }
});

