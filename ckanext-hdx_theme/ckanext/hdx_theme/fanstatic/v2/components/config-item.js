(function () {
  'use strict';

  function init(list) {
    var items      = list.querySelector('.c-config-item-list__items');
    var template   = list.querySelector('[data-config-item-template]');
    var alertEl    = list.querySelector('[data-config-item-error]');
    var addButton  = list.querySelector('[data-config-item-add]');
    var saveButton = list.querySelector('[data-config-item-save]');
    var counter    = items.children.length;
    var deletedIds = [];
    var knownIds   = cards().map(function (card) { return card.dataset.configItemId; }).filter(Boolean);

    function cards() {
      return Array.from(items.querySelectorAll('[data-config-item]'));
    }

    function renumber() {
      cards().forEach(function (card, index) {
        card.querySelector('[data-config-item-title]').textContent =
          list.dataset.titleFormat.replace('{n}', index + 1);
      });
    }

    function setExpanded(card, expanded) {
      card.querySelector('[data-config-item-toggle]').setAttribute('aria-expanded', String(expanded));
      card.querySelector('.c-config-item__body').hidden = !expanded;
    }

    function acceptReply(reply) {
      if (!Array.isArray(reply)) throw new Error('Unexpected reply');
      var previousIds = knownIds;
      knownIds = reply.map(function (item) { return item.id; });
      return knownIds.filter(function (id) { return previousIds.indexOf(id) === -1; });
    }

    function deleteItem(id) {
      return window.hdxV2.post(list.dataset.deleteUrl.replace('__id__', encodeURIComponent(id)))
        .then(function (reply) {
          acceptReply(reply);
          deletedIds.splice(deletedIds.indexOf(id), 1);
        });
    }

    function updateItem(card, order) {
      var body = new FormData();
      card.querySelector('.c-config-item__body').querySelectorAll('[name]').forEach(function (control) {
        body.append(control.name, control.value);
      });
      body.append('order', order);
      if (card.dataset.configItemId) body.append('id', card.dataset.configItemId);
      return window.hdxV2.post(list.dataset.updateUrl, body).then(function (reply) {
        var addedIds = acceptReply(reply);
        if (card.dataset.configItemId) return;
        if (addedIds.length !== 1) throw new Error('Unexpected reply');
        card.setAttribute('data-config-item-id', addedIds[0]);
      });
    }

    function save() {
      var invalid = [];
      alertEl.hidden = true;
      cards().forEach(function (card) {
        card.querySelectorAll('[required]').forEach(function (control) {
          var empty = !control.value.trim();
          window.hdxV2.setFieldError(control, empty ? control.dataset.requiredMessage : '');
          if (empty) {
            invalid.push(control);
            setExpanded(card, true);
          }
        });
      });
      if (invalid.length) {
        invalid[0].focus();
        return;
      }

      window.hdxV2.setDisabled(saveButton, true);
      var chain = Promise.resolve();
      deletedIds.slice().forEach(function (id) {
        chain = chain.then(function () { return deleteItem(id); });
      });
      cards().forEach(function (card, index) {
        chain = chain.then(function () { return updateItem(card, index + 1); });
      });
      chain
        .then(function () { window.location.reload(); })
        .catch(function () {
          window.hdxV2.showAlert(alertEl, list.dataset.errorMessage);
          window.hdxV2.setDisabled(saveButton, false);
        });
    }

    Sortable.create(items, {
      handle: '.c-config-item__header',
      animation: window.hdxV2.prefersReducedMotion() ? 0 : 250,
      ghostClass: 'is-dragging',
      onUpdate: renumber
    });

    items.addEventListener('click', function (e) {
      var toggle = e.target.closest('[data-config-item-toggle]');
      if (toggle) {
        setExpanded(toggle.closest('[data-config-item]'), toggle.getAttribute('aria-expanded') !== 'true');
        return;
      }
      var deleteButton = e.target.closest('[data-config-item-delete]');
      if (!deleteButton) return;
      var card = deleteButton.closest('[data-config-item]');
      var row = card.parentElement;
      var next = row.nextElementSibling;
      if (card.dataset.configItemId) deletedIds.push(card.dataset.configItemId);
      row.remove();
      renumber();
      (next ? next.querySelector('[data-config-item-toggle]') : addButton).focus();
    });

    items.addEventListener('input', function (e) {
      window.hdxV2.setFieldError(e.target, '');
    });

    addButton.addEventListener('click', function () {
      counter += 1;
      items.insertAdjacentHTML('beforeend', template.innerHTML.replace(/__index__/g, counter));
      renumber();
      items.lastElementChild.querySelector('.c-search-input input, .c-search-input textarea').focus();
    });

    saveButton.addEventListener('click', save);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-config-item-list]').forEach(init);
  });
})();
