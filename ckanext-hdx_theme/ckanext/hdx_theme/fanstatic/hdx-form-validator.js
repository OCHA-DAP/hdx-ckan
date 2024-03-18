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
      var $submitButton = form.find('[type="submit"]');

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
            self.validateForm(fieldName);
          },
          input: function () {
            if (liveFeedback) {
              self.showLiveFeedback(fieldName);
            }
          },
        });
      });

      form.submit(function (event) {
        if (!self.validateForm(null)) {
          self.scrollToError();
          event.preventDefault();
        }
      });

      $submitButton.parent().on('click', function () {
        if (!self.validateForm(null)) {
          self.scrollToError();
        }
      });
    },

    validateField: function (fieldName, displayError) {
      var self = this;
      var field = $('[name="' + fieldName + '"]', this.el);
      var validationTypes = field.data('validation');
      var liveFeedback = field.data('live-feedback');

      if (validationTypes) {
        var types = validationTypes.split(',');

        for (var i = 0; i < types.length; i++) {
          var validationResults = self.validateWithType(field, types[i].trim(), fieldName);
          var isValid = validationResults[0];
          if (!isValid) {
            if (displayError) {
              if (liveFeedback) {
                self.showLiveFeedback(fieldName);
              }
              self.displayError(fieldName);
            }
            return false;
          }
          else {
            self.validateLiveFeedback(fieldName);
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
      var form = field.closest('form');
      var matchFieldName = field.data('validation-match');
      var matchField = $('[name="' + matchFieldName + '"]', form);
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
      var isValid = /[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/.test(field.val());
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

    validateLiveFeedback: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var $liveFeedback = field.parent().parent().find('.live-feedback');

      if ($liveFeedback.length) {
        $liveFeedback.find('li').removeClass('text-danger').addClass('text-success');
        $liveFeedback.find('li .fa-solid').removeClass('fa-minus').addClass('fa-check');
      }
    },

    showDefaultLiveFeedbackMessage: function (fieldName) {
      var field = $('[name="' + fieldName + '"]', this.el);
      var $liveFeedback = field.parent().parent().find('.live-feedback');
      var validationMessages = {
        'name': [
          {'key': 'invalid-length', 'message': 'Must be between 2 and 100 characters in length'},
          {'key': 'invalid-format', 'message': 'Must use lowercase alphanumeric characters'},
          {'key': null, 'message': 'Can use - (dash) or _ (underscore)'}
        ],
        'password1': [
          {'key': 'invalid-length', 'message': 'The password must be a minimum of 10 characters in length'},
          {'key': 'no-strength', 'message': 'Must contain a minimum of three out of the following four:'},
          {'key': 'no-uppercase', 'class': 'ps-5', 'message': 'at least one uppercase letter'},
          {'key': 'no-lowercase', 'class': 'ps-5', 'message': 'at least one lowercase letter'},
          {'key': 'no-digit', 'class': 'ps-5', 'message': 'at least one number'},
          {'key': 'no-punctuation', 'class': 'ps-5', 'message': 'at least one special character'}
        ],
        'password2': [
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

    validateForm: function (currentField) {
      var self = this;
      var form = this.el;
      var isFormValid = true;

      form.find('[data-validation]').each(function () {
        var fieldName = $(this).attr('name');
        var displayError = currentField && currentField === fieldName || currentField == null;
        var isFieldValid = self.validateField(fieldName, displayError);
        if (!isFieldValid) {
          isFormValid = false;
        }
        else {
          self.removeErrorMessages(fieldName);
        }
      });

      if (!isFormValid) {
        self.disableSubmitButton();
      }
      else {
        self.enableSubmitButton();
      }

      return isFormValid;
    },

    scrollToError: function () {
      var form = this.el;
      var topPosition = 0;
      var invalidInput = form.find('.is-invalid').first();

      if (invalidInput.length) {
        topPosition = invalidInput.parent().parent().offset().top - 100;
      }

      if (topPosition > 0) {
        $('html, body').animate({
          scrollTop: topPosition
        }, 500);
      }
    },

    disableSubmitButton: function () {
      var form = this.el;
      var $submitButton = form.find('[type="submit"]');
      $submitButton.addClass('disabled').attr('disabled');
    },

    enableSubmitButton: function () {
      var form = this.el;
      var $submitButton = form.find('[type="submit"]');
      $submitButton.removeClass('disabled').removeAttr('disabled');
    },
  };
});
