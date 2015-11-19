"use strict";

ckan.module('hdx_custom_pages', function ($, _) {
    function displayingFormFieldsBySType(id, sType) {
        var fields = $('#section_' + id).find('.hdx-section-field');
        for (var _i = 0; _i < fields.length; _i++) {
            var field = fields[_i];
            var inputs = $(field).find('input');
            var name = inputs[0].getAttribute("id").replace("field-section-" + id + "-", "");
            if (this.field_config[sType].indexOf(name) == -1) {
                //el invisible
                $(field).removeClass("hdx-visible-element");
                if (!$(field).hasClass("hdx-invisible-element"))
                    $(field).addClass("hdx-invisible-element");
            }
            else {
                //element visible
                $(field).removeClass("hdx-invisible-element");
                if (!$(field).hasClass("hdx-visible-element"))
                    $(field).addClass("hdx-visible-element");
            }

        }
    }

    return {
        initialize: function () {
            $.proxyAll(this, /_on/);

            this.field_config = {
                "empty":[],
                "map":["data-url","section-title","max-height"],
                "key-figures":["data-url","section-title","section-description"],
                "interactive-data":["data-url","section-title","section-description","max-height"],
                "data-list":["data-url", "section-title"]
            };

            var c = $('#hdx_counter').val();
            if (!c)
                this.counter = 0;
            else{
                this.counter = c;
                for( var _i=0; _i< c; _i++){
                    //delete button
                    var sDelBtn = $('#del_section_'+_i);
                    sDelBtn.on('click',  {"section_id":_i}, this._onDelSectionClick);

                    //select section type dropdown
                    var sType = $('#field-section-'+_i+'-type');
                    displayingFormFieldsBySType.call(this, _i, sType.val());
                    sType.on('change',  {"section_id":_i, "obj": sType}, this._onSectionTypeChange);
                }
            }

            $('input[name=field-type]').on('change', this._onPageTypeChange);
            $('#add_section').on('click', this._onAddSectionClick);



        },
        _onPageTypeChange: function (event) {
            //alert(this.value);
        },
        _onSectionTypeChange: function (event) {
            var id = event.data.section_id;
            var sTypeValue = event.data.obj.val();
            //if(sType == 'empty' || sType==null )
            //    return;
            displayingFormFieldsBySType.call(this, id, sTypeValue);
        },
        _onDelSectionClick: function (event) {
            var id = event.data.section_id;
            $('#section_'+ id).remove();
        },
        _onAddSectionClick: function (e) {
            var newSection = $('#section_template').clone();
            var label = "section_" + this.counter;
            newSection.attr("id", label);
            if( $(newSection).hasClass("hdx-invisible-element") ) {
                $(newSection).removeClass("hdx-invisible-element");
                $(newSection).addClass("hdx-visible-element");
            }
            $('#sections').append(newSection);
            var templateFields = newSection.find('[id^=field-section-template-]');
            for( var _i=0; _i<templateFields.length; _i++){
                var id = templateFields[_i].getAttribute("id").replace("template", this.counter);
                var name = templateFields[_i].getAttribute("name").replace("template", this.counter);
                $(templateFields[_i]).attr("id", id);
                $(templateFields[_i]).attr("name",name);
            }

            //delete section button
            var sDelBtn = $('#del_section');
            sDelBtn.attr('id','del_section_'+this.counter);
            sDelBtn.attr('name','del_section_'+this.counter);
            sDelBtn.on('click',  {"section_id":this.counter}, this._onDelSectionClick);

            //select section type dropdown
            var sType = $('#field-section-'+this.counter+'-type');
            sType.on('change',  {"section_id":this.counter, "obj": sType}, this._onSectionTypeChange);

            $('#hdx_counter').val(this.counter);

            this.counter++;
        },
        counter: 0,
        field_config: {},
        options: {}
    };
});