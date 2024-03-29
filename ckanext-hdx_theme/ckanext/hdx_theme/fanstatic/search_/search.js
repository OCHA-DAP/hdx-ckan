/*jshint esversion: 6 */
$('document').ready(function(){
  var index = new MiniSearch({
    fields: ['title', 'title_nf', 'extra_terms', 'event', 'url'],
    storeFields: ['title', 'extra_terms', 'event', 'url']
  });

  for(let i=0; i<feature_index.length; i++){
    let fi = feature_index[i];
    fi['id'] = i;
    fi['title_nf'] = toNormalForm(fi['title']); //adding the normal form in the index as well
    if(fi['type'] === 'event'){
      fi['event'] = fi['extra_terms'];
    }else{
      fi['event'] = '';
    }
  }
  index.addAll(feature_index);

  var performSearchQuery = function(query) {
    const termList = toNormalForm(query.split(' ').filter(item => item.length));
    const modifiedQ = termList.map(term => term.length > 0 ? '' + term : term).join(' ');
    let results = [];
    if (modifiedQ.length > 0) {
      results = index.search(modifiedQ, {
        prefix: true,
        boost: {
          title: 10,
          event: 1000 //Little hack to boost the scores of event pages
        }
      });
    }

    return {
      'q': query,
      'termList': termList,
      'modifiedQ': modifiedQ,
      'results': results
    };
  };


    var searchInfo = performSearchQuery($('#headerSearch').attr('value') || '');
    var results = searchInfo.results;
    if(results.length > 0){//Don't show if we don't have any good matches
        var html = "You might also like:";
        var limit = results.length > 5 ? 5 : results.length;
        for(let i=0; i<limit; i++){
            html += ' <a href="'+feature_index[results[i]['id']]['url']+'">'+feature_index[results[i]['id']]['title']+'</a> '+feature_index[results[i]['id']]['type']+' page';
            if(i<limit-1){
                html +=',';
            }
        }
        $('#search-recs').html(html).removeClass('d-none');
    }

    // move search-ahead element in parent container to fix absolute positioning
    if(window.matchMedia('(max-width:767px)').matches) { // 767 = @cut-point-tablet
      $('.navbar-header .search-ahead').appendTo('.navbar-header');
    }
    // calculate the top property value for search dropdown on responsive devices
    calculate_search_top_positioning();

    var onSearch = function(){
        let value = toNormalForm(hdxUtil.text.sanitize($(this).val()));
        var searchInfo = performSearchQuery(value);

        var prevSearch = JSON.parse($("#previous-searches").text());

        // console.log('MODIFIED QUERY IS: ' + searchInfo.modifiedQ);
        // console.log('QUERY IS: ' + searchInfo.q);
        // console.log('results are: ' + searchInfo.results);
        // console.log('________________________' );
        var search = searchInfo.results;
        var $results = $(this).parents(".navbar-header").find('.search-ahead');
        var html = "";
        html += "<ul>";

        // (re)calculate the top property value because .header-message appears after a while on staging/dev
        calculate_search_top_positioning();

        if (prevSearch != null && prevSearch.length > 0){
            $(prevSearch).each(function(idx, el){
                const prevSearchQuery = hdxUtil.text.sanitize(el.text);
                html += '<li data-href="'+el.url+'" data-toggle="tooltip" title="'+ prevSearchQuery +'"><div class="ahead-link"><i class="icon icon-previoussearches"></i>'+process_title(prevSearchQuery, searchInfo.termList)+'</div><div class="ahead-type">'+el.count+' new results</div></li>';
            });
        }

        if(search.length >0){
            var limit = search.length > 5 ? 5 : search.length;
            for(let i=0; i<limit; i++){
                const featureTitle = hdxUtil.text.sanitize(feature_index[search[i].id].title);
                html += '<li data-search-term="'+searchInfo.q+'" data-search-type="'+feature_index[search[i]['id']]['type']+
                    '" data-href="'+feature_index[search[i]['id']]['url']+'" ' +
                    'data-toggle="tooltip" title="'+ featureTitle +'"><div class="ahead-link"><i class="empty"></i>'+
                    process_title(featureTitle, searchInfo.termList)+'</div><div class="ahead-type">'+feature_index[search[i]['id']]['type']+' page</div></li>';

            }
        }
        const searchQuery = hdxUtil.text.sanitize(searchInfo.q);
        html +=
            '<li data-href="/search?q='+ searchQuery +'&ext_search_source=main-nav"><div class="ahead-link">' +
            '<i class="icon icon-search"></i>Search <b>'+ searchQuery +'</b> in <b>datasets</b>' +
            '</div></li>' +
            '<li data-href="/showcase?q='+ searchQuery +'&ext_search_source=main-nav"><div class="ahead-link">' +
            '<i class="icon icon-dataviz"></i>Search <b>'+ searchQuery +'</b> in <b>dataviz</b>' +
            '</div></li>';
        html += '</ul>';
        $results.html(html);
        $results.find("li").tooltip({
            placement: 'top',
    	    trigger: 'hover',
            delay: {
                show: 700,
                hide: 100
            }
        });
        $results.show();
    };

    // $('#q, #q2').keyup(onSearch);

    $('#q, #qMobile').keyup(onSearch);
    $('#q, #qMobile').click(onSearch);

    $('.search-ahead').on('mousedown', "li", function(){
        var searchTerm = $(this).attr('data-search-term');
        var resultType = $(this).attr('data-search-type');
        var dataHref = $(this).attr('data-href');
        console.log("Clicked on " + resultType + ". Search term is " + searchTerm);
        var followLink = function () {
            window.location = dataHref;
        };
        if (searchTerm && resultType) {
            hdxUtil.analytics.sendTopBarSearchEvents(searchTerm, resultType).then(followLink, followLink);
        }
        else {
            followLink();
        }
    });

    $('#q, #q2, #qMobile').blur(function(){
        var $results = $(this).parents(".navbar-header").find('.search-ahead');
        // $results.html('');
        $results.hide();
    });

  $('.show-more-dates, .hide-more-dates').on('click', function(e) {
    e.preventDefault();
    var parent = $(this).closest('.dataset-dates');
    $('.show-more-dates, .hide-more-dates', parent).toggleClass('d-none');
    $('.more-dates', parent).toggleClass('d-none');
  });
});

function process_title(title, termList){
  if (termList && termList.length > 0) {
    terms = termList.join('|');
    var re = new RegExp(terms, "gi");
    title = title.replace(re, '<strong>$&</strong>');
  }
  return title;
}

// .header-message is overwritten by nginx on staging/dev
function calculate_search_top_positioning() {
  if(window.matchMedia('(max-width:767px)').matches) { // 767 = @cut-point-tablet
    let top_value = $('.global-header').outerHeight() + $('.hdx-header').outerHeight();
    $('.navbar-header .search-ahead').css('top',  top_value + 'px');
  }
}
