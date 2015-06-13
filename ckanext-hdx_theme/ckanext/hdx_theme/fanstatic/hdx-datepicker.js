"use strict";

ckan.module('hdx_datepicker', function ($, _) {
  return {
    initialize: function () {
    	var originalDateString 	= null;
    	if (this.options.alt_field_id) 
    		originalDateString	= $('#'+this.options.alt_field_id).val()
		this.el.datepicker(
			{
				onSelect: this._onSelect,
			    dateFormat: "mm/dd/yy"
			    
			}
		);
    	
    	if (originalDateString)
    		this.el.datepicker('setDate', originalDateString);
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
    		this.sandbox.publish(this.options.topic,{action: 'clicked', source: this.options.group, date: selectedDate });
    	}
    },
    _onAnotherGroupDateChange: function (message) {
    	if (message.source != this.options.group) {
//    		this.el.prop('disabled', true);
    		this.el.val('');
    		this.el.datepicker("option","maxDate",null);
    		this.el.datepicker("option","minDate",null);
    	}
    	else {
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
    	alt_field_id: null
    }
  };
});