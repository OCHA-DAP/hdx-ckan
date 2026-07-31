/**
 * resource-page.js
 *
 * Behaviour for the v2 resource page:
 *   - Data dictionary section (AJAX-loaded via datastore_info, builds a c-table)
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initDataDictionary();
    });

    var DATA_DICTIONARY_COLUMNS = [
        { header: 'Title', get: function (field) { return (field.info && field.info.label) || field.id; } },
        { header: 'Column name', get: function (field) { return field.id; } },
        { header: 'Data type', get: function (field) { return field.type; } },
        { header: 'Description', get: function (field) { return (field.info && field.info.notes) || ''; } }
    ];

    function initDataDictionary() {
        var section = document.querySelector('[data-module="data-dictionary"]');
        if (!section) return;

        var target = section.querySelector('.hdx-v2-data-dictionary-container');
        var resourceId = section.dataset.resourceId;
        var url = '/api/3/action/datastore_info?id=' + encodeURIComponent(resourceId);

        fetch(url, { headers: hdxUtil.net.getCsrfTokenAsObject() })
            .then(function (r) { return r.json(); })
            .then(function (response) {
                var fields = (response.success && response.result && response.result.fields) || [];
                fields = fields.filter(function (field) { return field.id !== '_id'; });
                if (!fields.length) return;
                target.appendChild(buildDataDictionaryTable(fields));
            });
    }

    function buildDataDictionaryTable(fields) {
        var container = document.createElement('div');
        container.className = 'c-table-container';

        var scroll = document.createElement('div');
        scroll.className = 'c-table__scroll';
        container.appendChild(scroll);

        var table = document.createElement('table');
        table.className = 'c-table';
        scroll.appendChild(table);

        var thead = document.createElement('thead');
        var headRow = document.createElement('tr');
        DATA_DICTIONARY_COLUMNS.forEach(function (column) {
            var th = document.createElement('th');
            th.textContent = column.header;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        var tbody = document.createElement('tbody');
        fields.forEach(function (field) {
            var row = document.createElement('tr');
            DATA_DICTIONARY_COLUMNS.forEach(function (column) {
                var td = document.createElement('td');
                td.textContent = column.get(field);
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        return container;
    }
})();
