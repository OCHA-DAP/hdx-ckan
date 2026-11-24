(function () {
  'use strict';

  var VALIDATE_URL       = '/contribute/validate';
  var GUESS_FORMAT_URL   = '/api/action/hdx_guess_format_from_extension?q=';
  var RECOMMEND_TAGS_URL = '/api/action/hdx_recommend_tags';
  var PACKAGE_SHOW_URL   = '/api/action/package_show_edit?id=';
  var PRIVATE_INFO_KEY   = '/contribute:hidePrivateDatasetInfo';
  var ARCHIVE_EXTENSIONS = ['zip', '7z', 'tar', 'rar'];
  var FIELDLESS_SUMMARY  = ['resource-list', 'server_or_connection_error', 'General Error'];
  var ERROR_TARGETS      = {
    groups_list:  '[name="locations"]',
    dataset_date: '#ui_date_range1',
    tags:         '[name="tag_string"]'
  };
  var GOOGLE_DRIVE = {
    apiKey:   'AIzaSyD_jaQn1BkqeA5Bua4GlC61DB-8p-Gwa7E',
    clientId: '732730459122-896ieod4v4i9qdj8hq0vqj5mmlb13h0l.apps.googleusercontent.com',
    scope:    'https://www.googleapis.com/auth/drive.file',
    appId:    '732730459122'
  };

  function fill(template, values) {
    return Object.keys(values).reduce(function (text, key) {
      return text.replace('{' + key + '}', values[key]);
    }, template);
  }

  function isTrue(value) {
    return value === true || value === 'true' || value === 'True';
  }

  function messagesOf(value) {
    if (value === null || value === undefined) return [];
    if (typeof value === 'string') return [value];
    if (Array.isArray(value)) return value.reduce(function (all, item) { return all.concat(messagesOf(item)); }, []);
    if (typeof value === 'object') return Object.keys(value).reduce(function (all, key) { return all.concat(messagesOf(value[key])); }, []);
    return [String(value)];
  }

  function prettify(key) {
    var text = key.replace(/_/g, ' ');
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  function computeExtension(url) {
    if (!url) return null;
    try {
      var pathname = new URL(url, 'https://data.humdata.org').pathname;
      var lastIndex = pathname.lastIndexOf('.');
      if (lastIndex > 0 && lastIndex + 1 < pathname.length) return pathname.substring(lastIndex + 1).toLowerCase();
    } catch (e) {
      return null;
    }
    return null;
  }

  function resourceExtension(attrs) {
    return computeExtension(attrs.name) || computeExtension(attrs.url);
  }

  function hashResource(attrs) {
    return window.hdxUtil.compute.strListHash([
      attrs.name, attrs.format, attrs.url, attrs.description, attrs.url_type, attrs.resource_type,
      attrs.dataset_preview_enabled ? 'true' : 'false',
      attrs.upload ? 'true' : 'false',
      attrs.microdata ? 'true' : 'false'
    ]);
  }

  function flatten(obj, prefix, output) {
    Object.keys(obj).forEach(function (key) {
      var value = obj[key];
      var name = prefix ? prefix + '[' + key + ']' : key;
      if (value !== null && typeof value === 'object') {
        flatten(value, name, output);
      } else if (value !== undefined && value !== null) {
        output.push([name, value]);
      }
    });
    return output;
  }

  function paramValue(value) {
    return value === null || value === undefined ? '' : String(value);
  }

  function encode(values) {
    var params = new URLSearchParams();
    values.forEach(function (item) { params.append(item.name, item.value); });
    return params;
  }

  function requireSuccess(reply) {
    if (!reply || !reply.success) {
      var error = new Error('Request failed');
      error.reply = reply;
      throw error;
    }
    return reply;
  }

  function init(form) {
    var messages       = JSON.parse(form.getAttribute('data-messages'));
    var datasetId      = form.getAttribute('data-dataset-id') || null;
    var datasetName    = null;
    var wasRequestdata = form.getAttribute('data-dataset-requestdata') === 'true';
    var requestUrl     = window.location.pathname;
    var errorAlert     = form.querySelector('[data-dataset-form-error]');
    var submit         = document.getElementById('create-form-submit');
    var terms          = document.getElementById('checkbox-hdx-terms');
    var list           = document.getElementById('resource-list');
    var categories     = JSON.parse(form.getAttribute('data-format-categories'));
    var configItem     = window.hdxV2ConfigItem(list);
    var previewCheck   = document.getElementById('field_dataset_preview_check');
    var previewSelect  = document.getElementById('field_dataset_preview_value');
    var previewField   = document.getElementById('dataset-preview-check-other-define');
    var overlay        = document.querySelector('[data-dataset-form-overlay]');
    var overlayMessage = overlay.querySelector('[data-dataset-form-overlay-message]');
    var cards          = new Map();
    var removed        = [];
    var serverOrder    = [];
    var busy           = false;
    var googlePicker   = null;
    var pickerTarget   = null;

    function showOverlay(text) {
      overlayMessage.textContent = text;
      overlay.hidden = false;
      form.inert = true;
    }

    function hideOverlay() {
      overlay.hidden = true;
      form.inert = false;
    }

    function showFieldless(lines) {
      window.hdxV2.showAlert(errorAlert, lines.join(' '));
    }

    function currentMode() {
      var checked = form.querySelector('input[name="private"]:checked');
      return checked ? checked.value : 'private';
    }

    function setRequired(field, required) {
      var label = field.querySelector('.c-form-field__label');
      var mark  = label && label.querySelector('.c-form-field__required');
      if (required && label && !mark) {
        mark = document.createElement('span');
        mark.className = 'c-form-field__required';
        mark.setAttribute('aria-hidden', 'true');
        mark.textContent = ' *';
        label.appendChild(mark);
      } else if (!required && mark) {
        mark.remove();
      }
      var control = field.querySelector('[name]:not([type="hidden"]):not([type="checkbox"])');
      if (control) control.required = required;
    }

    function applyMode() {
      var mode = currentMode();
      form.querySelectorAll('[data-required-modes]').forEach(function (field) {
        setRequired(field, field.getAttribute('data-required-modes').split(',').indexOf(mode) !== -1);
      });
      form.querySelectorAll('[data-share-hide]').forEach(function (el) {
        el.hidden = el.getAttribute('data-share-hide') === mode;
      });
      form.querySelectorAll('[data-share-show]').forEach(function (el) {
        el.hidden = el.getAttribute('data-share-show') !== mode;
      });
      form.querySelector('[data-share-notice="public"]').hidden = mode !== 'public';
      form.querySelector('[data-share-notice="requestdata"]').hidden = !(mode === 'requestdata' && datasetId && !wasRequestdata);
      document.querySelectorAll('.c-anchor-links__item[href^="#"]').forEach(function (link) {
        var section = document.getElementById(link.getAttribute('href').slice(1));
        link.hidden = !!section && section.hidden;
      });
    }

    function refreshTerms() {
      var blocked = Array.from(cards.values()).some(function (resource) { return resource.piiTickedHere; });
      if (blocked) terms.checked = false;
      window.hdxV2.setDisabled(terms, blocked);
      window.hdxV2.setDisabled(submit, !terms.checked);
    }

    function orderedResources() {
      return Array.from(list.querySelectorAll('[data-config-item]')).map(function (card) {
        return cards.get(card);
      }).filter(Boolean);
    }

    function applyPreviewSelection() {
      var index = Number(previewSelect.value);
      orderedResources().forEach(function (resource, i) {
        resource.attrs.dataset_preview_enabled = !isNaN(index) && i === index;
      });
    }

    function rebuildPreviewOptions(apply) {
      var selectedValue = 'first_resource';
      previewSelect.textContent = '';
      previewSelect.add(new Option(messages.previewDefault, 'first_resource'));
      orderedResources().forEach(function (resource, index) {
        var name = resource.attrs.name ? resource.attrs.name : fill(messages.resourceName, { n: index + 1 });
        previewSelect.add(new Option(name, String(index)));
        if (resource.attrs.dataset_preview_enabled === true) selectedValue = String(index);
      });
      previewSelect.value = selectedValue;
      if (apply) applyPreviewSelection();
    }

    var rebuildPreviewOptionsSoon = window.hdxUtil.eventUtil.debouncer(function () {
      rebuildPreviewOptions(true);
    }, 300);

    function control(resource, field) {
      return resource.card.querySelector('[data-resource-field="' + field + '"]');
    }

    function formatCategory(format) {
      var value = (format || '').toLowerCase();
      var match = Object.keys(categories).filter(function (category) {
        return categories[category].indexOf(value) !== -1;
      })[0];
      return match || 'neutral';
    }

    function showFileType(resource, format) {
      var category = formatCategory(format);
      resource.card.querySelectorAll('[data-resource-file-type]').forEach(function (tile) {
        tile.hidden = tile.getAttribute('data-resource-file-type') !== category;
      });
    }

    function setFormat(resource, format) {
      var select = control(resource, 'format');
      if (format && !Array.prototype.some.call(select.options, function (option) { return option.value === format; })) {
        select.add(new Option(format, format));
      }
      jQuery(select).val(format || '').trigger('change.select2');
      showFileType(resource, format);
    }

    function showFormatWarning(resource) {
      var isArchive = ARCHIVE_EXTENSIONS.indexOf(resourceExtension(resource.attrs)) >= 0;
      var select = control(resource, 'format');
      if (isArchive && !resource.attrs.format) {
        window.hdxV2.setFieldError(select, messages.archiveFormat);
      } else {
        window.hdxV2.setFieldError(select, '');
      }
    }

    function guessFormat(resource) {
      var extension = resourceExtension(resource.attrs);
      if (!extension) return;
      fetch(GUESS_FORMAT_URL + encodeURIComponent(extension))
        .then(function (response) { return response.json(); })
        .then(function (reply) {
          if (reply.success === true && reply.result) {
            resource.attrs.format = reply.result;
            setFormat(resource, reply.result);
            showFormatWarning(resource);
          }
        })
        .catch(function () {});
    }

    function setSource(resource, state) {
      var card   = resource.card;
      var fields = card.querySelector('[data-resource-fields]');
      card.querySelector('[data-resource-upload]').hidden = state === 'url';
      fields.hidden = state === 'file';
      card.querySelector('[data-resource-url-field]').hidden = state !== 'url';
      card.querySelector('[data-text-field-leading]').hidden = state !== 'file-selected';
      card.querySelector('[data-resource-source][value="' + (state === 'url' ? 'url' : 'file') + '"]').checked = true;
      if (state === 'url') {
        resource.attrs.url_type = 'api';
        resource.attrs.resource_type = 'api';
        resource.attrs.upload = null;
      }
    }

    function setUpWithPath(resource, path, useShortUrl, filename, isUrl, file) {
      var name = filename || path.split('\\').pop().split('/').pop();
      if (file) resource.attrs.upload = file;
      resource.attrs.url_type = isUrl ? 'api' : 'upload';
      resource.attrs.resource_type = isUrl ? 'api' : 'file.upload';
      resource.attrs.url = useShortUrl ? name : path;
      resource.attrs.name = name;
      control(resource, 'url').value = resource.attrs.url;
      control(resource, 'name').value = name;
    }

    function fillCard(card, resource) {
      var attrs = resource.attrs;
      resource.card = card;
      cards.set(card, resource);
      control(resource, 'name').value = attrs.name || '';
      control(resource, 'description').value = attrs.description || '';
      control(resource, 'url').value = attrs.url || '';
      setFormat(resource, attrs.format);
      [['pii', attrs.pii], ['microdata', attrs.microdata]].forEach(function (pair) {
        var checked = isTrue(pair[1]);
        control(resource, pair[0]).checked = checked;
        card.querySelector('[data-resource-notice="' + pair[0] + '"]').hidden = !checked;
      });
      var state = 'file';
      if (attrs.url_type || attrs.resource_type) {
        state = attrs.url_type === 'upload' || attrs.resource_type === 'file.upload' ? 'file-selected' : 'url';
      }
      if (state === 'file-selected') {
        var upload = card.querySelector('[data-image-upload]');
        upload.querySelector('[data-image-upload-url]').value = attrs.url || '';
        upload.setAttribute('data-image-upload-state', 'attached');
      }
      setSource(resource, state);
    }

    function register(attrs) {
      attrs.originalHash = hashResource(attrs);
      attrs.batch_mode = 'DONT_GROUP';
      return {
        attrs: attrs,
        card: null,
        piiTickedHere: false,
        savedHash: attrs.originalHash,
        savedPii: isTrue(attrs.pii)
      };
    }

    function addExisting(attrs) {
      var resource = register(attrs);
      configItem.add({
        position: 'end',
        focus: false,
        prepare: function (card) { fillCard(card, resource); }
      });
      showFormatWarning(resource);
    }

    function newDefaults() {
      return { position: cards.size, url: '', format: '', pii: false, microdata: false, description: '' };
    }

    function finishLoading() {
      serverOrder = orderedResources().map(function (resource) { return resource.attrs.id; }).filter(Boolean);
      rebuildPreviewOptions(false);
      refreshTerms();
      if (window.location.hash && cards.size) {
        var target = document.getElementById(window.location.hash.slice(1));
        var field = target && form.contains(target) && target.closest('.c-form-field, fieldset, section');
        if (field) field.scrollIntoView();
      }
    }

    function buildCards(items) {
      var schedule = window.requestIdleCallback || function (callback) { setTimeout(callback, 16); };
      var batch = function (start) {
        items.slice(start, start + 10).forEach(addExisting);
        if (start + 10 < items.length) {
          schedule(function () { batch(start + 10); });
        } else {
          finishLoading();
        }
      };
      if (items.length) batch(0); else finishLoading();
    }

    function loadResources() {
      var json = document.getElementById('resource-list-json');
      if (json) {
        buildCards(JSON.parse(json.textContent));
        return;
      }
      if (!datasetId) {
        finishLoading();
        return;
      }
      showOverlay(messages.wait);
      fetch(PACKAGE_SHOW_URL + encodeURIComponent(datasetId))
        .then(function (response) { return response.json(); })
        .then(function (reply) {
          hideOverlay();
          buildCards(reply.result.resources || []);
        })
        .catch(function () {
          hideOverlay();
          showFieldless([messages.serverError]);
          finishLoading();
        });
    }

    function openDropbox(resource) {
      window.Dropbox.choose({
        success: function (files) { cloudFileSelected(resource, files[0].link, files[0].name); },
        linkType: 'preview'
      });
    }

    function cloudFileSelected(resource, url, filename) {
      setUpWithPath(resource, url, false, filename, true);
      setSource(resource, 'url');
      control(resource, 'url').focus();
      rebuildPreviewOptionsSoon();
    }

    function openGoogleDrive(resource) {
      if (!googlePicker || !googlePicker.tokenClient) return;
      pickerTarget = resource;
      googlePicker.open();
    }

    list.addEventListener('config-item:add', function (e) {
      if (cards.has(e.target)) return;
      fillCard(e.target, register(newDefaults()));
      rebuildPreviewOptions(true);
    });

    list.addEventListener('config-item:remove', function (e) {
      var resource = cards.get(e.detail.item);
      if (!resource) return;
      cards.delete(e.detail.item);
      if (resource.attrs.id) removed.push(resource);
      refreshTerms();
      rebuildPreviewOptions(true);
    });

    list.addEventListener('config-item:sort', function () {
      rebuildPreviewOptions(true);
    });

    list.addEventListener('change', function (e) {
      var card = e.target.closest('[data-config-item]');
      var resource = card && cards.get(card);
      if (!resource) return;
      if (e.target.hasAttribute('data-resource-source')) {
        var toUrl = e.target.value === 'url';
        var currentUrlType = resource.attrs.url_type;
        if (currentUrlType && currentUrlType !== (toUrl ? 'api' : 'upload')) {
          delete resource.attrs.upload;
          delete resource.attrs.url_type;
          delete resource.attrs.resource_type;
          resource.attrs.url = '';
          control(resource, 'url').value = '';
          card.querySelector('[data-image-upload-url]').value = '';
          card.querySelector('[data-image-upload-file]').value = '';
          card.querySelector('[data-image-upload-attached]').hidden = true;
          card.querySelector('[data-image-upload-blank]').hidden = false;
        }
        setSource(resource, toUrl ? 'url' : 'file');
        return;
      }
      var field = e.target.getAttribute('data-resource-field');
      if (!field || e.target.tagName === 'SELECT') return;
      if (field === 'pii' || field === 'microdata') {
        resource.attrs[field] = e.target.checked;
        card.querySelector('[data-resource-notice="' + field + '"]').hidden = !e.target.checked;
        if (field === 'pii') {
          resource.piiTickedHere = e.target.checked;
          refreshTerms();
        }
        return;
      }
      resource.attrs[field] = e.target.value;
      if (field === 'name' || field === 'url') {
        guessFormat(resource);
        showFormatWarning(resource);
      }
      if (field === 'name') rebuildPreviewOptionsSoon();
    });

    jQuery(list).on('change', 'select[data-resource-field="format"]', function () {
      var resource = cards.get(this.closest('[data-config-item]'));
      if (!resource) return;
      resource.attrs.format = this.value || '';
      showFileType(resource, resource.attrs.format);
      showFormatWarning(resource);
    });

    list.addEventListener('image-upload:change', function (e) {
      var card = e.target.closest('[data-config-item]');
      var resource = card && cards.get(card);
      var file = e.target.querySelector('[data-image-upload-file]').files[0];
      if (!resource || !file) return;
      resource.attrs.format = '';
      setFormat(resource, '');
      setUpWithPath(resource, file.name, true, null, false, file);
      setSource(resource, 'file-selected');
      guessFormat(resource);
      rebuildPreviewOptionsSoon();
    });

    list.addEventListener('click', function (e) {
      var card = e.target.closest('[data-config-item]');
      var resource = card && cards.get(card);
      if (!resource) return;
      if (e.target.closest('[data-resource-dropbox]')) openDropbox(resource);
      if (e.target.closest('[data-resource-drive]')) openGoogleDrive(resource);
    });

    function clearErrors() {
      errorAlert.hidden = true;
      form.querySelectorAll('[aria-invalid="true"]').forEach(function (el) {
        window.hdxV2.setFieldError(el, '');
      });
      cards.forEach(showFormatWarning);
    }

    function targetFor(key) {
      var selector = ERROR_TARGETS[key] || '[name="' + key + '"]';
      var sections = form.querySelectorAll('[data-dataset-form-fields]');
      for (var i = 0; i < sections.length; i++) {
        var match = sections[i].querySelector(selector);
        if (match) return match;
      }
      return null;
    }

    function focusTarget() {
      var invalid = Array.from(form.querySelectorAll('[aria-invalid="true"]')).filter(function (el) {
        return !el.closest('[hidden]');
      })[0];
      if (!invalid) {
        if (!errorAlert.hidden) errorAlert.focus();
        return;
      }
      if (invalid.tagName === 'SELECT' && invalid.classList.contains('select2-hidden-accessible')) {
        invalid.closest('.c-dropdown').querySelector('.select2-selection').focus();
      } else if (invalid.type === 'file') {
        invalid.closest('[data-image-upload]').querySelector('[data-image-upload-choose]').focus();
      } else if (invalid.type === 'radio') {
        (form.querySelector('input[name="' + invalid.name + '"]:checked') || invalid).focus();
      } else {
        invalid.focus();
      }
    }

    function showResourceErrors(resourceErrors, fieldless) {
      var ordered = orderedResources();
      Object.keys(resourceErrors).forEach(function (label) {
        var index = Number(label.split(' ').pop());
        var resource = ordered[index];
        var fieldErrors = resourceErrors[label] || {};
        Object.keys(fieldErrors).forEach(function (field) {
          var text = messagesOf(fieldErrors[field]).join(', ');
          if (!resource) {
            fieldless.push(text);
            return;
          }
          var target = control(resource, field);
          if (!target || target.closest('[hidden]')) target = resource.card.querySelector('[data-image-upload-file]');
          window.hdxV2.setFieldError(target, text);
        });
      });
    }

    function showErrors(data) {
      var errors  = data.errors || {};
      var summary = data.error_summary || {};
      var fieldless = [];
      FIELDLESS_SUMMARY.forEach(function (key) {
        if (summary[key]) fieldless.push(summary[key]);
      });
      if (summary.Resources && typeof summary.Resources === 'object') {
        showResourceErrors(summary.Resources, fieldless);
      } else if (summary.Resources) {
        fieldless.push(summary.Resources);
      }
      Object.keys(errors).forEach(function (key) {
        if (key === 'resources') return;
        if (key === 'customviz') {
          var vizInputs = form.querySelectorAll('[data-custom-viz]');
          (errors.customviz || []).forEach(function (vizErrors, index) {
            var text = messagesOf(vizErrors).join(', ');
            if (!text) return;
            if (vizInputs[index]) window.hdxV2.setFieldError(vizInputs[index], text); else fieldless.push(text);
          });
          return;
        }
        var text = messagesOf(errors[key]).join(', ');
        if (!text) return;
        var target = targetFor(key);
        if (target && !target.closest('[hidden]')) {
          window.hdxV2.setFieldError(target, text);
        } else {
          fieldless.push(prettify(key) + ': ' + (summary[prettify(key)] || text));
        }
      });
      if (fieldless.length) showFieldless(fieldless);
      hideOverlay();
      focusTarget();
    }

    function hasErrors(data) {
      return Object.keys(data.errors || {}).length > 0 || Object.keys(data.error_summary || {}).length > 0;
    }

    function serverFailure() {
      showErrors({ error_summary: { server_or_connection_error: messages.serverError } });
    }

    function formValues(saveMode) {
      var values = [{ name: 'save', value: saveMode }];
      form.querySelectorAll('[data-dataset-form-fields]').forEach(function (section) {
        section.querySelectorAll('input, select, textarea').forEach(function (el) {
          if (!el.name || el.disabled) return;
          if (['file', 'submit', 'button', 'reset'].indexOf(el.type) !== -1) return;
          if ((el.type === 'checkbox' || el.type === 'radio') && !el.checked) return;
          if (el.tagName === 'SELECT') {
            Array.prototype.forEach.call(el.selectedOptions, function (option) {
              if (option.value) values.push({ name: el.name, value: option.value });
            });
            return;
          }
          var value = el.value.replace(/\r?\n/g, '\r\n');
          if (value) values.push({ name: el.name, value: value });
        });
      });
      return values;
    }

    function customVizValues() {
      var urls = Array.from(form.querySelectorAll('[data-custom-viz]')).map(function (input) { return input.value.trim(); });
      if (urls.length < 2 && !urls[0]) return [];
      return urls.map(function (url, index) { return { name: 'customviz__' + index + '__url', value: url }; });
    }

    function resourceValues() {
      var values = [];
      orderedResources().forEach(function (resource, index) {
        Object.keys(resource.attrs).forEach(function (key) {
          values.push({ name: 'resources__' + index + '__' + key, value: paramValue(resource.attrs[key]) });
        });
      });
      return values;
    }

    function validate(requestdata) {
      var values = formValues('validate-json');
      var hasResources = false;
      if (!requestdata) {
        var files = resourceValues();
        hasResources = files.length > 0;
        values = values.concat(files, customVizValues());
      }
      values.push({ name: 'id', value: datasetId || '' });
      return window.hdxV2.post(VALIDATE_URL, encode(values)).then(function (data) {
        if (data.aborted) return data;
        data.errors = data.errors || {};
        data.error_summary = data.error_summary || {};
        var dataset = data.data || {};
        if (!dataset.is_requestdata_type && !hasResources) {
          data.error_summary['resource-list'] = messages.atLeastOneFile;
        }
        if (dataset.is_requestdata_type && !(dataset.tag_string && dataset.tag_string.length)) {
          data.errors.tag_string = [messages.missingValue];
        }
        return data;
      });
    }

    function sendCreationEvent(values) {
      var mode = currentMode();
      var tags = values.filter(function (item) { return item.name === 'tag_string'; }).map(function (item) { return item.value; });
      var shaped = values.filter(function (item) {
        return ['private', 'tag_string'].indexOf(item.name) === -1;
      }).concat([
        { name: 'private', value: mode === 'private' ? 'true' : 'false' },
        { name: 'is_requestdata_type', value: mode === 'requestdata' ? 'true' : 'false' },
        { name: 'tag_string', value: tags.join(',') }
      ]);
      return new Promise(function (resolve) {
        var promise = window.hdxUtil.analytics.sendDatasetCreationEvent(shaped);
        if (promise && promise.then) promise.then(resolve, resolve); else resolve();
      });
    }

    function saveMetadata() {
      var values;
      var before;
      if (datasetId) {
        values = formValues('update-dataset-json');
        values.push({ name: 'id', value: datasetId });
        before = Promise.resolve();
      } else {
        values = formValues('new-dataset-json');
        before = sendCreationEvent(values);
      }
      values.push({ name: 'batch_mode', value: 'DONT_GROUP' });
      values = values.concat(customVizValues());
      return before.then(function () {
        showOverlay(messages.savingDataset);
        return window.hdxV2.post(requestUrl, encode(values));
      });
    }

    function showPrivateInfo(data) {
      var hidden = false;
      try { hidden = !!window.localStorage.getItem(PRIVATE_INFO_KEY); } catch (e) {}
      if (!data.data || !isTrue(data.data.private) || hidden) return Promise.resolve();
      var drawerEl = document.getElementById('private-dataset-info');
      hideOverlay();
      return new Promise(function (resolve) {
        drawerEl.addEventListener('drawer:close', function () {
          if (document.getElementById('private-dataset-info-hide').checked) {
            try { window.localStorage.setItem(PRIVATE_INFO_KEY, 'true'); } catch (e) {}
          }
          resolve();
        }, { once: true });
        window.hdxV2Drawer('private-dataset-info').open();
      });
    }

    function isChanged(resource) {
      return resource.savedHash !== hashResource(resource.attrs) || resource.savedPii !== isTrue(resource.attrs.pii);
    }

    function sendResource(resource, onProgress) {
      var attrs = resource.attrs;
      var url = attrs.id ? '/api/action/resource_update?id=' + encodeURIComponent(attrs.id) : '/api/action/resource_create';
      return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        var headers = window.hdxUtil.net.getCsrfTokenAsObject();
        Object.keys(headers).forEach(function (name) { xhr.setRequestHeader(name, headers[name]); });
        xhr.setRequestHeader('Accept', 'application/json');
        var body;
        if (attrs.upload instanceof File) {
          body = new FormData();
          flatten(attrs, '', []).forEach(function (pair) {
            if (pair[0] !== 'upload') body.append(pair[0], pair[1]);
          });
          body.append('upload', attrs.upload);
          xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) onProgress(Math.floor(e.loaded / e.total * 100));
          });
        } else {
          xhr.setRequestHeader('Content-Type', 'application/json');
          body = JSON.stringify(attrs);
        }
        xhr.onload = function () {
          var reply = null;
          try { reply = JSON.parse(xhr.responseText); } catch (e) { reply = null; }
          if (xhr.status >= 200 && xhr.status < 300 && reply && reply.success) resolve(reply.result);
          else reject({ reply: reply });
        };
        xhr.onerror = function () { reject({ reply: null }); };
        xhr.send(body);
      });
    }

    function saveResources(packageId) {
      var ordered = orderedResources();
      var total = ordered.length;
      return ordered.reduce(function (chain, resource, index) {
        return chain.then(function () {
          var values = { n: index + 1, total: total };
          showOverlay(fill(messages.savingFile, values));
          resource.attrs.package_id = packageId;
          resource.attrs.position = index;
          delete resource.attrs.fs_check_info;
          if (!isChanged(resource)) return null;
          var created = !resource.attrs.id;
          return sendResource(resource, function (percent) {
            overlayMessage.textContent = fill(messages.savingFileProgress, { n: index + 1, total: total, percent: percent });
          }).then(function (result) {
            Object.assign(resource.attrs, result || {});
            delete resource.attrs.upload;
            resource.savedHash = hashResource(resource.attrs);
            resource.savedPii = isTrue(resource.attrs.pii);
            if (created && resource.attrs.id) serverOrder.push(resource.attrs.id);
          }, function (failure) {
            failure.resource = resource;
            failure.fileNumber = index + 1;
            throw failure;
          });
        });
      }, Promise.resolve());
    }

    function deleteRemoved() {
      showOverlay(messages.almostDone);
      return removed.slice().reduce(function (chain, resource) {
        return chain.then(function () {
          return window.hdxV2.post('/api/action/resource_delete', { id: resource.attrs.id, batch_mode: 'DONT_GROUP' })
            .then(requireSuccess)
            .then(function () {
              removed.splice(removed.indexOf(resource), 1);
              serverOrder = serverOrder.filter(function (id) { return id !== resource.attrs.id; });
            });
        });
      }, Promise.resolve());
    }

    function reorder() {
      var order = orderedResources().map(function (resource) { return resource.attrs.id; });
      if (!datasetId || order.join(',') === serverOrder.join(',')) return Promise.resolve();
      return window.hdxV2.post('/api/action/package_resource_reorder', { id: datasetId, order: order, batch_mode: 'DONT_GROUP' })
        .then(requireSuccess)
        .then(function () { serverOrder = order; });
    }

    function fileFailure(failure) {
      var reply = failure.reply;
      var fieldless = [fill(messages.fileSaveError, { n: failure.fileNumber })];
      var fieldErrors = reply && reply.error ? Object.assign({}, reply.error) : {};
      delete fieldErrors.__type;
      delete fieldErrors.message;
      if (Object.keys(fieldErrors).length) {
        var resourceErrors = {};
        resourceErrors['Resource ' + (failure.fileNumber - 1)] = fieldErrors;
        showResourceErrors(resourceErrors, fieldless);
      } else if (reply && reply.error && reply.error.message) {
        fieldless.push(reply.error.message);
      }
      showFieldless(fieldless);
      hideOverlay();
      focusTarget();
    }

    function finish() {
      window.top.location.href = '/dataset/' + datasetName;
    }

    function save() {
      busy = true;
      clearErrors();
      showOverlay(messages.validating);
      var requestdata = currentMode() === 'requestdata';
      var done = function () { busy = false; };

      validate(requestdata)
        .then(function (data) {
          if (data.aborted) {
            showErrors({ error_summary: { server_or_connection_error: data.message || messages.serverError } });
            return done();
          }
          if (hasErrors(data)) {
            showErrors(data);
            return done();
          }
          return saveMetadata().then(function (saved) {
            if (saved.aborted) {
              showErrors({ error_summary: { server_or_connection_error: saved.message || messages.serverError } });
              return done();
            }
            if (hasErrors(saved)) {
              showErrors(saved);
              return done();
            }
            if (!datasetId && saved.data && saved.data.id) datasetId = saved.data.id;
            if (saved.data && saved.data.name) datasetName = saved.data.name;
            return showPrivateInfo(saved).then(function () {
              if (requestdata) return finish();
              return saveResources(datasetId)
                .then(deleteRemoved)
                .then(reorder)
                .then(finish, function (failure) {
                  if (failure && failure.fileNumber) fileFailure(failure); else serverFailure();
                  done();
                });
            });
          });
        })
        .catch(function () {
          serverFailure();
          done();
        });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy || submit.disabled) return;
      save();
    });

    form.querySelectorAll('input[name="private"]').forEach(function (radio) {
      radio.addEventListener('change', applyMode);
    });

    terms.addEventListener('change', refreshTerms);

    form.querySelectorAll('[data-other-for]').forEach(function (target) {
      window.hdxV2.wireReveal(document.getElementById(target.getAttribute('data-other-for')), target, {
        values: target.getAttribute('data-other-values').split(',')
      });
    });

    previewCheck.addEventListener('change', function () {
      previewField.hidden = !previewCheck.checked;
    });
    previewSelect.addEventListener('change', applyPreviewSelection);

    var startRoot = document.getElementById('ui_date_range1').closest('[data-date-picker]');
    var endRoot   = document.getElementById('ui_date_range2').closest('[data-date-picker]');
    var ongoing   = document.getElementById('ui_date_ongoing');
    startRoot.addEventListener('date-picker:change', function (e) {
      window.hdxV2DatePicker(endRoot).setMin(e.detail.value);
    });
    endRoot.addEventListener('date-picker:change', function (e) {
      window.hdxV2DatePicker(startRoot).setMax(e.detail.value);
    });
    ongoing.addEventListener('change', function () {
      window.hdxV2DatePicker(endRoot).setValue('');
      window.hdxV2DatePicker(endRoot).setDisabled(ongoing.checked);
      window.hdxV2DatePicker(startRoot).setMax('');
    });

    var titleInput      = document.getElementById('field_title');
    var orgSelect       = document.getElementById('field_owner_org');
    var tagSelect       = document.getElementById('field_tag_string');
    var suggestions     = form.querySelector('[data-tag-suggestions]');
    var suggestionsList = form.querySelector('[data-tag-suggestions-list]');
    var recommended     = null;

    function selectedTags() {
      return Array.from(tagSelect.selectedOptions).map(function (option) { return option.value.trim(); });
    }

    function renderSuggestions() {
      var current = selectedTags();
      var unused = (recommended || []).filter(function (tag) { return current.indexOf(tag) < 0; });
      suggestionsList.textContent = '';
      unused.forEach(function (tag, index) {
        if (index) suggestionsList.appendChild(document.createTextNode(', '));
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'hdx-v2-dataset-form__suggested-tag';
        button.textContent = tag;
        suggestionsList.appendChild(button);
      });
      suggestions.hidden = unused.length === 0;
    }

    var fetchSuggestions = window.hdxUtil.eventUtil.debouncer(function () {
      var title = titleInput.value;
      if (!title || title.length <= 3) {
        recommended = null;
        renderSuggestions();
        return;
      }
      var url = RECOMMEND_TAGS_URL + '?title=' + encodeURIComponent(title);
      if (orgSelect.value && orgSelect.value.length > 2) url += '&organization=' + encodeURIComponent(orgSelect.value);
      fetch(url)
        .then(function (response) { return response.json(); })
        .then(function (reply) {
          if (!reply.success) return;
          recommended = reply.result.map(function (tag) { return tag.name; });
          renderSuggestions();
        })
        .catch(function () {});
    }, 1000);

    suggestionsList.addEventListener('click', function (e) {
      var button = e.target.closest('button');
      if (!button) return;
      var tag = button.textContent;
      var current = selectedTags();
      if (current.indexOf(tag) >= 0) return;
      jQuery(tagSelect).val(current.concat(tag)).trigger('change');
      window.hdxUtil.analytics.sendLinkClickEvent({ destinationUrl: '#', linkType: 'dataset recommended tag' });
    });

    titleInput.addEventListener('input', fetchSuggestions);
    titleInput.addEventListener('change', fetchSuggestions);
    jQuery(orgSelect).on('change', fetchSuggestions);
    jQuery(tagSelect).on('change', renderSuggestions);

    var suggestLink = form.querySelector('[data-dataset-form-suggest-tag]');
    var tagsForm    = document.querySelector('[data-request-tags-form]');
    suggestLink.addEventListener('click', function (e) {
      e.preventDefault();
      tagsForm.querySelector('[data-request-tags-error]').hidden = true;
      tagsForm.querySelector('[data-request-tags-success]').hidden = true;
      window.hdxV2Drawer('request-tags-drawer').open();
    });

    tagsForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var errorEl   = tagsForm.querySelector('[data-request-tags-error]');
      var successEl = tagsForm.querySelector('[data-request-tags-success]');
      errorEl.hidden = true;
      successEl.hidden = true;
      tagsForm.querySelectorAll('[name]').forEach(function (field) { window.hdxV2.setFieldError(field, ''); });
      window.hdxV2.post(tagsForm.getAttribute('action'), new URLSearchParams(new FormData(tagsForm)))
        .then(function (result) {
          if (result.success) {
            tagsForm.reset();
            successEl.hidden = false;
            return;
          }
          var fields = result.error && result.error.fields;
          if (fields && Object.keys(fields).length) {
            Object.keys(fields).forEach(function (name) {
              var field = tagsForm.querySelector('[name="' + name + '"]');
              if (field) window.hdxV2.setFieldError(field, messagesOf(fields[name]).join(', '));
            });
            var first = tagsForm.querySelector('[aria-invalid="true"]');
            if (first) first.focus();
          } else {
            window.hdxV2.showAlert(errorEl, fill(tagsForm.getAttribute('data-error-message'), { message: result.error ? result.error.message : '' }));
          }
        })
        .catch(function () {
          window.hdxV2.showAlert(errorEl, tagsForm.getAttribute('data-network-error'));
        });
    });

    var deleteButton = form.querySelector('[data-dataset-form-delete]');
    var deleteForm   = document.querySelector('[data-dataset-form-delete-form]');
    if (deleteButton && deleteForm) {
      deleteButton.addEventListener('click', function () {
        window.hdxV2Drawer('delete-dataset-drawer').open();
      });
      deleteForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var errorEl = deleteForm.querySelector('[data-dataset-form-delete-error]');
        errorEl.hidden = true;
        window.hdxV2.post(deleteForm.getAttribute('data-url'), { id: deleteForm.getAttribute('data-dataset-id') })
          .then(requireSuccess)
          .then(function () {
            window.top.location = form.getAttribute('data-search-url');
          })
          .catch(function (error) {
            var message = error.reply && error.reply.error && error.reply.error.message ? error.reply.error.message : '';
            window.hdxV2.showAlert(errorEl, fill(deleteForm.getAttribute('data-error-message'), { message: message }));
          });
      });
    }

    if (window.FilePicker) {
      googlePicker = new window.FilePicker(Object.assign({
        onSelect: function (url, filename) {
          if (pickerTarget) cloudFileSelected(pickerTarget, url, filename);
        }
      }, GOOGLE_DRIVE));
    }

    applyMode();
    refreshTerms();
    loadResources();
    fetchSuggestions();
  }

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.querySelector('[data-dataset-form]');
    if (form) init(form);
  });
})();
