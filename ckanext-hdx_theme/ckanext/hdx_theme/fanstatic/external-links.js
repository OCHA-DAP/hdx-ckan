//$(document).ready(function(){
//    var base = '{{ app_globals.site_url }}';
//    if(base.lastIndexOf('https://')){//Sometimes the site_url config doesn't factor in HTTPSs
//      base = base.slice(7);
//    }else if(base.lastIndexOf('http://')){
//      base = base.slice(6);
//    }
//    $('a').each(function(){
//      if (this.href.search(base) == -1 && this.href.search('http://docs.hdx.rwlabs.org') == -1){
//        this.target="_blank";
//      }
//    });
//});
