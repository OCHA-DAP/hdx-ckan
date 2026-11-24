(function () {
  'use strict';

  var LOCALE      = 'en-US';
  var WEEK_START  = new Date(2023, 0, 1);
  var controllers = [];

  function parseIso(value) {
    var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '');
    if (!match) return null;
    var date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    return date.getMonth() === Number(match[2]) - 1 ? date : null;
  }

  function toIso(date) {
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
  }

  function sameDay(a, b) {
    return !!a && !!b && toIso(a) === toIso(b);
  }

  function addDays(date, days) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
  }

  function addMonths(date, months) {
    var target = new Date(date.getFullYear(), date.getMonth() + months, 1);
    var last   = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate();
    return new Date(target.getFullYear(), target.getMonth(), Math.min(date.getDate(), last));
  }

  function format(date, options) {
    return date.toLocaleDateString(LOCALE, options);
  }

  function init(root) {
    var trigger = root.querySelector('[data-date-picker-trigger]');
    var display = root.querySelector('[data-date-picker-display]');
    var input   = root.querySelector('[data-date-picker-input]');
    var panel   = root.querySelector('[data-date-picker-panel]');
    var prev    = root.querySelector('[data-date-picker-prev]');
    var next    = root.querySelector('[data-date-picker-next]');
    var title   = root.querySelector('[data-date-picker-title]');
    var days    = root.querySelector('[data-date-picker-days]');
    var months  = root.querySelector('[data-date-picker-months]');
    var view    = 'day';
    var cursor  = null;

    function limit(name) {
      return parseIso(root.getAttribute('data-date-picker-' + name));
    }

    function outOfRange(date) {
      var lo = limit('min');
      var hi = limit('max');
      return !!((lo && date < lo) || (hi && date > hi));
    }

    function monthOutOfRange(year, month) {
      var lo = limit('min');
      var hi = limit('max');
      return !!((lo && new Date(year, month + 1, 0) < lo) || (hi && new Date(year, month, 1) > hi));
    }

    function yearOutOfRange(year) {
      var lo = limit('min');
      var hi = limit('max');
      return !!((lo && new Date(year, 11, 31) < lo) || (hi && new Date(year, 0, 1) > hi));
    }

    function clamp(date) {
      var lo = limit('min');
      var hi = limit('max');
      if (lo && date < lo) return lo;
      if (hi && date > hi) return hi;
      return date;
    }

    function updateDisplay() {
      var date = parseIso(input.value);
      display.textContent = date
        ? format(date, { month: 'long', day: 'numeric', year: 'numeric' })
        : root.getAttribute('data-date-picker-placeholder');
      root.classList.toggle('c-date-picker--filled', !!date);
    }

    function setNav(direction) {
      [prev, next].forEach(function (button) {
        button.setAttribute('aria-label', button.getAttribute('data-label-' + view));
      });
      var year  = cursor.getFullYear();
      var month = cursor.getMonth();
      prev.disabled = view === 'day' ? monthOutOfRange(year, month - 1) : yearOutOfRange(year - 1);
      next.disabled = view === 'day' ? monthOutOfRange(year, month + 1) : yearOutOfRange(year + 1);
      if (direction && document.activeElement && document.activeElement.disabled) title.focus();
    }

    function renderDays() {
      var year     = cursor.getFullYear();
      var month    = cursor.getMonth();
      var selected = parseIso(input.value);
      var today    = new Date();
      var first    = new Date(year, month, 1);
      var total    = new Date(year, month + 1, 0).getDate();

      title.textContent = format(first, { month: 'long', year: 'numeric' });
      title.setAttribute('aria-label', title.getAttribute('data-label-day') + ', ' + title.textContent);
      days.textContent = '';

      var head = days.createTHead().insertRow();
      for (var w = 0; w < 7; w++) {
        var weekday = addDays(WEEK_START, w);
        var th = document.createElement('th');
        th.scope = 'col';
        th.abbr = format(weekday, { weekday: 'long' });
        th.textContent = format(weekday, { weekday: 'short' }).slice(0, 2);
        head.appendChild(th);
      }

      var body = days.createTBody();
      var row  = null;
      for (var cell = 0; cell < first.getDay() + total; cell++) {
        if (cell % 7 === 0) row = body.insertRow();
        var td = row.insertCell();
        td.setAttribute('role', 'gridcell');
        if (cell < first.getDay()) continue;
        var date   = new Date(year, month, cell - first.getDay() + 1);
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'c-date-picker__day';
        button.textContent = String(date.getDate());
        button.setAttribute('data-date', toIso(date));
        button.setAttribute('aria-label', format(date, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }));
        button.tabIndex = sameDay(date, cursor) ? 0 : -1;
        button.disabled = outOfRange(date);
        if (sameDay(date, today)) button.setAttribute('aria-current', 'date');
        if (sameDay(date, selected)) {
          button.classList.add('is-active');
          td.setAttribute('aria-selected', 'true');
        }
        td.appendChild(button);
      }
      while (row && row.cells.length < 7) row.insertCell().setAttribute('role', 'gridcell');
    }

    function renderMonths() {
      var year     = cursor.getFullYear();
      var selected = parseIso(input.value);
      title.textContent = String(year);
      title.setAttribute('aria-label', title.getAttribute('data-label-month') + ', ' + year);
      months.textContent = '';
      for (var m = 0; m < 12; m++) {
        var first  = new Date(year, m, 1);
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'c-dropdown-calendar__month-btn';
        button.textContent = format(first, { month: 'short' });
        button.setAttribute('data-month', String(m));
        button.setAttribute('aria-label', format(first, { month: 'long', year: 'numeric' }));
        button.tabIndex = m === cursor.getMonth() ? 0 : -1;
        button.disabled = monthOutOfRange(year, m);
        if (selected && selected.getFullYear() === year && selected.getMonth() === m) {
          button.classList.add('is-active');
          button.setAttribute('aria-pressed', 'true');
        }
        months.appendChild(button);
      }
    }

    function render(direction) {
      days.hidden   = view !== 'day';
      months.hidden = view !== 'month';
      if (view === 'day') renderDays(); else renderMonths();
      setNav(direction);
    }

    function focusCursor() {
      var target = view === 'day'
        ? days.querySelector('[data-date="' + toIso(cursor) + '"]')
        : months.querySelector('[data-month="' + cursor.getMonth() + '"]');
      if (target && !target.disabled) {
        target.focus();
      } else {
        title.focus();
      }
    }

    function open() {
      if (trigger.disabled) return;
      cursor = clamp(parseIso(input.value) || new Date());
      view = 'day';
      render();
      panel.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      focusCursor();
    }

    function close(returnFocus) {
      if (panel.hidden) return;
      panel.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      if (returnFocus) trigger.focus();
    }

    function choose(date) {
      input.value = toIso(date);
      updateDisplay();
      close(true);
      root.dispatchEvent(new CustomEvent('date-picker:change', { bubbles: true, detail: { value: input.value } }));
    }

    function moveCursor(date) {
      var target = clamp(date);
      var redraw = view === 'day'
        ? target.getFullYear() !== cursor.getFullYear() || target.getMonth() !== cursor.getMonth()
        : target.getFullYear() !== cursor.getFullYear();
      cursor = target;
      if (redraw) {
        render();
      } else {
        (view === 'day' ? days : months).querySelectorAll('button').forEach(function (button) {
          button.tabIndex = -1;
        });
      }
      var focused = view === 'day'
        ? days.querySelector('[data-date="' + toIso(cursor) + '"]')
        : months.querySelector('[data-month="' + cursor.getMonth() + '"]');
      if (focused) focused.tabIndex = 0;
      focusCursor();
    }

    trigger.addEventListener('click', function () {
      if (panel.hidden) open(); else close(true);
    });

    prev.addEventListener('click', function () {
      cursor = clamp(view === 'day' ? addMonths(cursor, -1) : addMonths(cursor, -12));
      render('prev');
    });

    next.addEventListener('click', function () {
      cursor = clamp(view === 'day' ? addMonths(cursor, 1) : addMonths(cursor, 12));
      render('next');
    });

    title.addEventListener('click', function () {
      view = view === 'day' ? 'month' : 'day';
      render();
      focusCursor();
    });

    days.addEventListener('click', function (e) {
      var button = e.target.closest('[data-date]');
      if (button && !button.disabled) choose(parseIso(button.getAttribute('data-date')));
    });

    months.addEventListener('click', function (e) {
      var button = e.target.closest('[data-month]');
      if (!button || button.disabled) return;
      var month = Number(button.getAttribute('data-month'));
      var last  = new Date(cursor.getFullYear(), month + 1, 0).getDate();
      cursor = clamp(new Date(cursor.getFullYear(), month, Math.min(cursor.getDate(), last)));
      view = 'day';
      render();
      focusCursor();
    });

    days.addEventListener('keydown', function (e) {
      if (!e.target.closest('[data-date]')) return;
      var weekday = cursor.getDay();
      var moves = {
        ArrowLeft:  function () { return addDays(cursor, -1); },
        ArrowRight: function () { return addDays(cursor, 1); },
        ArrowUp:    function () { return addDays(cursor, -7); },
        ArrowDown:  function () { return addDays(cursor, 7); },
        Home:       function () { return addDays(cursor, -weekday); },
        End:        function () { return addDays(cursor, 6 - weekday); },
        PageUp:     function () { return addMonths(cursor, e.shiftKey ? -12 : -1); },
        PageDown:   function () { return addMonths(cursor, e.shiftKey ? 12 : 1); }
      };
      if (!moves[e.key]) return;
      e.preventDefault();
      moveCursor(moves[e.key]());
    });

    months.addEventListener('keydown', function (e) {
      if (!e.target.closest('[data-month]')) return;
      var steps = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -3, ArrowDown: 3 };
      if (!(e.key in steps)) return;
      e.preventDefault();
      moveCursor(addMonths(cursor, steps[e.key]));
    });

    panel.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      e.stopPropagation();
      close(true);
    });

    root.addEventListener('focusout', function () {
      setTimeout(function () {
        if (!root.contains(document.activeElement)) close(false);
      }, 0);
    });

    updateDisplay();

    controllers.push({
      root: root,
      api: {
        setValue: function (iso) {
          input.value = parseIso(iso) ? iso : '';
          updateDisplay();
        },
        setMin: function (iso) { root.setAttribute('data-date-picker-min', iso || ''); },
        setMax: function (iso) { root.setAttribute('data-date-picker-max', iso || ''); },
        setDisabled: function (disabled) {
          window.hdxV2.setDisabled(trigger, disabled);
          if (disabled) close(false);
        }
      }
    });
  }

  window.hdxV2DatePicker = function (root) {
    var match = controllers.filter(function (controller) { return controller.root === root; })[0];
    return match ? match.api : null;
  };

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-date-picker]').forEach(init);
  });
})();
