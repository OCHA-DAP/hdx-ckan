"use strict";

ckan.module('hdx_resource_grouping', function ($, _) {
  return {
    initialize: function () {
      const resourceEls = $('.resource-list li.resource-item');
      const selectedResourceGroupingLabel = $('#resource-grouping-link-title .selected-grouping-title');
      const processResourceList = function (groupingId) {
        resourceEls.each( (idx, resourceEl) => {
          if ($(resourceEl).data('groupingId') === groupingId) {
            $(resourceEl).show();
          } else {
            $(resourceEl).hide();
          }
        });
      };
      const clickCallback = function() {
        const groupingId = $(this).data('groupingId');
        selectedResourceGroupingLabel.text($(this).text());
        processResourceList(groupingId);
      }

      processResourceList($(this.el.find('li li')[0]).data('groupingId'));
      this.el.find('li li').click(clickCallback);
    },
    options : {
      default_grouping_id: null,
    }
  };
});
