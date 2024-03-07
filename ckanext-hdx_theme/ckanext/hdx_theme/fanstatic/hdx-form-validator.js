/**
 * HDX Form Validator
 *
 * This CKAN module provides basic client-side form validation for common use cases
 * such as username, email, password, field matching and checkbox validation.
 *
 * Initialization:
 * To use this module, add the 'hdx-form-validator' module to the data-module attribute
 * of your form element. Example: <form method="post" data-module="hdx-form-validator">
 *
 * Data Attributes:
 * - Use the 'data-validation' attribute on form fields to specify the types of validation
 *   to be applied. Multiple types can be separated by commas.
 *   Example: <input type="text" name="username" data-validation="username" />
 *
 * - For field matching validation, use the 'data-validation-match' attribute on the field
 *   that should match another field.
 *   Example: <input type="password" name="confirmPassword" data-validation="match" data-validation-match="password" />
 *
 * - For checkbox validation, use the 'data-validation' attribute with the value 'checkbox'.
 *   Example: <input type="checkbox" name="terms" data-validation="checkbox" />
 */

this.ckan.module('hdx-form-validator', function ($) {
  return {
    initialize: function () {
      this.setupFieldValidation();
    },

    setupFieldValidation: function () {
      var self = this;
      var form = this.el;

      form.find('[data-validation]').each(function () {
        var fieldName = $(this).attr('name');
        var liveFeedback = $(this).data('live-feedback');
        $(this).on({
          focus: function () {
            self.removeErrorMessages(fieldName);
            if (liveFeedback) {
              self.showLiveFeedback(fieldName);
            }
          },
          blur: function () {
            self.validateField(fieldName);
            if (liveFeedback) {
              self.hideLiveFeedback(fieldName);
            }
          },
          input: function () {
            if (liveFeedback) {
              self.showLiveFeedback(fieldName);
            }
          },
        });
      });

      form.submit(function (event) {
        if (!self.validateForm()) {
          self.scrollToError();
          event.preventDefault();
        }
      });
    },

    validateField: function (fieldName) {
      var self = this;
      var field = $('[name="' + fieldName + '"]', this.el);
      var validationTypes = field.data('validation');

      if (validationTypes) {
        var types = validationTypes.split(',');

        for (var i = 0; i < types.length; i++) {
          var validationResults = self.validateWithType(field, types[i].trim(), fieldName);
          var isValid = validationResults[0];
          if (!isValid) {
            this.displayError(fieldName);
            return false;
          }
        }
      }

      return true;
    },

    validateWithType: function (field, validationType, fieldName) {
      var validationErrors = [];

      var validators = {
        username: [
          {rule: this.validateRegex, args: [/^[a-z0-9_-]+$/]},
          {rule: this.validateLength, args: [2, 100]}
        ],
        email: [
          {rule: this.validateRegex, args: [/^[^\s@]+@[^\s@]+\.[^\s@]+$/]}
        ],
        password: [
          {rule: this.validateLength, args: [10, null]}
        ],
        match: [
          {rule: this.validateFieldsMatch}
        ],
        checkbox: [
          {rule: this.validateCheckbox}
        ]
      };

      if (validators.hasOwnProperty(validationType)) {
        validators[validationType].forEach(function (validator) {
          var validation = validator.rule.apply(this, [field].concat(validator.args));
          if (!validation[0]) validationErrors.push(validation[1]);
        });

        if (validationType === 'password') {
          var passwordRules = [
            {rule: this.validateUppercase},
            {rule: this.validateLowercase},
            {rule: this.validateDigit},
            {rule: this.validatePunctuation}
          ];

          var metRules = 0;
          passwordRules.forEach(function (rule) {
            if (rule.rule(field)[0]) {
              metRules++;
            }
            else {
              validationErrors.push(rule.rule(field)[1]);
            }
          });

          if (metRules < 3) {
            validationErrors.push('no-strength');
          }
          else {
            var invalidRuleMessages = [];
            passwordRules.forEach(function (rule) {
              if (!rule.rule(field)[0]) {
                invalidRuleMessages.push(rule.rule(field)[1]);
              }
            });
            validationErrors = validationErrors.filter(function (error) {
              return !invalidRuleMessages.includes(error);
            });
          }
        }
      }

      return [validationErrors.length === 0, validationErrors];
    },


    validateRegex: function (field, regex) {
      var isValid = regex.test(field.val());
      return [isValid, isValid ? null : 'invalid-format'];
    },

    validateFieldsMatch: function (field) {
      var matchFieldName = field.data('validation-match');
      var matchField = $('[name="' + matchFieldName + '"]', this.el);
      var isValid = field.val() === matchField.val();
      return [isValid, isValid ? null : 'fields-not-match'];
    },

    validateCheckbox: function (field) {
      var isValid = field.is(':checked');
      return [isValid, isValid ? null : 'checkbox-not-checked'];
    },

    validateUppercase: function (field) {
      var isValid = /[A-Z]/.test(field.val());
      return [isValid, isValid ? null : 'no-uppercase'];
    },

    validateLowercase: function (field) {
      var isValid = /[a-z]/.test(field.val());
      return [isValid, isValid ? null : 'no-lowercase'];
    },

    validateDigit: function (field) {
      var isValid = /\d/.test(field.val());
      return [isValid, isValid ? null : 'no-digit'];
    },

    validatePunctuation: function (field) {
      var isValid = /[@$!%*?&]/.test(field.val());
      return [isValid, isValid ? null : 'no-punctuation'];
    },

    validateLength: function (field, minLength, maxLength) {
      var length = field.val().length;
      var isValid = true;

      if (minLength !== null && length < minLength) {
        isValid = false;
      }
      if (maxLength !== null && length > maxLength) {
        isValid = false;
      }

      return [isValid, isValid ? null : 'invalid-length'];
    },

    displayError: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var feedbackField = field.parent().find('.invalid-feedback');
      var errorMessage = field.data('validation-error');
      field.addClass('is-invalid');
      feedbackField.text(errorMessage);
    },

    removeErrorMessages: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      field.removeClass('is-invalid');
    },

    addLiveFeedbackMessage: function (fieldName, key, message, className) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var $liveFeedback = field.parent().parent().find('.live-feedback');
      var $message = $('<li data-live-feedback-key="' + key + '"></li>');

      $message.addClass('list-group-item');
      if (className !== '') {
        $message.addClass(className);
      }
      $liveFeedback.append($message);

      $message.html(message);
    },

    showLiveFeedback: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var validationTypes = field.data('validation') ? field.data('validation').split(',') : [];

      if (validationTypes.length) {
        var $liveFeedback = field.parent().parent().find('.live-feedback');
        this.showDefaultLiveFeedbackMessage(fieldName);

        validationTypes.forEach(function (validationType) {
          var validationResults = this.validateWithType(field, validationType.trim(), fieldName);
          var validationErrors = validationResults[1];

          validationErrors.forEach(function (errorKey) {
            var $validationError = $liveFeedback.find('li[data-live-feedback-key="' + errorKey + '"]');
            if ($validationError.length) {
              $validationError.removeClass('text-success').addClass('text-danger');
              $validationError.find('.fa-solid').removeClass('fa-check').addClass('fa-minus');
            }
            else {
              this.addLiveFeedbackMessage(fieldName, errorKey, '<i class="fa-solid fa-fw me-1 fa-minus"></i>' + errorKey, 'text-danger');
            }
          }, this);
        }, this);
      }
    },

    hideLiveFeedback: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var $liveFeedback = field.parent().parent().find('.live-feedback');

      $liveFeedback.addClass('d-none');
    },

    showDefaultLiveFeedbackMessage: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var $liveFeedback = field.parent().parent().find('.live-feedback');
      var validationMessages = {
        'name': [
          {'key': 'invalid-length', 'message': 'Username should be between 2 and 100 characters in length'},
          {'key': 'invalid-format', 'message': 'Use only lowercase alphanumeric characters, - or _'}
        ],
        'password1': [
          {'key': 'invalid-length', 'message': 'The password must be a minimum of 10 characters in length'},
          {'key': 'no-strength', 'message': 'Should contain a minimum of three out of the following four character set:'},
          {'key': 'no-uppercase', 'class': 'ps-5', 'message': 'Password should contain at least one uppercase letter'},
          {'key': 'no-lowercase', 'class': 'ps-5', 'message': 'Password should contain at least one lowercase letter'},
          {'key': 'no-digit', 'class': 'ps-5', 'message': 'Password should contain at least one digit'},
          {'key': 'no-punctuation', 'class': 'ps-5', 'message': 'Password should contain at least one special character'
          }
        ],
        'password2': [
          {'key': 'invalid-length', 'message': 'The password must be a minimum of 10 characters in length'},
          {'key': 'no-strength', 'message': 'Should contain a minimum of three out of the following four character set:'},
          {'key': 'no-uppercase', 'class': 'ps-5', 'message': 'Password should contain at least one uppercase letter'},
          {'key': 'no-lowercase', 'class': 'ps-5', 'message': 'Password should contain at least one lowercase letter'},
          {'key': 'no-digit', 'class': 'ps-5', 'message': 'Password should contain at least one digit'},
          {'key': 'no-punctuation', 'class': 'ps-5', 'message': 'Password should contain at least one special character'},
          {'key': 'fields-not-match', 'message': 'Passwords should match'}
        ],
      };

      $liveFeedback.html('').removeClass('d-none');
      var messages = validationMessages[fieldName] || [];
      messages.forEach(function (message) {
        var classes = 'text-success';
        if (message.class) {
          classes += ' ' + message.class;
        }
        this.addLiveFeedbackMessage(fieldName, message.key, '<i class="fa-solid fa-fw me-1 fa-check"></i>' + message.message, classes);
      }, this);
    },

    validateForm: function () {
      var self = this;
      var form = this.el;
      var isValid = true;

      form.find('[data-validation]').each(function () {
        var fieldName = $(this).attr('name');
        if (!self.validateField(fieldName)) {
          isValid = false;
        }
      });

      return isValid;
    },

    scrollToError: function () {
      var form = this.el;
      var topPosition = 0;
      var invalidInput = form.find('.is-invalid').first();

      if (invalidInput.length) {
        topPosition = invalidInput.parent().parent().offset().top + 200;
      }

      if (topPosition > 0) {
        $('html, body').animate({
          scrollTop: topPosition
        }, 500);
      }
    },
  };
});
