import frappe

def before_save(doc,method):
    if doc.get("is_return") and frappe.db.get_single_value('Motory Settings', 'return_vin_number_validation'):
        serial_nos = []
        vin_nos = []
        error_msg = ""
        for row in doc.get("items"):
            if row.get("serial_no"):
                serial_nos.append(row.get("serial_no"))
            if row.get("car_vin_no"):
                vin_nos.append(row.get("car_vin_no"))
        if serial_nos:
            error_msg = ""
            for row in frappe.db.get_all("Sales Invoice Item",filters = {"docstatus":["<",2],"parent":["!=",doc.get("name")],"serial_no":["IN",serial_nos]},fields=['parent','serial_no']):
                if frappe.db.get_value("Sales Invoice",str(row.get("parent")),"is_return"):
                    error_msg += "Serial No {} already returned in invoice {} <br>".format(str(row.get("serial_no")),str(row.get("parent")))

        if vin_nos:
            error_msg = ""
            for row in frappe.db.get_all("Sales Invoice Item",filters = {"docstatus":["<",2],"parent":["!=",doc.get("name")],"car_vin_no":["IN",vin_nos]},fields=['parent','car_vin_no']):
                if frappe.db.get_value("Sales Invoice",str(row.get("parent")),"is_return"):
                    error_msg += "VIN No. {} already returned in invoice {} <br>".format(str(row.get("car_vin_no")),str(row.get("parent")))
        
        if error_msg:
            frappe.throw(error_msg)

def before_submit(doc,method):
    if not doc.get("tax_id"):
        customer_values = frappe.db.get_value("Customer",doc.get("customer"),["tax_id","territory","custom_b2c"],as_dict=True)
        if customer_values.get("territory") != "Rest Of The World":
            doc.tax_id = customer_values.get("tax_id")
            if not doc.get("tax_id"):
                frappe.throw("Tax ID is not set for B2B Customer {}. Please set the Tax ID in the Customer.".format(doc.get("customer")))