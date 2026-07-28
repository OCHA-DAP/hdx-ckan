var DATASTORE_FETCH_ALL_LIMIT = 32000;

document.addEventListener('DOMContentLoaded', function () {
    var resourceUrl     = document.getElementById('resource-url').textContent.trim();
    var resourceId      = document.getElementById('resource-id').textContent.trim();
    var datastoreActive = document.getElementById('datastore-active').textContent.trim() === 'true';

    if (datastoreActive) {
        loadFromDatastore(resourceId);
    } else {
        loadFromHxlProxy(resourceUrl);
    }
});

function loadFromHxlProxy(resourceUrl) {
    var previewUrl = '/hxl/api/data-preview.json?rows=0&sheet=0&url=' + encodeURIComponent(resourceUrl);
    fetch(previewUrl)
        .then(function (r) { return r.json(); })
        .then(function (response) {
            if (!response || !response[0]) return;
            var columns = response[0].map(function (h) { return { title: h }; });
            initDataTable(response.slice(1), columns);
        });
}

function loadFromDatastore(resourceId) {
    var url = '/api/3/action/datastore_search?resource_id=' + encodeURIComponent(resourceId) + '&limit=' + DATASTORE_FETCH_ALL_LIMIT;
    fetch(url, { headers: hdxUtil.net.getCsrfTokenAsObject() })
        .then(function (r) { return r.json(); })
        .then(function (response) {
            if (!response || !response.success || !response.result) return;
            var fields = response.result.fields.filter(function (f) { return f.id !== '_id'; });
            var columns = fields.map(function (f) { return { data: f.id, title: f.id }; });
            initDataTable(response.result.records, columns);
        });
}

function initDataTable(data, columns) {
    new DataTable('#hdx-csv-table', {
        data:         data,
        columns:      columns,
        pageLength:   10,
        autoWidth:    false,
        searching:    false,
        lengthChange: false,
        info:         false,
        select:       false,
        layout: {
            topStart:    null,
            topEnd:      null,
            bottomStart: { paging: { type: 'simple_numbers' } },
            bottomEnd:   null
        },
        language: { paginate: { previous: '‹', next: '›' } }
    });
}
