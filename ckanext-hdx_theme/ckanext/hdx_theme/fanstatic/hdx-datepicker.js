"use strict";

ckan.module('hdx_datepicker', function ($, _) {
  return {
    initialize: function () {
		this.el.datepicker(
			{
				onSelect: this._onSelect,
			    dateFormat: "mm/dd/yy"
			    
			}
		);

		var dateStr = null;
    	if (this.options.original_value) {
			try {
				var range = this.options.original_value.split("-");
				if (range.length > 1) {
					if (this.options.type == 'start-period') {
						dateStr = range[0];
						this.el.datepicker("option", "maxDate", range[1]);
					}
					else if (this.options.type == 'end-period') {
						dateStr = range[1];
						this.el.datepicker("option", "minDate", range[0]);
					}
				}
				else if (this.options.type == 'single')
					dateStr = this.options.original_value;
			}
			catch(e){;}
		}
		this.el.datepicker('setDate', dateStr);

    	this.el.datepicker("option","dateFormat","MM d, yy");
    	
    	if ( this.options.alt_field_id) {
    		this.el.datepicker("option","altField","#" + this.options.alt_field_id);
    		this.el.datepicker("option","altFormat","mm/dd/yy");
    	}
    	if ( this.options.show_years_months == 'true') {
    		this.el.datepicker("option","changeMonth",true);
    		this.el.datepicker("option","changeYear",true);
    	}
    	
    	
    	$.proxyAll(this, /_on/);
    	
    	//this.el.on('click', this._onClick);
    	if ( this.options.topic ) {
    		this.el.context.ckanModule	= this;
    		this.sandbox.subscribe(this.options.topic, this._onAnotherGroupDateChange );
    	}
    },
    _onSelect: function(dateText, datepicker){
    	if (this.ckanModule)
    		this.ckanModule._onDateChange();
    },
    _onDateChange: function() {
//    	this.el.prop('disabled', false);
    	
    	if ( this.options.topic ) {
    		var selectedDate = this.el.datepicker('getDate');
    		this.sandbox.publish(this.options.topic,{action: 'clicked', source: this.options.group, sourceType:this.options.type, date: selectedDate });
    	}
    },
    _onAnotherGroupDateChange: function (message) {
    	if (message.source != this.options.group) {
//    		this.el.prop('disabled', true);
    		this.el.val('');
    		this.el.datepicker("option","maxDate",null);
    		this.el.datepicker("option","minDate",null);
    	}
    	else if (this.options.type != message.sourceType) {
    		if (this.options.type == 'start-period') {
    			this.el.datepicker("option","maxDate",message.date);
    		}
    		else if (this.options.type == 'end-period') {
    			this.el.datepicker("option","minDate",message.date);
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