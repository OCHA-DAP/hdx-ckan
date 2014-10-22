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
//		if(localStorage.getItem('hdx_filter')==1){
//		localStorage.setItem('hdx_filter', 0);
//		}else{
//		localStorage.setItem('hdx_filter', 1);
//		}
		if ($("#search_filter_btn span").text() === '+') {
			return $("#search_bar_content").slideDown(300, function() {
				return $("#search_filter_btn span").text('-');
			});
		} else {
			return $("#search_bar_content").slideUp(300, function() {
				return $("#search_filter_btn span").text('+');
			});
		}
	});
});
