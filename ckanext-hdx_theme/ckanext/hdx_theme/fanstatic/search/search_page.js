$('document').ready(function() {
    $("#search_filter_btn").css("visibility", "visible");
    $("#search_filter_btn").click(function(){
        var $this = $(this);
        var open = true;
        if ($this.hasClass("icon-close_filter_button")){
            open = false;
        }

        var $filter = $("#dataset-filter-start");
        if (open){
            $this.removeClass("icon-open_filter_button");
            $this.addClass("icon-close_filter_button");

            $filter.removeClass("list-header-min");
        } else {
            $this.removeClass("icon-close_filter_button");
            $this.addClass("icon-open_filter_button");

            $filter.addClass("list-header-min");
        }
    });
});