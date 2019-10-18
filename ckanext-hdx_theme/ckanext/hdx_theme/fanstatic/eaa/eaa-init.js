(function() {
  //fixed page menu
  var countDatasets = prepareCount();

  var openInNewWindow = $("#map").attr("data-open-new-window") === "true";
  prepareMap(countDatasets, openInNewWindow);
  // prepareCountryList(countDatasets);

  //initSortingWidget();
}).call(this);
