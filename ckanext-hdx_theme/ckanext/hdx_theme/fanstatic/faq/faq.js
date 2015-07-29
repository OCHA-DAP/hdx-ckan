(function() {
    function scroll_to_menu() {
        var window_top = $(window).scrollTop();
        var lowest = null;
        var highestEl = null;
        var sections = $('.section-flag');
        for (var i=0; i<sections.length; i++ ) {
            var el = $(sections[i]);
            $('#menu-' + el.attr('id')).removeClass('active');
            var section_top = el.offset().top;
            if ( (!lowest || section_top < lowest) && window_top < section_top  ) {
                lowest = section_top;
                highestEl = el;
            }
        }
        if (highestEl) {
            var targetEl = $('#menu-' + highestEl.attr('id'));
            targetEl.addClass('active');
        }
    }

    function sticky_menu() {
        var window_top = $(window).scrollTop();
        var marker_top = $('#hdx-faq-sidebar-wrapper').offset().top;
        if (window_top > marker_top) {
            $('#hdx-faq-sidebar').addClass('sticky');
        }
        else {
            $('#hdx-faq-sidebar').removeClass('sticky');
        }
    }

    function add_menu_click_events() {

        function scrollTo() {

            $('html, body').animate({
                scrollTop: $(this).offset().top - 40
            }, 700);
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
    sticky_menu();
}).call(this);