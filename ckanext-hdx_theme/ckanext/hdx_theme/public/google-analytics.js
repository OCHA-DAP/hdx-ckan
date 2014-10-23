(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-48221887-3', 'auto');
ga('send', 'pageview');

$('.ga-download').on('click', function(){
      ga('send','event','a','download');
});

$('.ga-share').on('click', function(){
      ga('send','event','a','share');
});

$('.ga-preview').on('click', function(){
      ga('send','event','a','preview');
});