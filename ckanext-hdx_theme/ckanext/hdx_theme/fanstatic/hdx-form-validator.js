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
        $(this).on({
          focus: function () {
            self.removeErrorMessages(fieldName);
          },
          blur: function () {
            self.validateField(fieldName);
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
          if (!self.validateWithType(field, types[i].trim(), fieldName)) {
            return false;
          }
        }
      }

      return true;
    },

    validateWithType: function (field, validationType, fieldName) {
      var isValid = true;

      switch (validationType) {
        case 'username':
          isValid = this.validateRegex(field, /^[a-z0-9_-]{2,100}$/);
          break;
        case 'email':
          isValid = this.validateRegex(field, /^[^\s@]+@[^\s@]+\.[^\s@]+$/);
          break;
        case 'password':
          isValid = this.validatePassword(field);
          break;
        case 'match':
          isValid = this.matchFields(field);
          break;
        case 'checkbox':
          isValid = this.validateCheckbox(field);
          break;
      }

      if (!isValid) {
        this.displayError(fieldName);
      }

      return isValid;
    },

    validateRegex: function (field, regex) {
      return regex.test(field.val());
    },

    validatePassword: function (field) {
      var password = field.val();

      var hasUppercase = /[A-Z]/.test(password);
      var hasLowercase = /[a-z]/.test(password);
      var hasDigit = /\d/.test(password);
      var hasPunctuation = /[@$!%*?&]/.test(password);

      var isLengthValid = password.length >= 10;

      var characterSetCount = [hasUppercase, hasLowercase, hasDigit, hasPunctuation].filter(Boolean).length;

      return characterSetCount >= 3 && isLengthValid;
    },

    matchFields: function (field) {
      var matchFieldName = field.data('validation-match');
      var matchField = $('[name="' + matchFieldName + '"]', this.el);
      return field.val() === matchField.val();
    },

    validateCheckbox: function (field) {
      return field.is(':checked');
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

      if(invalidInput.length) {
        if (invalidInput.attr('type') === 'password') {
          topPosition = invalidInput.parent().parent().offset().top + 200;
        }
        else {
          topPosition = invalidInput.parent().offset().top + 200;
        }
      }

      if(topPosition > 0) {
        $('html, body').animate({
          scrollTop: topPosition
        }, 500);
      }
    },
  };
});
