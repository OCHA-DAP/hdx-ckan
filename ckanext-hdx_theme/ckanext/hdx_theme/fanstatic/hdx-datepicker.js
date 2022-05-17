"use strict";

ckan.module('hdx_datepicker', function ($, _) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      if(this.options.type !== 'date_ongoing') {
        this.el.datepicker(
          {
            onSelect: this._onSelect,
            dateFormat: "yy-mm-dd"
          }
        );

        var dateStr = null;
        if (this.options.original_value) {
          try {
            var range = this.options.original_value.split("TO");
            if (range.length > 1) {
              if (this.options.type === 'start-period') {
                dateStr = range[0];
                this.el.datepicker("option", "maxDate", range[1]);
              } else if (this.options.type === 'end-period') {
                dateStr = range[1];
                this.el.datepicker("option", "minDate", range[0]);
              }
            } else if (this.options.type === 'single')
              dateStr = this.options.original_value;
          } catch (e) {
            ;
          }
        }

        this.el.datepicker('setDate', dateStr);
        this.el.datepicker("option", "dateFormat", "MM d, yy");

        if (this.options.alt_field_id) {
          this.el.datepicker("option", "altField", "#" + this.options.alt_field_id);
          this.el.datepicker("option", "altFormat", "yy-mm-dd");
        }
        if (this.options.show_years_months === 'true') {
          this.el.datepicker("option", "changeMonth", true);
          this.el.datepicker("option", "changeYear", true);
        }
      }
      else{
        if(this.options.type === "date_ongoing"){
          if(this.el[0].checked === true){
            var uiDateRange2 = $('#ui_date_range2');
            uiDateRange2.val('');
            uiDateRange2.prop('disabled',true);
            $('#date_range2').val('');
          }
          this.el.change(this._onDateOngoingChange);
        }
      }
      if (this.options.topic) {
        this.sandbox.subscribe(this.options.topic, this._onAnotherGroupDateChange);
      }
    },
    _onDateOngoingChange: function () {
      this.sandbox.publish(this.options.topic, {
            action: 'date_ongoing',
            group: this.options.group,
            sourceType: this.options.type
            // checked: this.el[0].checked
          });
    },
    _onSelect: function (dateText, datepicker) {
      this._onDateChange();
    },
    _onDateChange: function () {
      if (this.options.topic) {
        var selectedDate = this.el.datepicker('getDate');
        this.sandbox.publish(this.options.topic, {
          action: 'date_selected',
          group: this.options.group,
          sourceType: this.options.type,
          date: selectedDate
        });
      }
    },
    _onAnotherGroupDateChange: function (message) {
      if (message.action === "date_ongoing") {
        if(this.options.type === "date_ongoing"){
          var dateRange2 = $('#date_range2');
          dateRange2.val('');
          var uiDateRange2 = $('#ui_date_range2');
          uiDateRange2.val('');
          if(this.el[0].checked === true){
            uiDateRange2.prop('disabled',true);
          }
          else{
            uiDateRange2.prop('disabled',false);
          }
        }
      } else if (this.options.type !== message.sourceType) {
        if (this.options.type === 'start-period') {
          this.el.datepicker("option", "maxDate", message.date);
        } else if (this.options.type === 'end-period') {
          this.el.datepicker("option", "minDate", message.date);
        }
      }
    },
    options: {
      group: '1',
      topic: null,
      show_years_months: 'true',
      type: null,
      alt_field_id: null,
      original_value: null
    }
  };
});
