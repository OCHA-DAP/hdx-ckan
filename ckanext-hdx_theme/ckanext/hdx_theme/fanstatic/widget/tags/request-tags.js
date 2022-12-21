function showTagRequestWidget(id) {

  $(id).show();

  function _tagRequestTriggerInputDataClass($this) {
    if ($this.val() === '')
      $this.removeClass('input-content');
    else
      $this.addClass('input-content');
  }

  $(id).find('input[type="password"], input[type="text"], textarea').each(
    function (idx, el) {
      _tagRequestTriggerInputDataClass($(el));
    }
  );

  $(id).find('input[type="password"], input[type="text"], textarea').change(
    function () {
      var $this = $(this);
      _tagRequestTriggerInputDataClass($this);
    }
  );
  $(id).find('input[type="password"], input[type="text"], textarea').on('keyup',
    function () {
      var $this = $(this);
      _tagRequestTriggerInputDataClass($this);
    }
  );

  return false;
}

$(document).ready(function () {
  requestTagsOnSubmit = function () {
    $this = $('#request-tags-form');
    $fields = $this.find('input', 'select', 'textarea');
    $iframe = $($('.g-recaptcha').find('iframe:first'));

    $fields.removeClass('error');
    $iframe.css('border', '');

    var grecaptchaID = 0;
    var grecaptchaElementID = $('#faq-send-message-form').find('.g-recaptcha-response').prop('id');
    var gRecaptchaResponseText = 'g-recaptcha-response-';

    if (grecaptchaElementID && grecaptchaElementID.indexOf(gRecaptchaResponseText) >= 0) {
      var idNum = grecaptchaElementID.substr(grecaptchaElementID.indexOf(gRecaptchaResponseText) + gRecaptchaResponseText.length);
      if (idNum.length > 0) {
        grecaptchaID = parseInt(idNum);
      }
    } else {
      if (___grecaptcha_cfg && ___grecaptcha_cfg.count) {
        grecaptchaID = ___grecaptcha_cfg.count - 1;
      }
    }

    var postPromise = $.post('/request_tags/suggest', $this.serialize());

    $.when(postPromise).then(
      function (postData) {
        var result = postData;
        if (result.success) {
          $this[0].reset();
          closeCurrentWidget($this);
        } else {
          if (result.error.message == 'Captcha is not valid') {
            $iframe.css('border', '1px solid red');
          } else {
            if (result.error.fields) {
              $.each(result.error.fields, function (field, message) {
                $this.find('[name="' + field + '"]').addClass('error');
              });
            } else {
              alert("Can't send your request: " + result.error.message);
            }
          }
        }
      },
      function () {
        alert("Can't send your request!");
      }
    );
    grecaptcha.reset(grecaptchaID);
  };

});
