frappe.ui.form.on(cur_frm.doctype, {
	party_name:function(frm) {
		if ( frm.doc.quotation_to=='Customer') {
         	frappe.db.get_value('Customer', frm.doc.party_name, 'is_bank_cf')
			.then(r => {
				let is_bank=r.message.is_bank_cf
				if (is_bank==1) {
					frm.set_df_property('sub_customer_cf', 'read_only', 0);
				}else{
					frm.doc.sub_customer_cf=''
					frm.set_df_property('sub_customer_cf', 'read_only', 1);
					frm.doc.sub_customer_name_cf=''
				}
			})
		}
	},
	customer:function(frm) {
			frappe.db.get_value('Customer', frm.doc.customer, 'is_bank_cf')
			.then(r => {
				let is_bank=r.message.is_bank_cf
				if (is_bank==1) {
					frm.set_df_property('sub_customer_cf', 'read_only', 0);
				}else{
					frm.doc.sub_customer_cf=''
					frm.set_df_property('sub_customer_cf', 'read_only', 1);
					frm.doc.sub_customer_name_cf=''
				}
			})
	},
    onload: function (frm) {
        cur_frm.set_query("sub_customer_cf", function() {
			return {
				filters: [
					["is_bank_cf", "=", 0]
				]
			}
		});
    }
});

frappe.ui.form.on(cur_frm.doctype+" Item", {
    item_code: function (frm, cdt, cdn) {
        var d = frappe.model.get_doc(cdt, cdn);
        if (d.item_code) {
            frappe.db.get_list('Car Features Detail CT', {
                fields: ['feature'],
                filters: {
                    'parent': d.item_code,
                    'parenttype': 'Item'
                }
            }).then(records => {
                let car_grade_cf = []
                records.forEach(data => {
                    car_grade_cf.push(data.feature)
                });
                d.car_grade_cf = car_grade_cf.join("\n")
            })
        }
    },
    serial_no_cf: function (frm, cdt, cdn) {
        var d = frappe.model.get_doc(cdt, cdn);
        if (d.serial_no_cf &&  d.serial_no_cf != '') {
            set_rate_for_second_hand_car(frm, cdt, cdn)
        }
        // copy serial_no_cf --> serial_no
        if (d.serial_no_cf && (['Sales Invoice','Delivery Note'].includes(frm.doctype))) {
            frappe.model.set_value(cdt, cdn, 'serial_no', d.serial_no_cf);
        }
    },
    item_type_cf: function (frm, cdt, cdn) {
        set_rate_for_second_hand_car(frm, cdt, cdn)
    }
})

function set_rate_for_second_hand_car(frm, cdt, cdn) {
    var d = frappe.model.get_doc(cdt, cdn);
    if (d.serial_no_cf && ['Used Car', 'New Car'].includes(d.item_type_cf) == true) {
        frappe.db.get_list('Expense Entry', {
            fields: ['total_amount', 'name'],
            filters: {
                expense_against_serial_no_cf: d.serial_no_cf,
                docstatus:1
            }
        }).then(records => {
            let expense_entry_total = 0
            let expense_entry_urls = ''
            if (records.length > 0) {
                for (let index = 0; index < records.length; index++) {
                    expense_entry_total += records[index].total_amount;
                    expense_entry_urls += '<a href="/app/expense-entry/' + records[index].name + '">' + records[index].name + '</a> &nbsp;'
                }
            }
            frappe.db.get_value('Serial No', d.serial_no_cf, ['purchase_rate', 'gp_percent_cf'])
                .then(r => {
                    let values = r.message;
                    if (values) {
                        let purchase_rate = values.purchase_rate
                        let gp_percent_cf = values.gp_percent_cf

                        let rate = flt(expense_entry_total + values.purchase_rate + flt(purchase_rate * gp_percent_cf / 100.0, precision("rate", d)));
                        frappe.model.set_value(cdt, cdn, 'rate', rate);
                        refresh_field("items");
                        let serial_no_url = '<a href="/app/serial-no/' + d.serial_no_cf + '">' + d.serial_no_cf + '</a>'
                        if (expense_entry_urls!='') {
                            frappe.msgprint(__('Serial No: {0} has incoming rate {1} and GP% {2} and Expense Entry total as {3}. <br> Hence rate is set as <b>{4}</b> <br> Expense Entries considered are {5}',
                            [serial_no_url, purchase_rate, gp_percent_cf, expense_entry_total, rate, expense_entry_urls]));
                        } else {
                            frappe.msgprint(__('Serial No: {0} has incoming rate {1} and GP% {2} and Expense Entry total as {3}. <br> Hence rate is set as <b>{4}</b>',
                            [serial_no_url, purchase_rate, gp_percent_cf, expense_entry_total, rate]));
                        }
                    }
                })
        })
    }
}