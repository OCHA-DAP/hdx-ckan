(function() {
  const SEARCH_BASE_SELECTOR='.hdx-wrapper';
  function _resetSearch($panel) {
    $panel.find("span.highlight").closest(".faq-panel-collapse").collapse('hide');
    $panel.unhighlight();
    $("#search-no-results").hide();
    $("#search-results").hide();
    $("#hdx-faq-sidebar").removeClass('ongoing');
  }

  function scrollIntoViewAdjusted(element){
    let headerOffset = 70;
    let elementPosition = element.getBoundingClientRect().top;
    let offsetPosition = elementPosition + window.pageYOffset - headerOffset;
    window.scrollTo({
      top: offsetPosition,
      behavior: "smooth"
    });
  }

  function updateSearch() {
    const text = $(this).val();
    console.log(text);
    const $panel = $(SEARCH_BASE_SELECTOR);
    _resetSearch($panel);
    $panel.unhighlight();
    $panel.highlight(text);
    const $results = $panel.find("span.highlight");
    if ($results.length > 0) {
      $("#faq-search-current").text('0');
      $("#faq-search-total").text($results.length);
      $("#search-results").show();
      $("#hdx-faq-sidebar").addClass('ongoing');
      setTimeout(() => {
        $results.closest(".faq-panel-collapse").collapse('show');
        // $results.first().get(0).scrollIntoView({ behavior: 'smooth' });
        scrollIntoViewAdjusted($results.first().get(0));
        incrementCurrentResult(1)();
      }, 150); //wait for hide collapse animation to fire for sections that might get re-shown :)
    } else {
      $("#search-no-results").show();
    }
  }

  function incrementCurrentResult(val) {
    return () => {
      $("span.highlight.current").removeClass("current");
      let result = parseInt($("#faq-search-current").text());
      let total = parseInt($("#faq-search-total").text());
      result += val;
      result = (result < 1 ? total : (result > total ? 1 : result));
      $("#faq-search-current").text(result);
      const current = $(SEARCH_BASE_SELECTOR).find("span.highlight").get(result - 1);
      $(current).addClass("current");
      setTimeout(() => scrollIntoViewAdjusted(current), 350); //wait for the collapse animation to finish :)
      return false;
    }
  }

  $(document).ready(function(){
    $("#faq-search").change(updateSearch);
    $("#faq-search-prev").click(incrementCurrentResult(-1));
    $("#faq-search-next").click(incrementCurrentResult(1));
  });
}).call(this);
