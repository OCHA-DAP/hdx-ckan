$(document).ready(function(){
    var $contact = $('#contact-contributor-form');
    $contact.find("select").select2();
    $contact.on('submit', function(){
        $this = $(this);

        return false;
    });

});