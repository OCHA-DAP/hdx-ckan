function _markAlreadyApprovedTags(existing_tags) {
  var $choices = $('#request-tags-form').find('.suggested-tags .select2-search-choice');

  $.each(existing_tags, function(i, existing_tag) {
    $choices.find('div').filter(function () {
      return $(this).text() === existing_tag;
    }).parent().addClass('existing-choice');
  });

  _showAlreadyApprovedTagsError(existing_tags);
}

function _showAlreadyApprovedTagsError(existing_tags) {
  var $form = $('#request-tags-form');
  var $input = $form.find('[name="suggested_tags"]');

  var message = '';
  var noTags = existing_tags.length;

  if (noTags) {
    if (noTags > 1) {
      message = existing_tags.join(', ') + ' already exist';
    } else {
      message = existing_tags[0] + ' already exists';
    }
    $input.addClass('error');
  } else {
    $input.removeClass('error');
  }
  $input.parent().parent().find('.error-block').text(message);
}

function showTagRequestWidget(id) {

  $(id).show();

  function _tagRequestTriggerInputDataClass($this) {
    if ($this.val() === '')
      $this.removeClass('input-content');
    else
      $this.addClass('input-content');
  }

  $(id).find('input[type="password"], input[type="text"], textarea').each(function (idx, el) {
    _tagRequestTriggerInputDataClass($(el));
  });

  $(id).find('input[type="password"], input[type="text"], textarea').on('change keyup', function () {
    _tagRequestTriggerInputDataClass($(this));
  });

  $.post('/api/action/hdx_tag_approved_list')
    .done((data) => {
      if (data.success) {
        var existingTags = [];
        $(id).find('#suggested_tags').on('change', function (e) {
          if(e.added) {
            if(data.result.includes(e.added.text.toLowerCase())) {
              existingTags.push(e.added.text);
              _markAlreadyApprovedTags(existingTags);
            }
          }
          else if(e.removed) {
            var index = existingTags.indexOf(e.removed.text);
            if (index !== -1) {
              existingTags.splice(index, 1);
              _showAlreadyApprovedTagsError(existingTags);
            }
          }
        });
      } else {
        console.log('Error, approved tags not loaded!');
      }
    })
    .fail((fail) => {
      console.log('Error, approved tags not loaded!');
    });
}

$(document).ready(function () {
  requestTagsOnSubmit = function () {
    var $this = $('#request-tags-form');
    var $fields = $this.find('.row').find('input, select, textarea');
    var $iframe = $($('.g-recaptcha').find('iframe:first'));
    var $error_blocks = $this.find('.error-block');

    $fields.removeClass('error');
    $iframe.css('border', '');
    $error_blocks.text('');

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
          showTagRequestWidget('#requestTagsConfirmationPopup');
        } else {
          if (result.error.message === 'Captcha is not valid') {
            $iframe.css('border', '1px solid red');
          } else {
            if (result.error.existing_tags) {
              _markAlreadyApprovedTags(result.error.existing_tags);
            }
            if (result.error.fields) {
              $.each(result.error.fields, function (field, message) {
                var $input = $this.find('[name="' + field + '"]');
                $input.addClass('error');
                $input.parent().parent().find('.error-block').text(message);
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
