/**
 * resource-page.js
 *
 * Behaviour for the v2 resource page:
 *   - Data dictionary section (AJAX-loaded via datastore_info, paginated
 *     with DataTables — same pattern as the Data Explorer/CSV preview)
 */


(function () {
    'use strict';

    var HdxDataTable = window.DataTable;

    document.addEventListener('DOMContentLoaded', function () {
        initDataDictionary();
        initApiAccessRescroll();
        initResourcePreviewSpinner();
    });

    function scrollToApiAccessIfActive() {
        if (location.hash !== '#api-access') return;
        setTimeout(function () {
            var target = document.getElementById('api-access');
            if (target) window.hdxSmoothScrollTo(target);
        }, 100);
    }

    function initApiAccessRescroll() {
        var iframe = document.querySelector('#resource-preview iframe');
        if (iframe) iframe.addEventListener('load', scrollToApiAccessIfActive);
    }

    // The resource-view snippet either renders content synchronously
    // (no spinner needed) or embeds an iframe (data-viewer module) whose
    // load can take a while — keep the spinner up until that fires.
    function initResourcePreviewSpinner() {
        var section = document.getElementById('resource-preview');
        if (!section) return;

        var spinner = section.querySelector('.c-spinner');
        if (!spinner) return;

        var iframe = section.querySelector('iframe');
        if (!iframe) {
            spinner.hidden = true;
            return;
        }

        iframe.addEventListener('load', function () { spinner.hidden = true; });
    }

    var DATA_DICTIONARY_COLUMNS = [
        { key: 'title', header: 'Title', get: function (field) { return (field.info && field.info.label) || field.id; } },
        { key: 'column_name', header: 'Column name', get: function (field) { return field.id; } },
        { key: 'data_type', header: 'Data type', get: function (field) { return field.type; } },
        { key: 'description', header: 'Description', get: function (field) { return (field.info && field.info.notes) || ''; } }
    ];

    // Rows/page is fixed so the table's footprint never grows past a single
    // page's height, regardless of how many fields a resource has — this
    // keeps the page from shifting under an anchor scroll (e.g. the "Access
    // via API" button) that lands lower on the page while this section is
    // still loading.
    var DATA_DICTIONARY_PAGE_LENGTH = 10;

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
                buildDataDictionaryTable(target, fields);
                scrollToApiAccessIfActive();
            })
            .finally(function () {
                var spinner = target.querySelector('.c-spinner');
                if (spinner) spinner.remove();
            });
    }

    function buildDataDictionaryTable(target, fields) {
        var rows = fields.map(function (field) {
            var row = {};
            DATA_DICTIONARY_COLUMNS.forEach(function (column) {
                row[column.key] = column.get(field);
            });
            return row;
        });
        var columns = DATA_DICTIONARY_COLUMNS.map(function (column) {
            return { data: column.key, title: column.header };
        });

        var table = document.createElement('table');
        table.id = 'hdx-data-dictionary-table';
        table.className = 'c-table';
        target.appendChild(table);

        new HdxDataTable(table, {
            data:         rows,
            columns:      columns,
            pageLength:   DATA_DICTIONARY_PAGE_LENGTH,
            autoWidth:    false,
            searching:    false,
            lengthChange: false,
            info:         false,
            select:       false,
            ordering:     false,
            layout: {
                topStart:    null,
                topEnd:      null,
                bottomStart: { paging: { type: 'simple_numbers' } },
                bottomEnd:   null
            },
            language: { paginate: { previous: '‹', next: '›' } }
        });
    }
})();
