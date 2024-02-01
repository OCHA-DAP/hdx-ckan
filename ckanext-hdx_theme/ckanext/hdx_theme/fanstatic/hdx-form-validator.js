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
      field.addClass('is-invalid');
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
  };
});
