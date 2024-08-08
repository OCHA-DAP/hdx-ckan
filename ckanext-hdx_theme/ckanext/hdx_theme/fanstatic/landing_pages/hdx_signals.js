$(document).ready(function () {

  var $form = $('#signals-form-card form');
  var $button = $form.find('#mc-embedded-subscribe');
  var $alert = $form.find('#mc-embedded-subscribe-alert');
  var $fields = $form.find('#mce-EMAIL, #mce-FNAME, #mce-ORG');

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
      $form.find('input[name^="group' + group + '"]').prop('checked', true);
    });
    disable_submit_button();
  }

  function unselect_group(groups) {
    groups.forEach(function (group) {
      $form.find('input[name^="group' + group + '"]').prop('checked', false);
    });
    disable_submit_button();
  }

  function select_values(values) {
    values.forEach(function (value) {
      $form.find('input[name="group' + value + '"]').prop('checked', true);
    });
    disable_submit_button();
  }

  function unselect_values(values) {
    values.forEach(function (value) {
      $form.find('input[name="group' + value + '"]').prop('checked', false);
    });
    disable_submit_button();
  }

  function add_select_buttons(group_label, group) {
    var select_btn = $('<button type="button" class="btn btn-link p-0 me-2"><small>Select all</small></button>');
    var unselect_btn = $('<button type="button" class="btn btn-link p-0"><small>Clear all</small></button>');

    group_label.append(select_btn);
    group_label.append(unselect_btn);

    select_btn.click(function () {
      select_groups([group]);
    });
    unselect_btn.click(function () {
      unselect_group([group]);
    });
  }

  function disable_submit_button() {
    var dataset_checked = DATASETS_GROUPS.some(function (group) {
      return $form.find('input[name^="group' + group + '"]:checked').length > 0;
    });

    var location_checked = LOCATIONS_GROUPS.some(function (group) {
      return $form.find('input[name^="group' + group + '"]:checked').length > 0;
    });

    var fields_filled = $fields.toArray().every(function(field) {
      return $(field).val().trim() !== '';
    });

    if(dataset_checked && location_checked && fields_filled) {
      $button.removeClass('disabled').removeAttr('disabled');
      $alert.addClass('d-none');
    }
    else {
      $button.addClass('disabled').attr('disabled', 'disabled');
      $alert.removeClass('d-none');
    }
  }

  $form.find('#select-all-datasets').on('click', function () {
    select_groups(DATASETS_GROUPS);
  });
  $form.find('#select-all-locations').on('click', function () {
    select_values(ALL_LOCATIONS);
  });
  $form.find('#select-all-hrp-locations').on('click', function () {
    select_values(HRP_LOCATIONS);
  });
  $form.find('#clear-all-locations').on('click', function () {
    unselect_values(ALL_LOCATIONS);
    unselect_values(HRP_LOCATIONS);
  });

  $form.find('.mc-field-group').each(function () {
    var group_label = $(this).find('p.action-buttons');
    var group_name = $(this).find('input[type="checkbox"]').first().attr('name');

    if (group_label.length && group_name) {
      var group = group_name.split('[')[1].split(']')[0];
      add_select_buttons(group_label, '[' + group + ']');
    }
  });

  DATASETS_LOCATIONS_GROUPS.forEach(function (group) {
    $form.find('input[name^="group' + group + '"]').on('change', function () {
      disable_submit_button();
    });
  });

  $fields.on('input', function() {
    disable_submit_button();
  });

});
