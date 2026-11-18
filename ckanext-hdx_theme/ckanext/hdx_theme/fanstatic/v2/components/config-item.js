(function () {
  'use strict';

  var controllers = [];

  function init(list) {
    var items      = list.querySelector('.c-config-item-list__items');
    var template   = list.querySelector('[data-config-item-template]');
    var alertEl    = list.querySelector('[data-config-item-error]');
    var addButton  = list.querySelector('[data-config-item-add]');
    var saveButton = list.querySelector('[data-config-item-save]');
    var statusEl   = list.querySelector('[data-config-item-status]');
    var formMode   = list.hasAttribute('data-config-item-form');
    var sortable   = !formMode || list.hasAttribute('data-config-item-sortable');
    var addAtStart = list.getAttribute('data-config-item-add-position') === 'start';
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

    function refreshMove() {
      var all = cards();
      all.forEach(function (card, index) {
        var up = card.querySelector('[data-config-item-move="up"]');
        if (!up) return;
        window.hdxV2.setDisabled(up, index === 0);
        window.hdxV2.setDisabled(card.querySelector('[data-config-item-move="down"]'), index === all.length - 1);
      });
    }

    function announce(type, detail) {
      list.dispatchEvent(new CustomEvent('config-item:' + type, { bubbles: true, detail: detail || {} }));
    }

    function move(button) {
      var card    = button.closest('[data-config-item]');
      var row     = card.parentElement;
      var up      = button.getAttribute('data-config-item-move') === 'up';
      var sibling = up ? row.previousElementSibling : row.nextElementSibling;
      if (up) {
        sibling.before(row);
      } else {
        sibling.after(row);
      }
      renumber();
      refreshMove();
      (button.disabled ? card.querySelector('[data-config-item-move]:not(:disabled)') : button).focus();
      var all = cards();
      statusEl.textContent = list.dataset.moveMessage
        .replace('{n}', all.indexOf(card) + 1)
        .replace('{total}', all.length);
      announce('sort');
    }

    function setExpanded(card, expanded) {
      var toggle = card.querySelector('[data-config-item-toggle]');
      if (toggle) toggle.setAttribute('aria-expanded', String(expanded));
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
        if (control.type !== 'file') {
          body.append(control.name, control.value);
        } else if (control.files[0]) {
          body.append(control.name, control.files[0]);
        }
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

    if (sortable) {
      Sortable.create(items, {
        handle: '.c-config-item__header',
        animation: window.hdxV2.prefersReducedMotion() ? 0 : 250,
        ghostClass: 'is-dragging',
        onUpdate: function () {
          renumber();
          refreshMove();
          announce('sort');
        }
      });
    }

    items.addEventListener('click', function (e) {
      var toggle = e.target.closest('[data-config-item-toggle]');
      if (toggle) {
        setExpanded(toggle.closest('[data-config-item]'), toggle.getAttribute('aria-expanded') !== 'true');
        return;
      }
      var moveButton = e.target.closest('[data-config-item-move]');
      if (moveButton) {
        move(moveButton);
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
      refreshMove();
      (next ? next.querySelector('[data-config-item-toggle]') || next.querySelector('[data-config-item-title]') : addButton).focus();
      announce('remove', { item: card });
    });

    items.addEventListener('input', function (e) {
      window.hdxV2.setFieldError(e.target, '');
    });

    function add(options) {
      options = options || {};
      var atStart = options.position ? options.position === 'start' : addAtStart;
      counter += 1;
      items.insertAdjacentHTML(atStart ? 'afterbegin' : 'beforeend', template.innerHTML.replace(/__index__/g, counter));
      var row  = atStart ? items.firstElementChild : items.lastElementChild;
      var card = row.querySelector('[data-config-item]');
      renumber();
      refreshMove();
      if (options.prepare) options.prepare(card);
      card.dispatchEvent(new CustomEvent('config-item:add', { bubbles: true }));
      if (options.focus !== false) {
        row.querySelector(formMode
          ? '.c-config-item__body :is(input:not([type="hidden"]), select, textarea):not(:disabled)'
          : '.c-search-input input, .c-search-input textarea').focus();
      }
      return card;
    }

    addButton.addEventListener('click', function () { add(); });

    if (!formMode) saveButton.addEventListener('click', save);
    refreshMove();
    controllers.push({ list: list, api: { add: add } });
  }

  window.hdxV2ConfigItem = function (list) {
    var match = controllers.filter(function (controller) { return controller.list === list; })[0];
    return match ? match.api : null;
  };

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-config-item-list]').forEach(init);
  });
})();
