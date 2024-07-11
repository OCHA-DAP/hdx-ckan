$(document).ready(function () {
  var $form = $('#mc_embed_signup form');
  var DATASETS_GROUP = '[4389]';
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

  function select_group(group) {
    $form.find('input[name^="group' + group + '"]').prop('checked', true);
  }

  function unselect_group(group) {
    $form.find('input[name^="group' + group + '"]').prop('checked', false);
  }

  function select_values(values) {
    values.forEach(function (value) {
      $form.find('input[name="group' + value + '"]').prop('checked', true);
    });
  }

  function add_select_buttons(group_label, group) {
    var select_btn = $('<button type="button" class="btn btn-link p-0 me-2"><small>Select all</small></button>');
    var unselect_btn = $('<button type="button" class="btn btn-link p-0"><small>Select none</small></button>');

    group_label.append(select_btn);
    group_label.append(unselect_btn);

    select_btn.click(function () {
      select_group(group);
    });
    unselect_btn.click(function () {
      unselect_group(group);
    });
  }

  $form.find('#select-all').click(function () {
    select_group(DATASETS_GROUP);
    select_values(ALL_LOCATIONS);
  });
  $form.find('#select-all-datasets').on('click', function () {
    select_group(DATASETS_GROUP);
  });
  $form.find('#select-all-locations').on('click', function () {
    select_values(ALL_LOCATIONS);
  });
  $form.find('#select-all-hrp-locations').on('click', function () {
    select_values(HRP_LOCATIONS);
  });

  $form.find('.mc-field-group').each(function () {
    var group_label = $(this).find('p.action-buttons');
    var group_name = $(this).find('input[type="checkbox"]').first().attr('name');

    if (group_label.length && group_name) {
      var group = group_name.split('[')[1].split(']')[0];
      add_select_buttons(group_label, '[' + group + ']');
    }
  });

});
