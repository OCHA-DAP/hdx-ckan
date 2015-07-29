$('document').ready(function(){
	var index = lunr(function () {
    this.field('title', {boost: 10})
    this.field('url')
    this.ref('id')
  })
	for(i=0; i<feature_index.length; i++){//This is the part where Lunr is actually not too bright
		feature_index[i]['id'] = i;
		index.add(feature_index[i])
	}

	results = index.search($('#terms').attr('value'));
	if(results.length > 0){//Don't show if we don't have any good matches
		var html = "You might also like:"
		var limit = results.length > 4 ? 4 : results.length;
		for(i=0; i<limit; i++){
			html += ' <a href="'+feature_index[results[i]['ref']]['url']+'">'+feature_index[results[i]['ref']]['title']+'</a> '+feature_index[results[i]['ref']]['type']+' page';
			if(i<limit-1){
				html +=',';
			}
		}
		$('#search-recs').html(html);
	}

});