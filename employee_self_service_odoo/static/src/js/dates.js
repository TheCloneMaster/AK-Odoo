odoo.define('odoo_rental_contract_management', function (require) {
'use strict';
    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var _t = core._t;
    var website = require('website.website');
    $("div.input-group span.fa-calendar").on('click', function(e) {
            $(e.currentTarget).closest("div.date").datetimepicker({
                useSeconds: true,
                icons : {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down'
                },
            });
        });
        
        var clickwatch = (function(){
              var timer = 0;
              return function(callback, ms){
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
              };
        })();
        
        $("td.text-center input.update_date").on("change", function (ev) {
            ev.preventDefault();
             var $link = $(ev.currentTarget);
             var $date_start = $link.closest('.start_date').val();
             var $end_date = $link.closest('.end_date').val();
          var $input = $(this);
          var line_id = parseInt($input.data('line-id'),10);
          var product_ids = [parseInt($input.data('product-id'),10)];
            clickwatch(function(){

            ajax.jsonRpc("/shop/cart/update_json_date", 'call', {
                'line_id': line_id,
                'product_id': parseInt($input.data('product-id'), 10),
                'start_date' : $date_start,
                'end_date' : $end_date,
            }).then(function (data) {});
          }, 500);
          });
});
