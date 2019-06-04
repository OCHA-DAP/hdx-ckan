$(document).ready(function(){
  $("select").select2();

  //make sure World is always first
  $('#country-drop>option:contains(World)').insertAfter('#country-drop>option[value=-1]');

  $('#country-drop').change(function(){
    var country = $('#country-drop option:selected').val();
    var country_name = $('#country-drop option:selected').attr('display_name');
    if($('#'+country).length == 0){
      var number_of_groups = $('.group_checked').length;
      var flag = 1;
      //Add country
      if(country != '-1'){
        // If any tags are shown
        if (number_of_groups) {
          // Do not add if already added
          $('.group_checked').each(function() {
            var tagval = $(this).attr('value');
            if (country == tagval) {
              flag = 0;
              // console.log('i already got ' + tagval + ' ... Not adding it again.');
            }
          });
        }
        if (flag) {
          $('#selected_groups').append('<span class="filtered pill">'+country_name+' <i id="field-group-'+country+'" name="groups__'+(number_of_groups)+'__id" value="'+country+'" class="group_checked glyphicon glyphicon-remove"/></span>');
          // //Add to solr_additions
          // var additions = $('#field-solr_additions').val();
          // if(!additions){
          //   additions = {'countries':[]};
          // }else{
          //   additions = JSON.parse(additions);
          // }
          // additions['countries'].push(country_name);
          // $('#field-solr_additions').val(JSON.stringify(additions));
          // //Add country for real
          if($('#select_groups_hidden').length >0){
            $('#select_groups_hidden').append('<input id="field-group-'+country+'-input" type="checkbox" name="groups__'+(number_of_groups)+'__id" value="'+country+'" checked="checked"/>');
          }
        }
        $('#country-drop').select2('val', '-1'); //reset Select2 dropdown
      }
    }
  });

  $('#selected_groups').click(function(event){
    if(event.target.className == "filtered pill"){
      //Uncheck hidden
      var id = event.target.children.item().value;
      $('#'+id).remove();
      $(event.target).remove();
      var country = event.target.innerText.toLowerCase().trim();
    }else if(event.target.className == "group_checked glyphicon glyphicon-remove"){
      var id = event.target.id;
      $('#'+id+'-input').remove();
      $(event.target).parent().remove();
      var country = event.target.parentNode.innerText.toLowerCase().trim();
    }
    //Remove from solr
    // var additions = JSON.parse($('#field-solr_additions').val());
    // var countries = []
    // for(c in additions['countries']){
    //   if(additions['countries'][c].toLowerCase() != country){
    //       countries.push(additions['countries'][c]);
    //   }
    // }
    // additions['countries'] = countries;
    // $('#field-solr_additions').val(JSON.stringify(additions));
    //Reset dropdown for better userability
    $('#country-drop option[value=-1]').attr('selected', true);
  });

  $('#field-organizations').change(function(){
    if($(this).val() == ''){
      $('#field-private option[value=False]').attr('selected', true);
      $('#field-private').attr('readonly', true);
    }else{
      $('#field-private').removeAttr('readonly');
    }
  });

  $('#onepage_submit, #dataset_edit').click(function(e){
    if(this.id == 'onepage_submit'){
      $(this).attr('disabled', true);
    }
    //e.preventDefault();
    if(this.id == 'onepage_submit' && $('.group_checked').length == 0){
      $(this).removeAttr('disabled');
      $('#select_country').prepend('<div class="error-explanation alert alert-danger" id="error-country"><p>Must select a country first.</p></div>');
      $('html, body').animate({
        scrollTop: $('#select_country').offset().top
      }, 2000);
    }else if($('#field-license').val()=='hdx-other' && $('#field-license_other').val() == ''){
      $(this).removeAttr('disabled');
      $('#field-license_other').parent().append('<div class="error-explanation alert alert-danger" id="error-license"><p>Please define the terms of your license.</p></div>');
      $('html, body').animate({
        scrollTop: $('#field-license_other').offset().top
      }, 2000);
    }else{
      $('#error-explanation, .error-block, .error-country').remove();
      $('.error').removeClass('error');

      //Add other specifics
      var other = $('#method_other').val();
      //$('input[value="Other"]').val("Other - "+other);
      //https://github.com/OCHA-DAP/hdx-ckan/issues/344
      $('input[value="Other"]').val(other);

      //Create date range
      var startDate	= $('#date_range1').val()
      if(startDate && startDate.length>0){
        $('#field-dataset_date').val($('#date_range1').val() +'-'+$('#date_range2').val());
      }
      //Remove extra form elements
      $('#method_other, #date_range1, #date_range2').remove();

      if(this.id == 'onepage_submit'){
        $('#dataset-upload-form').submit();
      }else{
        return true;
      }
      //$('form').submit();
    }
    return false;
  });

  $(document).ready(function(){
    $("#field-dataset_date, #date_range1, #date_range2").datepicker();
    // get rid of country tags is user tried to delete them and just got the error.
    if ($('div#select_country').find('span.error-block').length) {
      // console.log('country error detected. must be #985 :D');
      if ($('div#select_country').find('span.error-block').html().match('Missing value').length) {
        if ($('#selected_groups').find('span.pill').length) {
          $('#selected_groups').find('span.pill').each(function() {
            $(this).find('i').trigger('click');
          });
        }
      }
    }

  });

  $('#field-license').change(function(){
    if($(this).val() == 'hdx-other'){
      $('#licenses-other-define').show();
    }else{
      $('#licenses-other-define').hide();
    }
  });

  $('#field-dataset_methodology').change(function(){
    if($('#field-dataset_methodology').val() == 'Other'){
      $('#methodology-other-define').show();
    }else{
      $('#methodology-other-define').hide();
    }
  });

});

