// Copyright (c) 2024, Shahzad Naser and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expenses', {
	refresh: function(frm) {
		if(frm.doc.docstatus ==1) {
			frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by: '',
					show_cancelled_entries: frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			});
		}
		if(frm.doc.docstatus===1 && frm.doc.outstanding_amount!=0) {
			frm.add_custom_button(__("Payment"), function() {
				frm.events.make_payment_entry(frm);
			});
		}
	},
	calculate_totals: function(frm){
		let totals = {
			"base_grand_total":0,
			"grand_total":0,
			"total_taxes_and_charges":0
		};
		frm.doc.expenses.forEach(function(item){
			let tax_amount = 0;
			if (item.tax_rate){
				tax_amount = parseFloat(item.tax_rate/100) * parseFloat(item.amount)
			}
			frappe.model.set_value(item.doctype, item.name, 'tax_amount', tax_amount);
			frappe.model.set_value(item.doctype, item.name, 'net_amount', parseFloat(tax_amount)+parseFloat(item.amount));
			totals.base_grand_total = totals.base_grand_total + item.amount;
			totals.total_taxes_and_charges = totals.total_taxes_and_charges + tax_amount;
		});
		totals.markup_p = flt(totals.markup/totals.total)*100;
		frm.set_value("base_grand_total",totals.base_grand_total);
		frm.set_value("total_taxes_and_charges",totals.total_taxes_and_charges);
		frm.set_value("grand_total",totals.base_grand_total + totals.total_taxes_and_charges);
		frm.set_value("outstanding_amount",totals.base_grand_total + totals.total_taxes_and_charges);
		setTimeout(function(){
			cur_frm.refresh_fields();
		},1000)
	},
	before_save: function(frm){
		frm.trigger("calculate_totals");
	},
	make_payment_entry: function(frm) {
		return frappe.call({
			method: "motory.motory.doctype.expenses.expenses.get_payment_entry",
			args: {
				"dt": frm.doc.doctype,
				"dn": frm.doc.name,
				"party_type": "Supplier",
				"payment_type": "Pay",
			},
			callback: function(r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", doc[0].doctype, doc[0].name);
			}
		});
	},
});

frappe.ui.form.on('Expense Item', {
	item_tax_template:function(frm, cdt, cdn){
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "tax_rate", 0);
		frappe.model.set_value(cdt, cdn, "account_head", "");
		if(item.item_tax_template){
			frappe.call({
				"method": "motory.motory.doctype.expenses.expenses.get_tax_details",
				"args": {"item_tax_template":item.item_tax_template},
				callback: function(r) {
					if(r.message) {
						frappe.model.set_value(cdt, cdn, "tax_rate", r.message.tax_rate);
						frappe.model.set_value(cdt, cdn, "account_head", r.message.account);
						frm.trigger("calculate_totals");
					}
				}
			});
		}else{
			frm.trigger("calculate_totals");
		}
	},
	amount:function(frm, cdt, cdn){
		frm.trigger("calculate_totals");
	},
	expenses_add:function(frm, cdt, cdn){
		frm.trigger("calculate_totals");
	},
	expenses_remove:function(frm, cdt, cdn){
		frm.trigger("calculate_totals");
	}
});
