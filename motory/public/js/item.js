frappe.ui.form.on("Item", {
    refresh(frm){
        frm.trigger("has_serial_no");    
    },
    has_serial_no: function(frm){
        if(frm.doc.has_serial_no){
            frm.set_df_property("serial_no_series", "reqd", 1);
        }else{
            frm.set_value("serial_no_series","");
            frm.set_df_property("serial_no_series", "reqd", 0);
        }
    }
    // car_grade_template_cf: function (frm) {
    //     if (frm.doc.car_grade_template_cf) {
    //         frappe.db.get_list('Car Features Detail CT', {
    //             fields: ['feature', 'is_available'],
    //             filters: {
    //                 "is_available": 1,
    //                 "parent":frm.doc.car_grade_template_cf,
    //                 "parenttype": 'Car Grade Template'
    //             }
    //         }).then(records => {
    //             frm.set_value('car_features_detail_ct',[])
    //             frm.refresh_field('car_features_detail_ct');
    //             records.forEach(data => {
    //                 let row = frm.add_child('car_features_detail_ct')
    //                 row.feature=data.feature
    //                 row.is_available= data.is_available
    //             });
    //                 frm.refresh_field('car_features_detail_ct');
    //             });
    //         }

    //     }
});