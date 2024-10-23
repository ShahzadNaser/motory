import frappe

def before_save(doc,method=None):
    if doc.get("is_return") and frappe.db.get_single_value('Motory Settings', 'return_vin_number_validation'):
        serial_nos = []
        error_msg = ""
        for row in doc.get("items"):
            if row.get("serial_no"):
                serial_nos.append(row.get("serial_no"))
        if serial_nos:
            for row in frappe.db.get_all("Purchase Invoice Item",filters = {"docstatus":["<",2],"parent":["!=",doc.get("name")],"serial_no":["IN",serial_nos]},fields=['parent','serial_no']):
                error_msg += "Serial No {} already returned in invoice {} <br>".format(str(row.get("serial_no")),str(row.get("parent")))
        if error_msg:
            frappe.throw(error_msg)