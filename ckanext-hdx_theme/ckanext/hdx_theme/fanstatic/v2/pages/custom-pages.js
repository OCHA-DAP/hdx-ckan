(function () {
  'use strict';

  var HdxDataTable = window.DataTable;

  document.addEventListener('DOMContentLoaded', function () {
    var table = document.querySelector('.hdx-v2-custom-pages-table table.c-table');
    if (!table || !table.tBodies[0].rows.length) return;

    new HdxDataTable(table, {
      paging:       false,
      searching:    false,
      info:         false,
      lengthChange: false,
      autoWidth:    false,
      order:        [],
      columnDefs:   [{ targets: -1, orderable: false }],
      layout: {
        topStart:    null,
        topEnd:      null,
        bottomStart: null,
        bottomEnd:   null
      }
    });
  });
})();
