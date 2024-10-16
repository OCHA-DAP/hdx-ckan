$(document).ready(function () {
  var IFRAME_ID = 'hapi-availability-iframe';
  var IFRAME_MIN_HEIGHT = 866;
  var $iframe = $('#' + IFRAME_ID);

  $iframe.on('load', function () {
    delayExecution(3000).then(function () {
      adjustIframeHeight($iframe);
    });
  });

  function delayExecution(milliseconds) {
    return $.Deferred(function (defer) {
      setTimeout(function () {
        defer.resolve();
      }, milliseconds);
    }).promise();
  }

  function adjustIframeHeight($iframe) {
    var frameDocument = $iframe[0].contentWindow.document;
    var bodyHeight = $(frameDocument).find('body').outerHeight() + 50 || 0;
    if (bodyHeight >= IFRAME_MIN_HEIGHT) {
      $iframe.attr('height', bodyHeight);
    }
  }
});
