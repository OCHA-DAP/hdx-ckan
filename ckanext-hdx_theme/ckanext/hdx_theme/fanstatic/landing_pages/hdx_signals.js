document.addEventListener('DOMContentLoaded', function () {

  var formCard = document.querySelector('.hdx-v2-signals-form-card');
  if (!formCard) { return; }
  var form = formCard.querySelector('form');
  var button = form.querySelector('#mc-embedded-subscribe');
  var alert = form.querySelector('#mc-embedded-subscribe-alert');
  var fields = Array.from(form.querySelectorAll('#mce-EMAIL, #mce-FNAME, #mce-ORG'));

  var DATASETS_GROUPS = [
    '[4389]'
  ];
  var LOCATIONS_GROUPS = [
    '[4397]',
    '[4405]',
    '[4417]',
    '[4409]',
    '[4401]',
    '[4421]',
    '[4425]'
  ];
  var DATASETS_LOCATIONS_GROUPS = DATASETS_GROUPS.concat(LOCATIONS_GROUPS);

  var ALL_LOCATIONS = [
    '[4397][16384]',
    '[4405][8388608]',
    '[4417][8589934592]',
    '[4409][33554432]',
    '[4401][65536]',
    '[4421][549755813888]',
    '[4425][16]',
  ];
  var HRP_LOCATIONS = [
    '[4397][32768]',
    '[4397][131072]',
    '[4405][16777216]',
    '[4417][17179869184]',
    '[4417][34359738368]',
    '[4417][68719476736]',
    '[4417][137438953472]',
    '[4417][274877906944]',
    '[4417][4]',
    '[4409][67108864]',
    '[4409][134217728]',
    '[4409][268435456]',
    '[4401][524288]',
    '[4401][2097152]',
    '[4401][4194304]',
    '[4401][1]',
    '[4401][2]',
    '[4421][1099511627776]',
    '[4421][2199023255552]',
    '[4421][4398046511104]',
    '[4421][8796093022208]',
    '[4421][17592186044416]',
    '[4421][35184372088832]',
    '[4421][70368744177664]',
    '[4421][8]',
  ];

  function select_groups(groups) {
    groups.forEach(function (group) {
      form.querySelectorAll('input[name^="group' + group + '"]').forEach(function (cb) {
        cb.checked = true;
      });
    });
    disable_submit_button();
  }

  function unselect_group(groups) {
    groups.forEach(function (group) {
      form.querySelectorAll('input[name^="group' + group + '"]').forEach(function (cb) {
        cb.checked = false;
      });
    });
    disable_submit_button();
  }

  function select_values(values) {
    values.forEach(function (value) {
      var cb = form.querySelector('input[name="group' + value + '"]');
      if (cb) { cb.checked = true; }
    });
    disable_submit_button();
  }

  function unselect_values(values) {
    values.forEach(function (value) {
      var cb = form.querySelector('input[name="group' + value + '"]');
      if (cb) { cb.checked = false; }
    });
    disable_submit_button();
  }

  function add_select_buttons(group_label, group) {
    var select_btn = document.createElement('button');
    select_btn.type = 'button';
    select_btn.className = 'c-button c-button--tertiary c-button--size-s';
    select_btn.textContent = 'Select all';

    var unselect_btn = document.createElement('button');
    unselect_btn.type = 'button';
    unselect_btn.className = 'c-button c-button--tertiary c-button--size-s';
    unselect_btn.textContent = 'Clear all';

    group_label.appendChild(select_btn);
    group_label.appendChild(unselect_btn);

    select_btn.addEventListener('click', function () {
      select_groups([group]);
    });
    unselect_btn.addEventListener('click', function () {
      unselect_group([group]);
    });
  }

  function disable_submit_button() {
    var dataset_checked = DATASETS_GROUPS.some(function (group) {
      return form.querySelectorAll('input[name^="group' + group + '"]:checked').length > 0;
    });

    var location_checked = LOCATIONS_GROUPS.some(function (group) {
      return form.querySelectorAll('input[name^="group' + group + '"]:checked').length > 0;
    });

    var fields_filled = fields.every(function(field) {
      return field.value.trim() !== '';
    });

    if(dataset_checked && location_checked && fields_filled) {
      button.classList.remove('is-disabled');
      button.removeAttribute('disabled');
      button.removeAttribute('aria-disabled');
      alert.style.display = 'none';
    }
    else {
      button.classList.add('is-disabled');
      button.setAttribute('disabled', 'disabled');
      button.setAttribute('aria-disabled', 'true');
      alert.style.display = '';
    }
  }

  var selectAllLocations = form.querySelector('#select-all-locations');
  if (selectAllLocations) {
    selectAllLocations.addEventListener('click', function () {
      select_values(ALL_LOCATIONS);
    });
  }
  var selectAllHrp = form.querySelector('#select-all-hrp-locations');
  if (selectAllHrp) {
    selectAllHrp.addEventListener('click', function () {
      select_values(HRP_LOCATIONS);
    });
  }
  var clearAllLocations = form.querySelector('#clear-all-locations');
  if (clearAllLocations) {
    clearAllLocations.addEventListener('click', function () {
      unselect_values(ALL_LOCATIONS);
      unselect_values(HRP_LOCATIONS);
    });
  }

  form.querySelectorAll('.mc-field-group').forEach(function (group_el) {
    var group_label = group_el.querySelector('p.action-buttons');
    var first_cb = group_el.querySelector('input[type="checkbox"]');

    if (group_label && first_cb) {
      var group = first_cb.name.split('[')[1].split(']')[0];
      add_select_buttons(group_label, '[' + group + ']');
    }
  });

  DATASETS_LOCATIONS_GROUPS.forEach(function (group) {
    form.querySelectorAll('input[name^="group' + group + '"]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        disable_submit_button();
      });
    });
  });

  fields.forEach(function(field) {
    field.addEventListener('input', function() {
      disable_submit_button();
    });
  });

});
