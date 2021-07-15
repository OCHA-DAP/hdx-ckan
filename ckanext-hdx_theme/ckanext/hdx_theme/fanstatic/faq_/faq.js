(function() {

    function get_analytics_data(el) {
        return {
            destinationUrl: $(el).attr('href'),
            destinationLabel: $(el).text().trim()
        };

    }

    function send_analytic_event(collapsePanelEl) {
        var linkEl = $(collapsePanelEl.parentNode).find('.faq-question-link');
        if (linkEl && linkEl.length === 1) {
            var analyticsData = get_analytics_data(linkEl);
            hdxUtil.analytics.sendFaqClickEvent(analyticsData);
        }
        else {
            console.error('Exactly one <a> tag needs to exist in the parent panel');
        }
    }

    $('.faq-panel-collapse').on('show.bs.collapse', function(event){
      $(event.target).find('iframe[load-src]').each(function() {
        $(this).attr('src', $(this).attr('load-src'));
      })
    });
    $('.faq-panel-collapse').on('shown.bs.collapse', function(event){
        send_analytic_event(event.target);

    });

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

    function showPresentationModal(id){
        var modal = $(id);
        var iframe = $(id + ' iframe');
        iframe.attr('src', '');
        modal.modal('show');
        iframe.attr('src', iframe.attr('load-src'));
        iframe.focus();
    }

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

        // $("#learn-add-viz-dataset-link").click(function () {
        //   showPresentationModal("#learn-add-viz-dataset");
        // });

        var clickCallbackCreator = function (sufix) {
          var callback = function () {
            var strDiv = "#faq-google-embed-" + sufix;
            showPresentationModal(strDiv);
          };
          return callback;
        };

        var nrEmbeds = $('.faq-google-embed-marker');
        var faqEmbedPrefix = "faq-google-embed-link-";
        for (var i = 0; i < nrEmbeds.length; i++) {
          var embedLinkEl = nrEmbeds[i];
          var embedLinkId = $(embedLinkEl).attr("id");
          var embedLinkSufix = embedLinkId.substr(faqEmbedPrefix.length);
          console.log(embedLinkSufix);
          $(embedLinkEl).click(clickCallbackCreator(embedLinkSufix));

      }


    });

}).call(this);
