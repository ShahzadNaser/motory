import frappe
from frappe import _
from frappe.utils import flt

def update_serial_nos(doc,method=None):
    if doc.get("car_plate_no_cf"):
        update_serial_no(doc)
        update_expenses(doc)
        update_car_plate_no(doc)
def update_update(doc,method=None):
    try:
        old_doc = doc.get_doc_before_save()
        print(  old_doc.get("car_plate_no_cf") ,doc.get("car_plate_no_cf"),old_doc.get("car_plate_no_cf") != doc.get("car_plate_no_cf"))
        if old_doc.get("car_plate_no_cf") != doc.get("car_plate_no_cf"):
            update_serial_no(doc,old_doc.get("car_plate_no_cf"))
            update_expenses(doc,old_doc.get("car_plate_no_cf"))
            update_car_plate_no(doc,old_doc.get("car_plate_no_cf"))

    except:
        pass

def update_serial_no(doc,old_plate_no=False):
    if old_plate_no:
        old_serial_no = frappe.db.get_vaule("Serial No",{"car_plate_no_cf":str(old_serial_no)},"name")
        if old_serial_no:
            frappe.db.sql(""" UPDATE `tabGL Entry` set serial_no='{}' where remarks='{}' """.format(str(old_serial_no),str(old_plate_no)))

    if frappe.db.get_value("GL Entry",{"remarks":str(doc.get("car_plate_no_cf"))},"name"):
        frappe.db.sql(""" UPDATE `tabGL Entry` set serial_no='{}' where remarks='{}' """.format(str(doc.get("name")),str(doc.get("car_plate_no_cf"))))
    frappe.db.commit()
def update_expenses(doc,old_plate_no=False):
    if old_plate_no:
        old_serial_no = frappe.db.get_vaule("Serial No",{"car_plate_no_cf":str(old_serial_no)},"name")
        if old_serial_no:
            frappe.db.sql(""" UPDATE `tabSerial No` set total_expense_cf=(SELECT sum(net_amount) from `tabExpense Item` where car_plate_no='{0}' or serial_no='{1}' and docstatus=1) where name='{1}' """.format(str(old_plate_no),str(old_serial_no)))

    frappe.db.sql(""" UPDATE `tabSerial No` set total_expense_cf=(SELECT sum(net_amount) from `tabExpense Item` where car_plate_no='{0}' or serial_no='{1}' and docstatus=1) where name='{1}' """.format(doc.get("car_plate_no_cf"),doc.get("name")))
    frappe.db.commit()
def update_car_plate_no(doc,old_plate_no=False):
    try:
        if not frappe.db.get_value("Car Plate No",doc.get("car_plate_no_cf")):
            frappe.get_doc({"doctype":"Car Plate No","title":doc.get("car_plate_no_cf"),"serial_no":doc.get("name"),"item_name":doc.get("item_name")}).insert()
        else:
            frappe.db.sql(""" UPDATE `tabCar Plate No` set serial_no='{}' where name='{}' """.format(str(doc.get("name")),str(doc.get("car_plate_no_cf"))))

        if old_plate_no:
            old_serial_no = frappe.db.get_vaule("Serial No",{"car_plate_no_cf":str(old_serial_no)},"name")
            if old_serial_no:
                frappe.db.sql(""" UPDATE `tabCar Plate No` set serial_no='{}' where name='{}' """.format(str(old_serial_no),str(old_plate_no)))
        frappe.db.commit()    
    except:
        pass
