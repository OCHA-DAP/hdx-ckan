$('#group_select').change(function(){
          var go = $('#group_select option:selected').val();
          window.location = go;
        });