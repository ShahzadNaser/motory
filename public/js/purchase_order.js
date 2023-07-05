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
    }   
})