# Copyright (c) 2024, Shahzad Naser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CarPlateNo(Document):
	pass

def add_plate_nos():
	for row in frappe.get_all("Serial No",filters={"car_plate_no_cf": [">","0"]}, fields=["car_plate_no_cf","name","item_name"]):
		try:
			frappe.get_doc({"doctype":"Car Plate No","title":row.get("car_plate_no_cf"),"serial_no":row.get("name"),"item_name":row.get("item_name")}).insert()
		except:
			continue
	frappe.db.commit()
	for row in frappe.get_all("Purchase Order Item",filters={"car_plate_no_cf": [">","0"]}, fields=["car_plate_no_cf","item_name"]):
		try:
			frappe.get_doc({"doctype":"Car Plate No","title":row.get("car_plate_no_cf"),"serial_no":row.get("name"),"item_name":row.get("item_name")}).insert()
		except:
			continue
	frappe.db.commit()