"use strict";

ckan.module('hdx_custom_pages', function ($, _) {
    function displayingFormFieldsBySType(id, sType) {
        var fields = $('#section_' + id).find('.hdx-section-field');
        for (var _i = 0; _i < fields.length; _i++) {
            var field = fields[_i];
            var inputs = $(field).find('input');
            var txt_input = $(inputs[0]);
            var name = txt_input.attr('id').replace("field_section_" + id + "_", "");
            if (this.field_config[sType].indexOf(name) == -1) {
                //el invisible
                $(field).removeClass("hdx-visible-element");
                if (!$(field).hasClass("hdx-invisible-element"))
                    $(field).addClass("hdx-invisible-element");
                    txt_input.prop("disabled", true);
            }
            else {
                //element visible
                $(field).removeClass("hdx-invisible-element");
                if (!$(field).hasClass("hdx-visible-element"))
                    $(field).addClass("hdx-visible-element");
                    txt_input.removeProp("disabled");
            }

        }
    }

    return {
        initialize: function () {
            $.proxyAll(this, /_on/);

            this.field_config = {
                "empty":[],
                "map":["data_url","section_title","max_height"],
                "key_figures":["data_url","section_title","section_description"],
                "interactive_data":["data_url","section_title","section_description","max_height"],
                "data_list":["data_url", "section_title"]
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
                    var sType = $('#field_section_'+_i+'_type');
                    displayingFormFieldsBySType.call(this, _i, sType.val());
                    sType.on('change',  {"section_id":_i, "obj": sType}, this._onSectionTypeChange);
                }
            }

            $('input[name=field_type]').on('change', this._onPageTypeChange);
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
            event.preventDefault();
            return false;
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
            var templateFields = newSection.find('[id^=field_section_template_]');
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
            var sType = $('#field_section_'+this.counter+'_type');
            sType.on('change',  {"section_id":this.counter, "obj": sType}, this._onSectionTypeChange);

            this.counter++;

            $('#hdx_counter').val(this.counter);
        },
        counter: 0,
        field_config: {},
        options: {}
    };
});