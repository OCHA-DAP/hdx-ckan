document.addEventListener('DOMContentLoaded', function () {
    var resourceUrl = document.getElementById('resource-url').textContent.trim();
    var previewUrl  = '/hxl/api/data-preview.json?rows=0&sheet=0&url=' + encodeURIComponent(resourceUrl);
    fetch(previewUrl)
        .then(function (r) { return r.json(); })
        .then(function (response) {
            if (!response || !response[0]) return;
            var columns = response[0].map(function (h) { return { title: h }; });
            new DataTable('#hdx-csv-table', {
                data:         response.slice(1),
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
        })
});
