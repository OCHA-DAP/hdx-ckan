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
    var $this = $('#request-tags-form');
    var $fields = $this.find('.row').find('input, select, textarea');
    var $iframe = $($('.g-recaptcha').find('iframe:first'));
    var $error_blocks = $this.find('.error-block');
    var $choices = $this.find('.suggested-tags .select2-search-choice');

    $fields.removeClass('error');
    $iframe.css('border', '');
    $error_blocks.text('');
    $choices.removeClass('existing-choice');

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
          if (result.error.message === 'Captcha is not valid') {
            $iframe.css('border', '1px solid red');
          } else {
            if (result.error.fields) {
              $.each(result.error.fields, function (field, message) {
                var $input = $this.find('[name="' + field + '"]');
                $input.addClass('error');
                $input.parent().parent().find('.error-block').text(message);
              });
            } else {
              alert("Can't send your request: " + result.error.message);
            }
            if (result.error.existing_tags) {
              $.each(result.error.existing_tags, function(i, existing_tag) {
                $choices.find('div').filter(function() {
                  return $(this).text() === existing_tag;
                }).parent().addClass('existing-choice');
              });
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
