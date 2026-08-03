(function () {
  'use strict';

  function initFormValidator(form) {
    var submitButton = form.querySelector('[type="submit"]');

    // === Validation rules ===

    function validateRegex(input, regex) {
      var isValid = regex.test(input.value);
      return [isValid, isValid ? null : 'invalid-format'];
    }

    function validateLowercaseAlphanumeric(input) {
      var value = input.value;
      var isValid = !/[A-Z]/.test(value) && /[a-z0-9]/.test(value);
      return [isValid, isValid ? null : 'no-lowercase-alphanumeric'];
    }

    function validateCharacters(input, regex) {
      var isValid = regex.test(input.value);
      return [isValid, isValid ? null : 'invalid-characters'];
    }

    function validateFieldsMatch(input) {
      var matchFieldName = input.getAttribute('data-validation-match');
      var matchField = form.querySelector('[name="' + matchFieldName + '"]');
      var isValid = matchField ? input.value === matchField.value : false;
      return [isValid, isValid ? null : 'fields-not-match'];
    }

    function validateCheckbox(input) {
      return [input.checked, input.checked ? null : 'checkbox-not-checked'];
    }

    function validateUppercase(input) {
      var isValid = /[A-Z]/.test(input.value);
      return [isValid, isValid ? null : 'no-uppercase'];
    }

    function validateLowercase(input) {
      var isValid = /[a-z]/.test(input.value);
      return [isValid, isValid ? null : 'no-lowercase'];
    }

    function validateDigit(input) {
      var isValid = /\d/.test(input.value);
      return [isValid, isValid ? null : 'no-digit'];
    }

    function validatePunctuation(input) {
      var isValid = /[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/.test(input.value);
      return [isValid, isValid ? null : 'no-punctuation'];
    }

    function validateLength(input, minLength, maxLength) {
      var length = input.value.length;
      var isValid = (minLength === null || length >= minLength) && (maxLength === null || length <= maxLength);
      return [isValid, isValid ? null : 'invalid-length'];
    }

    function validateWithType(input, validationType) {
      var validationErrors = [];

      var validators = {
        fullname: [{rule: validateLength, args: [1, null]}],
        username: [
          {rule: validateLowercaseAlphanumeric, args: []},
          {rule: validateLength, args: [2, 100]},
          {rule: validateCharacters, args: [/^[a-zA-Z0-9_-]+$/]}
        ],
        email: [{rule: validateRegex, args: [/^[^\s@]+@[^\s@]+\.[^\s@]+$/]}],
        password: [{rule: validateLength, args: [10, null]}],
        match: [{rule: validateFieldsMatch, args: []}],
        checkbox: [{rule: validateCheckbox, args: []}]
      };

      if (!validators.hasOwnProperty(validationType)) return [true, []];

      validators[validationType].forEach(function (v) {
        var result = v.rule.apply(null, [input].concat(v.args));
        if (!result[0]) validationErrors.push(result[1]);
      });

      if (validationType === 'password') {
        var passwordRules = [validateUppercase, validateLowercase, validateDigit, validatePunctuation];
        var metRules = 0;
        var ruleErrors = [];
        passwordRules.forEach(function (ruleFn) {
          var result = ruleFn(input);
          if (result[0]) {
            metRules++;
          } else {
            validationErrors.push(result[1]);
            ruleErrors.push(result[1]);
          }
        });
        if (metRules < 3) {
          validationErrors.push('no-strength');
        } else {
          validationErrors = validationErrors.filter(function (err) {
            return ruleErrors.indexOf(err) === -1;
          });
        }
      }

      return [validationErrors.length === 0, validationErrors];
    }

    // === Error display ===

    function displayError(input) {
      var wrapper = input.closest('.c-search-input');
      if (wrapper) {
        wrapper.classList.add('c-search-input--error');
        var errorEl = wrapper.parentElement ? wrapper.parentElement.querySelector('.c-search-input__error') : null;
        if (errorEl) {
          errorEl.textContent = input.getAttribute('data-validation-error') || '';
        }
      } else {
        var checkboxWrapper = input.closest('.c-checkbox');
        if (checkboxWrapper) {
          checkboxWrapper.classList.add('c-checkbox--error');
          var errorEl = checkboxWrapper.parentElement ? checkboxWrapper.parentElement.querySelector('.c-checkbox__error') : null;
          if (errorEl) errorEl.textContent = input.getAttribute('data-validation-error') || '';
        }
      }
    }

    function removeErrorMessages(input) {
      var wrapper = input.closest('.c-search-input');
      if (wrapper) {
        wrapper.classList.remove('c-search-input--error');
        var errorEl = wrapper.parentElement ? wrapper.parentElement.querySelector('.c-search-input__error') : null;
        if (errorEl) {
          errorEl.textContent = '';
        }
      } else {
        var checkboxWrapper = input.closest('.c-checkbox');
        if (checkboxWrapper) {
          checkboxWrapper.classList.remove('c-checkbox--error');
          var errorEl = checkboxWrapper.parentElement ? checkboxWrapper.parentElement.querySelector('.c-checkbox__error') : null;
          if (errorEl) errorEl.textContent = '';
        }
      }
    }

    // === Live feedback ===

    var liveFeedbackMessages = {
      'name': [
        {key: 'invalid-length', message: 'Must be between 2 and 100 characters in length'},
        {key: 'no-lowercase-alphanumeric', message: 'Must use lowercase alphanumeric characters (a-z, 0-9)'},
        {key: 'invalid-characters', message: 'Only allowed special characters - (dash) or _ (underscore)'}
      ],
      'password1': [
        {key: 'invalid-length', message: 'The password must be a minimum of 10 characters in length'},
        {key: 'no-strength', message: 'Must contain a minimum of three out of the following four:'},
        {key: 'no-uppercase', extraClass: 'c-form-validator__live-feedback-item--indent', message: 'at least one uppercase letter'},
        {key: 'no-lowercase', extraClass: 'c-form-validator__live-feedback-item--indent', message: 'at least one lowercase letter'},
        {key: 'no-digit', extraClass: 'c-form-validator__live-feedback-item--indent', message: 'at least one number'},
        {key: 'no-punctuation', extraClass: 'c-form-validator__live-feedback-item--indent', message: 'at least one special character'}
      ],
      'password2': [
        {key: 'fields-not-match', message: 'Passwords should match'}
      ]
    };

    function getLiveFeedback(input) {
      var grandparent = input.parentElement ? input.parentElement.parentElement : null;
      return grandparent ? grandparent.querySelector('.c-form-validator__live-feedback') : null;
    }

    function addLiveFeedbackItem(liveFeedback, key, message, extraClass) {
      var li = document.createElement('li');
      li.className = 'c-form-validator__live-feedback-item c-form-validator__live-feedback-item--pass';
      if (extraClass) li.classList.add(extraClass);
      li.setAttribute('data-live-feedback-key', key);
      li.textContent = message;
      liveFeedback.appendChild(li);
    }

    function showDefaultLiveFeedbackMessage(input) {
      var liveFeedback = getLiveFeedback(input);
      if (!liveFeedback) return;
      liveFeedback.innerHTML = '';
      liveFeedback.removeAttribute('hidden');
      var messages = liveFeedbackMessages[input.getAttribute('name')] || [];
      messages.forEach(function (msg) {
        addLiveFeedbackItem(liveFeedback, msg.key, msg.message, msg.extraClass || '');
      });
    }

    function showLiveFeedback(input) {
      var liveFeedback = getLiveFeedback(input);
      if (!liveFeedback) return;
      var validationTypes = input.getAttribute('data-validation');
      if (!validationTypes) return;
      showDefaultLiveFeedbackMessage(input);
      validationTypes.split(',').forEach(function (type) {
        var result = validateWithType(input, type.trim());
        var errors = result[1];
        errors.forEach(function (errorKey) {
          var item = liveFeedback.querySelector('li[data-live-feedback-key="' + errorKey + '"]');
          if (item) {
            item.classList.remove('c-form-validator__live-feedback-item--pass');
            item.classList.add('c-form-validator__live-feedback-item--fail');
          } else {
            var li = document.createElement('li');
            li.className = 'c-form-validator__live-feedback-item c-form-validator__live-feedback-item--fail';
            li.setAttribute('data-live-feedback-key', errorKey);
            li.textContent = errorKey;
            liveFeedback.appendChild(li);
          }
        });
      });
    }

    function validateLiveFeedback(input) {
      var liveFeedback = getLiveFeedback(input);
      if (!liveFeedback) return;
      liveFeedback.querySelectorAll('li').forEach(function (li) {
        li.classList.remove('c-form-validator__live-feedback-item--fail');
        li.classList.add('c-form-validator__live-feedback-item--pass');
      });
    }

    // === Field validation ===

    function validateField(input, doDisplayError) {
      var validationTypes = input.getAttribute('data-validation');
      var hasLiveFeedback = input.getAttribute('data-live-feedback');
      if (!validationTypes) return true;

      var types = validationTypes.split(',');
      for (var i = 0; i < types.length; i++) {
        var result = validateWithType(input, types[i].trim());
        if (!result[0]) {
          if (doDisplayError) {
            if (hasLiveFeedback) showLiveFeedback(input);
            displayError(input);
          }
          return false;
        } else {
          validateLiveFeedback(input);
        }
      }
      return true;
    }

    // === Form validation ===

    function validateForm(currentInput) {
      var inputs = form.querySelectorAll('[data-validation]');
      var isFormValid = true;
      inputs.forEach(function (input) {
        var shouldDisplay = currentInput === null || currentInput === input;
        if (!validateField(input, shouldDisplay)) {
          isFormValid = false;
        } else {
          removeErrorMessages(input);
        }
      });
      if (isFormValid) {
        enableSubmitButton();
      } else {
        disableSubmitButton();
      }
      return isFormValid;
    }

    // === Submit button ===

    function disableSubmitButton() {
      if (!submitButton) return;
      submitButton.classList.add('is-disabled');
      submitButton.setAttribute('disabled', '');
      submitButton.setAttribute('aria-disabled', 'true');
    }

    function enableSubmitButton() {
      if (!submitButton) return;
      submitButton.classList.remove('is-disabled');
      submitButton.removeAttribute('disabled');
      submitButton.removeAttribute('aria-disabled');
    }

    // === Scroll to error ===

    function scrollToError() {
      var invalidEl = form.querySelector('.c-search-input--error, .c-checkbox--error');
      if (!invalidEl) return;
      var drawerBody = form.closest('.c-drawer__body');
      if (drawerBody) {
        var elTop = invalidEl.getBoundingClientRect().top - drawerBody.getBoundingClientRect().top;
        drawerBody.scrollTo({top: elTop + drawerBody.scrollTop - 80, behavior: 'smooth'});
      } else {
        var container = invalidEl.closest('.c-form-field') || invalidEl;
        var topPosition = container.getBoundingClientRect().top + window.scrollY - 100;
        if (topPosition > 0) window.scrollTo({top: topPosition, behavior: 'smooth'});
      }
    }

    // === Event binding ===

    form.querySelectorAll('[data-validation]').forEach(function (input) {
      var hasLiveFeedback = input.getAttribute('data-live-feedback');
      input.addEventListener('focus', function () {
        removeErrorMessages(input);
        if (hasLiveFeedback) showLiveFeedback(input);
      });
      input.addEventListener('blur', function () {
        validateForm(input);
      });
      input.addEventListener('input', function () {
        if (hasLiveFeedback) showLiveFeedback(input);
      });
    });

    form.addEventListener('submit', function (e) {
      if (!validateForm(null)) {
        scrollToError();
        e.preventDefault();
      }
    });

    if (submitButton && submitButton.parentElement) {
      submitButton.parentElement.addEventListener('click', function () {
        if (!validateForm(null)) scrollToError();
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form[data-hdx-v2-form-validator]').forEach(initFormValidator);
  });

})();
