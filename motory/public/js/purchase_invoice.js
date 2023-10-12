frappe.ui.form.on("Purchase Invoice Item", {
    item_code(frm,cdt,cdn) {
	    var item = frappe.get_doc(cdt, cdn);
        frappe.call({
            "method": "motory.api.get_account",
            "args": {"doctype":"Purchase Invoice","cost_center":item.cost_center,"item_type_cf":item.item_type_cf},
            callback: function(r) {
                if(r.message) {
                    frappe.model.set_value(cdt, cdn, "expense_account", r.message);
                }
            }
        });	
	},
    cost_center(frm,cdt,cdn) {
	    var item = frappe.get_doc(cdt, cdn);
        frappe.call({
            "method": "motory.api.get_account",
            "args": {"doctype":"Purchase Invoice","cost_center":item.cost_center,"item_type_cf":item.item_type_cf},
            callback: function(r) {
                if(r.message) {
                    frappe.model.set_value(cdt, cdn, "expense_account", r.message);
                }
            }
        });		
	},
	item_type_cf(frm,cdt,cdn) {
	    var item = frappe.get_doc(cdt, cdn);
        frappe.call({
            "method": "motory.api.get_account",
            "args": {"doctype":"Purchase Invoice","cost_center":item.cost_center,"item_type_cf":item.item_type_cf},
            callback: function(r) {
                if(r.message) {
                    frappe.model.set_value(cdt, cdn, "expense_account", r.message);
                }
            }
        });	
    }
});