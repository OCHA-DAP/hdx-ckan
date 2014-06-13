$('#field-private option[value=False]').attr('selected', true);

$('#country-drop').change(function(){
      var country = $('#country-drop option:selected').val();
      var country_name = $('#country-drop option:selected').attr('display_name');
      if($('#'+country).length == 0){
        var number_of_groups = $('.group_checked').length;
        //Add country
        if(country != '-1'){
          $('#selected_groups').append('<span class="filtered pill">'+country_name+' <input id="field-group-'+(number_of_groups)+'" type="checkbox" name="groups__'+(number_of_groups)+'__id" value="'+country+'" checked="checked" class="group_checked"/></span>');
          //Add country for real
          if($('#select_groups_hidden').length >0){
            $('#select_groups_hidden').append('<input id="'+country+'" type="checkbox" name="groups__'+(number_of_groups)+'__id" value="'+country+'" checked="checked"/>');
          }
        }
      }
    });

    $('#selected_groups').click(function(event){
      if(event.target.className == "filtered pill"){
        //Uncheck hidden
        var id = event.target.children.item().value;
        $('#'+id).remove();
        $(event.target).remove();
      }else if(event.target.className == "group_checked"){
        var id = event.target.value;
        $('#'+id).remove();
        $(event.target).parent().remove();
      }
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
      //e.preventDefault();	
      if(this.id == 'onepage_submit' && $('.group_checked').length == 0){
        $('#select_country').prepend('<div class="error-explanation alert alert-error" id="error-country"><p>Must select a country first.</p></div>');
        $('html, body').animate({
              scrollTop: $('#select_country').offset().top
            }, 2000);
      }else if($('#field-license').val()=='hdx-other' && $('#field-license_other').val() == ''){
        $('#field-license_other').parent().append('<div class="error-explanation alert alert-error" id="error-license"><p>Please define the terms of your license.</p></div>');
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
});

$('#field-license').change(function(){ 
  if($(this).val() == 'hdx-other'){
    $('#licenses-other-define').show();
  }else{
    $('#licenses-other-define').hide();
  }
});
