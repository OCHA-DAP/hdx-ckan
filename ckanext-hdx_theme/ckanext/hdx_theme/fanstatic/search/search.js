$('document').ready(function(){
    var index = lunr(function () {
        this.field('title', {boost: 10});
        this.field('event', {boost: 1000}); //Little hack to boost the scores of event pages
        this.field('url');
        this.ref('id')
    });

    for(i=0; i<feature_index.length; i++){//This is the part where Lunr is actually not too bright
        feature_index[i]['id'] = i;
        if(feature_index[i]['type'] == 'event'){
            feature_index[i]['event'] = feature_index[i]['title'];
        }else{
            feature_index[i]['event'] = '';
        }
        index.add(feature_index[i])
    }

    results = index.search($('#input-search input').attr('value'));
    if(results.length > 0){//Don't show if we don't have any good matches
        var html = "You might also like:";
        var limit = results.length > 5 ? 5 : results.length;
        for(i=0; i<limit; i++){
            html += ' <a href="'+feature_index[results[i]['ref']]['url']+'">'+feature_index[results[i]['ref']]['title']+'</a> '+feature_index[results[i]['ref']]['type']+' page';
            if(i<limit-1){
                html +=',';
            }
        }
        $('#search-recs').html(html);
    }

    const onSearch = function(){
        var q = $(this).val();
        var prevSearch = JSON.parse($("#previous-searches").text());

        var search = index.search(q);
        var $results = $(this).parents("form").find('.search-ahead');
        var html = "";
        html += "<ul>";

        if (prevSearch != null && prevSearch.length > 0){
            $(prevSearch).each(function(idx, el){
                html += '<li data-href="'+el.url+'"><div class="ahead-link"><i class="icon icon-previoussearches"></i>'+process_title(el.text, q)+'</div><div class="ahead-type">'+el.count+' new results</div></li>';
            });
        }

        if(search.length >0){
            var limit = search.length > 5 ? 5 : search.length;
            for(i=0; i<limit; i++){
                html += '<li data-href="'+feature_index[search[i]['ref']]['url']+'"><div class="ahead-link"><i class="empty"></i>'+process_title(feature_index[search[i]['ref']]['title'], q)+'</div><div class="ahead-type">'+feature_index[search[i]['ref']]['type']+' page</div></li>';

            }
        }

        html +=
            '<li data-href="/search?q='+ q +'"><div class="ahead-link">' +
            '<i class="icon icon-search"></i>Search <b>'+ q +'</b> in <b>datasets</b>' +
            '</div></li>' +
            '<li data-href="/showcase?q='+ q +'"><div class="ahead-link">' +
            '<i class="icon icon-dataviz"></i>Search <b>'+ q +'</b> in <b>dataviz</b>' +
            '</div></li>';
        html += '</ul>';
        $results.html(html);
        $results.show();
    };

    // $('#q, #q2').keyup(onSearch);

    $('#q').keyup(onSearch);
    $('#q').click(onSearch);

    $('.search-ahead').on('mousedown', "li", function(){
        window.location = $(this).attr('data-href');
    });

    $('#q, #q2').blur(function(){
        var $results = $(this).parents("form").find('.search-ahead');
        $results.html('');
        $results.hide();
    });
});

function process_title(title, q){
    if(title.length>40){
        title = title.substring(0,40);
        title = title+'...'
    }
    var re = new RegExp(q, "gi");
    title = title.replace(re, '<strong>$&</strong>');
    return title
}