(function() {
    var hdxUtil = {
        'ui': {},
        'compute': {},
        'analytics': {} // This will be populated from analytics.js
    };
    window.hdxUtil = hdxUtil;

    hdxUtil.ui.scrollTo = function (target) {
        $('html, body').animate({
            'scrollTop': $(target).offset().top - 40
        }, 700);
    };

    hdxUtil.compute.strHash = function (theString, startHash) {
        var i, chr, len;
        var hash = startHash ? startHash : 0;
        if (!theString || theString.length === 0) return hash;
        for (i = 0, len = theString.length; i < len; i++) {
            chr = theString.charCodeAt(i);
            hash = ((hash << 5) - hash) + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };

    hdxUtil.compute.strListHash = function (strList) {
        var hash = 0;
        if (strList) {
            for(var i=0; i<strList.length; i++) {
                var curStr = strList[i];
                hash = hdxUtil.compute.strHash(curStr, hash);
            }
        }
        return hash;
    };

})();