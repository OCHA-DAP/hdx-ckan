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


  $(window).scroll(scroll_to_menu);
}).call(this);