frappe.ui.form.on('Quotation', {
    refresh: function (frm) {
        if (frm.doc.docstatus==1 && has_common(frappe.user_roles, ["Administrator", "System Manager","Sales Manager","Sales Master Manager"])) {
            frm.add_custom_button(__('Update Valid Till'), () => {
                frappe.prompt({
                    label: 'Valid Till',
                    fieldname: 'valid_till',
                    fieldtype: 'Date'
                }, (values) => {
                    if (values.valid_till) {
                        frappe.call({
							args:{
                                quotation:frm.doc.name,
								valid_till: values.valid_till,
							},
							method: 'motory.api.update_valid_till',
							callback: function(r) {
								if(r.message){
                                    frm.reload_doc()
                                    frappe.msgprint(__('Valid till is updated'));
								}
							}
						});             
                    }
                    
                })                
            })
        }
    },
    setup: function (frm) {
        frm.set_query('serial_no_cf', 'items', (frm, cdt, cdn) => {
            var d = frappe.model.get_doc(cdt, cdn);
            let filters = {
                item_code: d.item_code,
                'car_status_cf': 'Available',
                'item_type_cf': d.item_type_cf,
                'car_color_cf': d.car_color_cf

            }
            if (d.warehouse == "" || d.warehouse == null) {
                delete filters['warehouse']

            } else {
                Object.assign(filters, {"warehouse":d.warehouse})
            }
            if (d.car_color_cf == "" || d.car_color_cf == null) {
                delete filters['car_color_cf']

            } else {
                Object.assign(filters, {"car_color_cf":d.car_color_cf})
            }
            return {
                filters: filters
            }
        })
    },
})