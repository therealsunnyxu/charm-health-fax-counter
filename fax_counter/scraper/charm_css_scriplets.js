function get_row_data(indices, x_path) {
    snapshot = document.evaluate(x_path, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    data = [];
    for (let i = 0, length = indices.length; i < length; ++i) {
        curr_element = snapshot.snapshotItem(indices[i]);
        text = '';
        if (curr_element) {
            text = curr_element.textContent;
        }
        data.push(text);
    }
    return data;
}

function get_row_ids(x_path) {
    var snapshot = document.evaluate(x_path, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    var ids = [];
    for (let i = 0, length = snapshot.snapshotLength; i < length; ++i) {
        ids.push(snapshot.snapshotItem(i).id);
    }
    return ids;
}