ckan.module('hdx-onboarding-flow', function ($) {
  return {
    initialize: function () {
      this.el.on('click', this.onClick);
    },
    onClick: function () {
      var startPageType = $(this).data('start-page-type');
      var startPageAdditionalParams = $(this).data('start-page-additional-params');
      var valuePropositionPage = $(this).data('value-proposition-page');

      var updateData = {};
      if (startPageType) {
        updateData.start_page = {
          'page_type': startPageType || '',
          'additional_params': startPageAdditionalParams || {}
        };
      }
      if (valuePropositionPage) {
        updateData.value_proposition_page = valuePropositionPage;
      }

      hdxUtil.net.updateOnboardingFlowData(updateData);
    }
  };
});
