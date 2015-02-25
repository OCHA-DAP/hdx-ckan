var legendOpts = {
    lClassSelId: "#lClass"
};

function processLegendInfo(legendOpts) {
    var pcode = $(legendOpts.lClassSelId);

    var opts = "<option value='null'>---Select---</option>";
    for (var i=1; i<=8; i++){
        opts += "<option value='"+i+"'>" + i + "</option>"
    }

    pcode.children().remove();

    pcode.append(opts);
}

$(document).ready(
    function (){
        processLegendInfo(legendOpts);
    }
);