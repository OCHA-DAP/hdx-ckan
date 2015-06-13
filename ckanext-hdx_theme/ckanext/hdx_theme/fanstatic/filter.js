$(document).ready(function(){
//	if(localStorage.getItem('hdx_filter') == 1){
//	$("#search_bar_content").slideDown(300, function() {
//	return $("#search_filter_btn span").text('-');
//	});
//	}
	var searchEl = $("#search_bar_content");
	var showFilters = searchEl.attr("data-module-show"); 
	if ( showFilters && 'true' == showFilters.toLowerCase() ) {
		searchEl.slideDown(300, function() {
			return $("#search_filter_btn span").text('-');
		});
	}
	$('#filter_dropdown').on('change','select', function(){
		window.location = $(this).val();
	});

	$("#search_filter_btn").click(function() {

        var filter_btn = $("#search_filter_btn");

		if (filter_btn.hasClass("icon-open_filter_button")) {
			return $("#search_bar_content").slideDown(300, function() {
                filter_btn.removeClass("icon-open_filter_button");
                filter_btn.addClass("icon-close_filter_button");
				return filter_btn;
			});
		} else {
			return $("#search_bar_content").slideUp(300, function() {
                filter_btn.removeClass("icon-close_filter_button");
                filter_btn.addClass("icon-open_filter_button");
				return filter_btn;
			});
		}
	});
});
