import frappe

def before_save(doc,method):
    for row in doc.get("items"):
        if row.get("serial_no"):
            row.serial_no = ""