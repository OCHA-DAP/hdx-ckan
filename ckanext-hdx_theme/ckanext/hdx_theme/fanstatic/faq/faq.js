(function() {
    function scroll_to_menu() {
        var window_top = $(window).scrollTop();
        var window_bottom = window_top + $(window).height();
        var lowestAfterWindow = null;
        var highestBeforeWindow = null;
        var nextActiveEl = null;
        var sections = $('.section-flag');
        for (var i=0; i<sections.length; i++ ) {
            var el = $(sections[i]);
            var section_top = el.offset().top;

            var isHighestBeforeWindow = false, isLowestAfterWindowAndVisible= false;
            isHighestBeforeWindow = window_top > section_top
                && (!highestBeforeWindow || section_top > highestBeforeWindow);
            if ( isHighestBeforeWindow )
                highestBeforeWindow = section_top;
            else {
                var isVisible = window_top < section_top && window_bottom > section_top;
                isLowestAfterWindowAndVisible = isVisible && (!lowestAfterWindow || section_top < lowestAfterWindow);
                if ( isLowestAfterWindowAndVisible )
                    lowestAfterWindow = section_top;
            }

            if ( isHighestBeforeWindow || isLowestAfterWindowAndVisible ) {
                nextActiveEl = el;
            }
        }
        if (nextActiveEl) {
            $('.hdx-faq-sidebar li a').removeClass('active');
            var menuItemId = nextActiveEl.attr('id').replace('body-', 'menu-');
            var targetEl = $('#' + menuItemId);
            targetEl.addClass('active');
        }
    }

    function sticky_menu() {
        var window_top = $(window).scrollTop();
        var marker_top = $('#hdx-faq-sidebar-wrapper').offset().top;
        if (window_top + 10 > marker_top) {
            $('#hdx-faq-sidebar').addClass('sticky');
        }
        else {
            $('#hdx-faq-sidebar').removeClass('sticky');
        }
    }

    function add_menu_click_events() {

        function scrollTo() {
            var targetId = $(this).attr('href');

            hdxUtil.ui.scrollTo(targetId);
            return false;
        }

        var menuAnchors = $('.hdx-faq-sidebar li a');
        for (var i=0; i<menuAnchors.length; i++) {
            aEl = $(menuAnchors[i]);
            aEl.click(scrollTo);
        }

    }

    $(window).scroll(scroll_to_menu);
    $(window).scroll(sticky_menu);

    $('.hdx-panel-group .panel-heading').click(
        function (e) {
            if ( e.target.tagName.toLowerCase() != 'a') {
                //var collapsible = $(this).siblings()[0];
                //$(collapsible).collapse('toggle');
                $(this).find('h4 a')[0].click();
            }
        }
    );

    scroll_to_menu();
    sticky_menu();
    add_menu_click_events();

    $(document).ready(function(){
        if (location.hash) {
            if (location.hash.endsWith("-a")) {
                var new_hash = location.hash.substring(0, location.hash.length - 2) + "-q";
                $(new_hash + " ~ .panel-collapse").collapse('show');
                hdxUtil.ui.scrollTo(new_hash, 1);

            } else {
                $(location.hash + " ~ .panel-collapse").collapse('show');
            }
        }


    });

}).call(this);
