(function() {
  //fixed page menu
  $(window).scroll(browse_by_menu);
  browse_by_menu();

  var countDatasets = prepareCount();
  prepareMap(countDatasets);
  prepareCountryList(countDatasets);

  //initSortingWidget();
}).call(this);
