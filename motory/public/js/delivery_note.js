frappe.ui.form.on('Delivery Note', {
    setup: function (frm) {
        frm.set_query('serial_no_cf', 'items', (frm,cdt,cdn) => {
            var d = frappe.model.get_doc(cdt, cdn);
            if (frm.doc.is_return==1) {
                car_status_cf = ['Sold Out']
            } else {
                car_status_cf = ['Available']
            }
            if (d.warehouse == "" || d.warehouse == null) {
                return {
                    filters: {
                        item_code: d.item_code,
                        'car_status_cf': ['in',car_status_cf],
                        'item_type_cf':d.item_type_cf                        

                    }
                }
            } else {
                return {
                    filters: {
                        item_code: d.item_code,
                        "warehouse": d.warehouse,
                        'car_status_cf': ['in',car_status_cf],
                        'item_type_cf':d.item_type_cf                        

                    }
                }
            }            
        })
    }
})

