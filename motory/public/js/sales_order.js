frappe.provide("erpnext.taxes_and_totals");

frappe.ui.form.on('Sales Order', {
    setup: function (frm) {
        frm.set_query('serial_no_cf', 'items', (frm,cdt,cdn) => {
            var d = frappe.model.get_doc(cdt, cdn);
            if (d.warehouse == "" || d.warehouse == null) {
                return {
                    filters: {
                        item_code: d.item_code,
                        'car_status_cf': ['in',['Available']],
                        'item_type_cf':d.item_type_cf                        

                    }
                }
            } else {
                return {
                    filters: {
                        item_code: d.item_code,
                        "warehouse": d.warehouse,
                        'car_status_cf': ['in',['Available']],
                        'item_type_cf':d.item_type_cf                        

                    }
                }
            }            
        })
    },	
    refresh: function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Transfer Car'), () => frm.trigger('create_stock_entry'));
        }
        cur_frm.doc.items.forEach(function(item){
            if (item.serial_no_cf && item.purchase_rate){
                let margin_p = ((item.rate - item.purchase_rate)/item.rate)*100;
                var color = "white";
                if(margin_p <= 1.00 ){
                    color = "#ffe6e6"; 
                }
                if(item.discount_percentage &&  item.discount_percentage > 0.5){
                    color = "#f9f1df"; 
                    if (margin_p <= 1.00){
                        color = "#e7b3b9"; 
                    }
                }
                $('[data-name="'+item.name+'"]').css('background-color',color);
            }
        });
    
    },
    create_stock_entry: (frm) => {
		frappe.xcall('motory.api.create_stock_entry', {
			'sales_order': frm.doc,
		}).then(stock_entry => {
			frappe.model.sync(stock_entry);
			frappe.set_route("Form", 'Stock Entry', stock_entry.name);
		});
	}
});

frappe.ui.form.on("Sales Order Item", {
    serial_no_cf:function(frm,cdt,cdn){
        var item = frappe.get_doc(cdt, cdn);
        frappe.db.get_value(
            "Serial No",
            {
                name: item.serial_no_cf
            },
            "purchase_rate",
            (r) => {
                if (r) {
                    frappe.model.set_value(cdt, cdn, "purchase_rate", r.purchase_rate);
                    frm.trigger("rate", cdt, cdn);
                }
            }
        );
    }
  });

erpnext.taxes_and_total = erpnext.taxes_and_totals.extend({
    calculate_net_total: function() {        
        var me = this;
        this.frm.doc.total_qty = this.frm.doc.total = this.frm.doc.base_total = this.frm.doc.net_total = this.frm.doc.base_net_total = 0.0;
        $.each(this.frm.doc["items"] || [], function(i, item) {
            me.frm.doc.total += item.amount;
            me.frm.doc.total_qty += item.qty;
            me.frm.doc.base_total += item.base_amount;
            me.frm.doc.net_total += item.net_amount;
            me.frm.doc.base_net_total += item.base_net_amount;
            if( "net_profit_margin" in me.frm.doc){
                me.frm.doc.net_profit_margin +=  (item.rate - (item.purchase_rate || 0)) * item.qty
            }
        });
        frappe.model.round_floats_in(this.frm.doc, ["total", "base_total", "net_total", "base_net_total","net_profit_margin"]);
        console.log("=====================calculate_net_total=======================");

    },
    get_current_tax_amount: function(item, tax, item_tax_map) {
		var tax_rate = this._get_tax_rate(tax, item_tax_map);
		var current_tax_amount = 0.0;

		// To set row_id by default as previous row.
		if(["On Previous Row Amount", "On Previous Row Total"].includes(tax.charge_type)) {
			if (tax.idx === 1) {
				frappe.throw(
					__("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row"));
			}
			if (!tax.row_id) {
				tax.row_id = tax.idx - 1;
			}
		}
		if(tax.charge_type == "Actual") {
			// distribute the tax amount proportionally to each item row
			var actual = flt(tax.tax_amount, precision("tax_amount", tax));
			current_tax_amount = this.frm.doc.net_total ?
				((item.net_amount / this.frm.doc.net_total) * actual) : 0.0;

		} else if(tax.charge_type == "On Net Total") {
			current_tax_amount = (tax_rate / 100.0) * item.net_amount;
		} else if(tax.charge_type == "On Previous Row Amount") {
			current_tax_amount = (tax_rate / 100.0) *
				this.frm.doc["taxes"][cint(tax.row_id) - 1].tax_amount_for_current_item;

		} else if(tax.charge_type == "On Previous Row Total") {
			current_tax_amount = (tax_rate / 100.0) *
				this.frm.doc["taxes"][cint(tax.row_id) - 1].grand_total_for_current_item;
		} else if (tax.charge_type == "On Item Quantity") {
			current_tax_amount = tax_rate * item.qty;
		} else if(tax.charge_type == "On Profit Margin") {
			current_tax_amount = (tax_rate / 100.0) * (item.net_amount - ((item.purchase_rate || 0) * item.qty));
		}

		if (!tax.dont_recompute_tax) {
			this.set_item_wise_tax(item, tax, tax_rate, current_tax_amount);
		}

        console.log("=====================get_current_tax_amount=======================");

		return current_tax_amount;
	}
});

$.extend(cur_frm.cscript, new erpnext.taxes_and_total({frm: cur_frm}));


