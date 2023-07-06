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
    },
    create_stock_entry: (frm) => {
		frappe.xcall('motory.api.create_stock_entry', {
			'sales_order': frm.doc,
		}).then(stock_entry => {
			frappe.model.sync(stock_entry);
			frappe.set_route("Form", 'Stock Entry', stock_entry.name);
		});
	}
})

