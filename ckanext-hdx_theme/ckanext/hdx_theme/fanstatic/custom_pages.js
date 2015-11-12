"use strict";

ckan.module('hdx_custom_pages', function ($, _) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);

            this.field_config = {
                "map":["data-url","max-height"],
                "key-figures":["data-url","description","source"],
                "interactive-data":["data-url","title-of-visualization","max-height","description","source"],
                "data-list":["data-url"]
            };

            var c = $('#hdx_counter').val();
            if (!c)
                this.counter = 0;
            else
                this.counter = c;

            $('input[name=field-type]').on('change', this._onPageTypeChange);
            $('#add_section').on('click', this._onAddSectionClick);

        },
        _onPageTypeChange: function (event) {
            alert(this.value)
        },
        _onSectionTypeChange: function (event) {
            var id = event.data.section_id;
            alert(this.value)
        },
        _onDelSectionClick: function (event) {
            var id = event.data.section_id;
            $('#section_'+ id).remove();
        },
        _onAddSectionClick: function (e) {
            var newSection = $('#section_template').clone();
            var label = "section_" + this.counter;
            newSection.attr("id", label);
            $('#sections').append(newSection);
            var templateFields = newSection.find('[id^=field-section-template-]');
            for( var _i=0; _i<templateFields.length; _i++){
                var id = templateFields[_i].getAttribute("id").replace("template", this.counter);
                var name = templateFields[_i].getAttribute("name").replace("template", this.counter);
                $(templateFields[_i]).attr("id", id);
                $(templateFields[_i]).attr("name",name);
            }

            var sDelBtn = $('#del_section');
            sDelBtn.attr('id','del_section_'+this.counter);
            sDelBtn.attr('name','del_section_'+this.counter);
            sDelBtn.on('click',  {"section_id":this.counter}, this._onDelSectionClick);

            var sType = $('#field-section-'+this.counter+'-type');
            sType.on('change',  {"section_id":this.counter}, this._onSectionTypeChange);

            this.counter++;
        },
        counter: 0,
        field_config: {},
        options: {}
    };
});