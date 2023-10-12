from operator import truth
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
import frappe
from frappe import _
import json
from frappe.utils import get_link_to_form
from frappe.utils import  getdate, today, flt, get_datetime

@frappe.whitelist()
def update_valid_till(quotation,valid_till):
	frappe.db.set_value('Quotation', quotation, 'valid_till', valid_till)
	return True

@frappe.whitelist()
def get_account(doctype=None,cost_center=None, item_type_cf=None):

	return frappe.db.get_value("Child Config",{"doctype_":doctype,"cost_center":cost_center,"item_type_cf":item_type_cf},"account") or ""

def update_expense_in_serial_no(self,method):
	if self.expense_against_serial_no_cf:
		if method=='on_submit':
			calculate_total_expense_cf_in_serial_no(self.expense_against_serial_no_cf)
		if method=='on_cancel':
			calculate_total_expense_cf_in_serial_no(self.expense_against_serial_no_cf)

def calculate_total_expense_cf_in_serial_no(serial_no):
	expense_entry_detail=frappe.db.sql("SELECT sum(exp_entry.total_amount) as total_amt ,exp_entry.expense_against_serial_no_cf  FROM `tabExpense Entry` as exp_entry WHERE exp_entry.docstatus =1 group by exp_entry.expense_against_serial_no_cf ", as_dict=1)
	for expense in expense_entry_detail:
		if expense.expense_against_serial_no_cf==serial_no:
			total_expense=flt(expense.total_amt or 0)
			incoming_rate=frappe.db.get_value('Serial No', expense.expense_against_serial_no_cf, 'purchase_rate')
			total_expense=flt(flt(total_expense)+flt(incoming_rate or 0))
			frappe.db.set_value('Serial No', expense.expense_against_serial_no_cf, 'total_expense_cf', total_expense)


def before_save_pi(doc,method):
	if doc.get("type") == "Expense" and doc.get("serial_no"):
		if doc.get("serial_no") not in doc.get("remarks"):
			doc.remarks = "Expense Entry For Serial No # {}".format(doc.get("serial_no"))
		
def update_car_status_to_available_for_expired_quotations():
	expired_quotations=frappe.db.get_list('Quotation', filters={'valid_till': ['<', getdate(today())],'docstatus':1,'status': ['!=', 'Expired']},fields=['name'])
	print('expired_quotations',expired_quotations)	
	for quotation_name in expired_quotations:
		quotation=frappe.get_doc('Quotation',quotation_name)
		for item in quotation.get("items"):
			if item.serial_no_cf:
				frappe.db.set_value('Serial No', item.serial_no_cf, 'car_status_cf', 'Available')		
				quotation.add_comment("Comment", "Night Job: VIN Number(Serial No) {0} status is made to available for expired quotation"
				.format(get_link_to_form('Serial No', item.serial_no_cf)))
				serial_no_doc=frappe.get_doc('Serial No',item.serial_no_cf)
				serial_no_doc.add_comment("Comment", "Night Job: VIN Number(Serial No) status is made to available for expired quotation {0}"
				.format(get_link_to_form('Quotation', quotation.name)))				

def copy_car_serial_to_vin(self,method):
	if ((self.doctype =='Delivery Note') 
	   or ( self.doctype =='Sales Invoice' and self.get("update_stock") == 1) ):
		for item in self.get("items"):
				if item.serial_no_cf!=None:
					item.serial_no=item.serial_no_cf
					frappe.msgprint(_("Car Serial No {0} is copied to VIN Number(Serial No)"
					.format(item.serial_no_cf)), alert=True)


def fetch_used_car_details(self,method):
	for item in self.get("items"):
		if item.item_type_cf=='Used Car':
			serial_nos=get_serial_nos(item.serial_no)
			if len(serial_nos)>0:		
				serial_no=serial_nos[0]
				serial_no_doc=frappe.get_doc('Serial No',serial_no)	
				item.car_plate_no_cf=serial_no_doc.car_plate_no_cf
				item.car_odometer_cf=serial_no_doc.car_odometer_cf
				frappe.msgprint(_("Car Plate,Odometer details are copied from  {0}"
				.format(serial_no)), alert=True)				

def copy_car_fields_to_serial_no_doc(self,method):
	if (self.doctype=='Purchase Receipt') or (self.doctype=='Stock Entry' and self.get("stock_entry_type")=="Material Receipt") or (self.doctype=='Purchase Invoice' and self.get("update_stock")==1):
		for item in self.get("items"):
			serial_nos=get_serial_nos(item.serial_no)
			if len(serial_nos)>0:		
				serial_no=serial_nos[0]
				serial_no_doc=frappe.get_doc('Serial No',serial_no)	
				serial_no_doc.car_source_cf=item.get("car_source_cf")
				serial_no_doc.car_plate_no_cf=item.get("car_plate_no_cf")
				serial_no_doc.car_odometer_cf=item.get("car_odometer_cf")
				serial_no_doc.item_type_cf=item.get("item_type_cf")
				serial_no_doc.car_color_cf=item.get("car_color_cf")
				serial_no_doc.car_parking_no_cf=item.get("car_parking_no_cf")
				serial_no_doc.car_line_no_cf=item.get("car_line_no_cf")
				if self.get('car_accessories_detail_cf'):
					serial_no_doc.car_accessories_detail_cf=None
					for accessory in self.get('car_accessories_detail_cf'):
						accessory_row=serial_no_doc.append('car_accessories_detail_cf',{})
						accessory_row.accessory=accessory.accessory
						accessory_row.is_available=accessory.is_available						
				if self.get('car_predelivery_inspection_checklist_cf'):
					serial_no_doc.car_predelivery_inspection_checklist_cf=None
					for checklist in self.get('car_predelivery_inspection_checklist_cf'):
						checklist_row=serial_no_doc.append('car_predelivery_inspection_checklist_cf',{})
						checklist_row.predelivery_check=checklist.predelivery_check
						checklist_row.is_checked=checklist.is_checked	
				if item.get("comments"):
					serial_no_doc.append("observation",{"posting_date":get_datetime(),"added_by":frappe.session.user,"reference_doctype":self.doctype,"observation":item.get("comments"),"reference_id":self.name})
				serial_no_doc.flags.ignore_validate = True					
				serial_no_doc.save(ignore_permissions=True)				
				frappe.msgprint(_("VIN Number(Serial No) {0} all car fields are updated"
				.format(get_link_to_form('Serial No', serial_no))), alert=True)
	if self.doctype=='Purchase Invoice' and self.get("type") == "Expense" and self.get("serial_no"):
		total_expense = frappe.db.get_value('Serial No', self.get("serial_no"), 'total_expense_cf') or 0 + self.get("rounded_total")
		frappe.db.set_value('Serial No', self.get("serial_no"), 'total_expense_cf', total_expense)
		# frappe.db.commit()


def sync_accessories_inspection_details(self,method):
	if (self.doctype=='Purchase Receipt') or (self.doctype=='Stock Entry' and self.get("stock_entry_type")=="Material Receipt"):
		for item in self.get("items"):
			serial_nos=get_serial_nos(item.serial_no)
			if len(serial_nos)>0:		
				serial_no=serial_nos[0]
				serial_no_doc=frappe.get_doc('Serial No',serial_no)
				if self.get('car_accessories_detail_cf'):
					serial_no_doc.car_accessories_detail_cf=None
					for accessory in self.get('car_accessories_detail_cf'):
						accessory_row=serial_no_doc.append('car_accessories_detail_cf',{})
						accessory_row.accessory=accessory.accessory
						accessory_row.is_available=accessory.is_available	
					serial_no_doc.flags.ignore_validate = True						
					serial_no_doc.save(ignore_permissions=True)
					frappe.msgprint(_("VIN Number(Serial No) {0} accessories table is updated"
					.format(get_link_to_form('Serial No', serial_no))), alert=True)  					
				
				if self.get('car_predelivery_inspection_checklist_cf'):
					serial_no_doc.car_predelivery_inspection_checklist_cf=None
					for checklist in self.get('car_predelivery_inspection_checklist_cf'):
						checklist_row=serial_no_doc.append('car_predelivery_inspection_checklist_cf',{})
						checklist_row.predelivery_check=checklist.predelivery_check
						checklist_row.is_checked=checklist.is_checked
					serial_no_doc.flags.ignore_validate = True	
					serial_no_doc.save(ignore_permissions=True)
					frappe.msgprint(_("VIN Number(Serial No) {0} predelivery inspection checklist table is updated"
					.format(get_link_to_form('Serial No', serial_no))), alert=True)					


def fetch_accessories_inspection_details(self,method):
	if ((self.doctype=='Purchase Receipt') or (self.doctype=='Delivery Note') or (self.doctype=='Stock Entry' and self.get("stock_entry_type")=="Material Receipt")
		or (self.doctype=='Purchase Invoice' and  self.get("update_stock") == 1)):
		motory_settings=frappe.get_doc('Motory Settings','Motory Settings')
		if not self.car_accessories_detail_cf:
			for accessory in motory_settings.get("car_accessories_detail"):
				accessory_row=self.append('car_accessories_detail_cf',{})
				accessory_row.accessory=accessory.accessory
				accessory_row.is_available=accessory.is_available

		if not self.car_predelivery_inspection_checklist_cf:
			for checklist in motory_settings.get("car_predelivery_inspection_checklist"):
				checklist_row=self.append('car_predelivery_inspection_checklist_cf',{})
				checklist_row.predelivery_check=checklist.predelivery_check
				checklist_row.is_checked=checklist.is_checked
			frappe.msgprint(_("Accessories & Pre delivery inspection checklist tables are updated from motory settings."
			), alert=True)  				

def change_serial_no_car_status_for_serial_no_cf(self,new_car_status):
	for item in self.get("items"):
		if item.serial_no_cf:
			# previous_car_status_cf=frappe.db.get_value('Serial No', item.serial_no_cf, 'car_status_cf') or None
			# frappe.db.set_value('Serial No', item.serial_no_cf, 'car_status_cf', new_car_status)

			if frappe.db.exists('Serial No', item.serial_no_cf):
				serial_no_doc=frappe.get_doc('Serial No',item.serial_no_cf)
				previous_car_status_cf = serial_no_doc.car_status_cf

				serial_no_doc.append("status_log",{"posting_date":get_datetime(),"updated_by":frappe.session.user,"reference_doctype":self.doctype,
					"reference_id":self.name,"old_status":previous_car_status_cf,"new_status":new_car_status})
				serial_no_doc.car_status_cf = new_car_status

				serial_no_doc.flags.ignore_validate = True					
				serial_no_doc.save(ignore_permissions=True)


				frappe.msgprint(_("VIN Number(Serial No) {0} status is changed from {1} to {2}"
				.format(get_link_to_form('Serial No', item.serial_no_cf),previous_car_status_cf,new_car_status)), alert=True) 	

def change_serial_no_car_status_for_serial_nos(self,new_car_status):
	for item in self.get("items"):
		serial_nos=get_serial_nos(item.serial_no)
		if len(serial_nos)>0:
			serial_no=serial_nos[0]
			# previous_car_status_cf=frappe.db.get_value('Serial No', serial_no, 'car_status_cf') or None
			# frappe.db.set_value('Serial No', serial_no, 'car_status_cf',new_car_status)
			if frappe.db.exists('Serial No', serial_no):
				serial_no_doc=frappe.get_doc('Serial No',serial_no)
				previous_car_status_cf = serial_no_doc.car_status_cf

				serial_no_doc.append("status_log",{"posting_date":get_datetime(),"updated_by":frappe.session.user,"reference_doctype":self.doctype,
					"reference_id":self.name,"old_status":previous_car_status_cf,"new_status":new_car_status})
				serial_no_doc.car_status_cf = new_car_status

				serial_no_doc.flags.ignore_validate = True					
				serial_no_doc.save(ignore_permissions=True)

				frappe.msgprint(_("VIN Number(Serial No) {0} status is changed from {1} to {2}"
				.format(get_link_to_form('Serial No', serial_no),previous_car_status_cf,new_car_status)), alert=True) 	

def change_serial_no_car_status_to_available_or_damage_for_serial_nos(self):
	damage_warehouse_type = frappe.db.get_single_value('Motory Settings', 'damage_warehouse_type')
	for item in self.get("items"):
		serial_nos=get_serial_nos(item.serial_no)

		if len(serial_nos)>0:
			serial_no=serial_nos[0]	
			new_car_status="Available"

			if frappe.db.exists('Serial No', serial_no):
				serial_no_doc=frappe.get_doc('Serial No',serial_no)

				previous_car_status_cf = serial_no_doc.car_status_cf

				serial_no_doc.append("status_log",{"posting_date":get_datetime(),"updated_by":frappe.session.user,"reference_doctype":self.doctype,
					"reference_id":self.name,"old_status":previous_car_status_cf,"new_status":new_car_status})

				if serial_no_doc.get("warehouse") and damage_warehouse_type == frappe.db.get_value('Warehouse', serial_no_doc.get("warehouse"), 'warehouse_type'):
					new_car_status = "Damage"

				serial_no_doc.car_status_cf = new_car_status

				serial_no_doc.flags.ignore_validate = True					
				serial_no_doc.save(ignore_permissions=True)

				frappe.msgprint(_("VIN Number(Serial No) {0} status is changed from {1} to {2}"
				.format(get_link_to_form('Serial No', serial_no),previous_car_status_cf,new_car_status)), alert=True)

		# print('1'*100)
		# print(serial_nos)
		# if len(serial_nos)>0:
		# 	serial_no=serial_nos[0]	
		# 	warehouse=frappe.db.get_value('Serial No', serial_no, 'warehouse')
		# 	warehouse_type=frappe.db.get_value('Warehouse', warehouse, 'warehouse_type')	
		# 	print(warehouse_type,damage_warehouse_type)
		# 	if warehouse_type and warehouse_type==damage_warehouse_type:
		# 		previous_car_status_cf=frappe.db.get_value('Serial No', serial_no, 'car_status_cf') or None
		# 		# self.car_status_cf='Damage'
		# 		frappe.db.set_value('Serial No', serial_no, 'car_status_cf', 'Damage')
		# 		frappe.msgprint(_("VIN Number(Serial No) {0} status is changed from {1} to {2}"
		# 		.format(get_link_to_form('Serial No', serial_no),previous_car_status_cf,'Damage')), alert=True) 
		# 	else:	
		# 		previous_car_status_cf=frappe.db.get_value('Serial No', serial_no, 'car_status_cf') or None
		# 		frappe.db.set_value('Serial No', serial_no, 'car_status_cf', 'Available')
		# 		frappe.msgprint(_("VIN Number(Serial No) {0} status is changed from {1} to {2}"
		# 		.format(get_link_to_form('Serial No', serial_no),previous_car_status_cf,'Available')), alert=True)

def update_car_status(self,method):
	print('-'*10, self.doctype,method )
	if self.doctype in ['Sales Order'] and method =='on_submit':
		change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Booked')
	if self.doctype in ['Sales Order'] and method =='on_cancel':
		change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Available')


	if self.doctype =='Delivery Note' and method =='on_submit':
			if self.get("is_return") == 0:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Delivered')
			elif self.get("is_return") == 1:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Sold Out')	
	if self.doctype =='Delivery Note' and method =='on_cancel':
			if self.get("is_return") == 0:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Sold Out')
			elif self.get("is_return") == 1:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Delivered')					

	if self.doctype =='Sales Invoice' and method =='on_submit':
		if self.get("update_stock") == 1 :
			if self.get("is_return") == 0:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Sold Out')
			elif self.get("is_return") == 1:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Available')
	if self.doctype =='Sales Invoice' and method =='on_cancel':
		if self.get("update_stock") == 1:
			if self.get("is_return") == 0:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Available')	
			elif self.get("is_return") == 1:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Sold Out')
		
	if self.doctype=='Purchase Receipt' and method =='on_submit':
		if self.get("is_return") == 1:
			change_serial_no_car_status_for_serial_nos(self,new_car_status='Returned')
		elif self.get("is_return") == 0:
			change_serial_no_car_status_to_available_or_damage_for_serial_nos(self)
	if self.doctype=='Purchase Receipt' and method =='on_cancel':
		change_serial_no_car_status_for_serial_nos(self,new_car_status='Returned')

	if self.doctype=='Purchase Invoice' and method =='on_submit':
		if self.get("update_stock") == 1 : 
			if self.get("is_return") == 0:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Available')
			elif self.get("is_return") == 1:
				change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Returned')
	if self.doctype=='Purchase Invoice' and method =='on_cancel':
		if self.get("update_stock") == 1 :
			change_serial_no_car_status_for_serial_no_cf(self,new_car_status='Returned')		

	if self.doctype=='Stock Entry' and method =='on_submit':	
		if self.get("stock_entry_type")=="Material Receipt"  or self.get("stock_entry_type")=="Material Transfer":
			change_serial_no_car_status_to_available_or_damage_for_serial_nos(self)	
	if self.doctype=='Stock Entry' and method =='on_cancel':	
		if self.get("stock_entry_type")=="Material Receipt"  : 
			change_serial_no_car_status_for_serial_nos(self,new_car_status='Returned')
		elif self.get("stock_entry_type")=="Material Transfer":
			change_serial_no_car_status_to_available_or_damage_for_serial_nos(self)

	if self.doctype=='Serial No' and method =='validate':	
		print('inside SN validate....'*10)
		damage_warehouse_type = frappe.db.get_single_value('Motory Settings', 'damage_warehouse_type')
		warehouse=frappe.db.get_value('Serial No', self.name, 'warehouse')
		warehouse_type=frappe.db.get_value('Warehouse', warehouse, 'warehouse_type')
		if warehouse_type and warehouse_type==damage_warehouse_type:
			previous_car_status_cf=frappe.db.get_value('Serial No', self.name, 'car_status_cf') or None
			self.car_status_cf='Damage'
			frappe.msgprint(_("VIN Number(Serial No) for damaged warehouse {0} status is changed from {1} to {2}"
			.format( self.name,previous_car_status_cf,'Damage')), alert=True) 		
		# else:
		# 	previous_car_status_cf=frappe.db.get_value('Serial No', self.name, 'car_status_cf')
		# 	if 	previous_car_status_cf in ['Booked','Returned','Sold Out','Damage']:
		# 		self.car_status_cf='Available'
		# 		frappe.msgprint(_("VIN Number(Serial No) for non-damaged warehouse {0} status is changed from {1} to {2}"
		# 		.format( self.name,previous_car_status_cf,'Available')), alert=True) 				

def validate_damaged_warehouse(self,method):
	damage_warehouse_type = frappe.db.get_single_value('Motory Settings', 'damage_warehouse_type')

	for item in self.get("items"):
		if item.serial_no_cf:
			warehouse=frappe.db.get_value('Serial No', item.serial_no_cf, 'warehouse')
			if warehouse:
				warehouse_type=frappe.db.get_value('Warehouse', warehouse, 'warehouse_type')
				if warehouse_type and warehouse_type==damage_warehouse_type:
					frappe.throw(_("Item row {0}: is from {1} VIN Number(Serial No) which is in {2} warehouse. You cannot use it in sales cycle.")
					.format(item.idx, frappe.bold(item.serial_no_cf),frappe.bold(damage_warehouse_type))) 					

def validate_serial_no_and_qty(self,method):
	if self.doctype=='Stock Entry':
		if self.get("stock_entry_type")=="Material Receipt" :
			item_count=len(self.items)
			for item in self.items:
				if item.item_type_cf in ['New Car','Used Car']:
					if item_count>1:
							frappe.throw(_("For Material Receipt, single row is allowd for New/Used Car."))
					if item.qty>1:
							frappe.throw(_("For Material Receipt, only single qty is allowd for New/Used Car."))									
					serial_nos=get_serial_nos(item.serial_no)
					if len(serial_nos)>1:
							frappe.throw(_("Item row {0}: has {1} VIN Number(Serial No). Only single VIN Number is allowed.")
							.format(item.idx, frappe.bold(len(serial_nos))))   
		elif self.get("stock_entry_type")=="Material Transfer" :
			for item in self.items:
				if item.item_type_cf in ['New Car','Used Car']:
					if item.qty>1:
							frappe.throw(_("For Material Transfer, only single qty is allowd for New/Used Car."))						
					serial_nos=get_serial_nos(item.serial_no)
					if len(serial_nos)>1:
							frappe.throw(_("Item row {0}: has {1} VIN Number(Serial No). Only single VIN Number is allowed.")
							.format(item.idx, frappe.bold(len(serial_nos))))   	

def validate_single_serial_no(self,method):
		for item in self.items:
			serial_nos=get_serial_nos(item.serial_no)
			if len(serial_nos)>1:
					frappe.throw(_("Item row {0}: has {1} VIN Number(Serial No). Only single VIN Number is allowed.")
					.format(item.idx, frappe.bold(len(serial_nos))))   		

def validate_color(self,method):
	for item in self.items:
		if item.car_color_cf and not item.serial_no_cf:
			frappe.throw(_("Item row {0}: has missing Car Serial No. It is required for using Car Color field.")
			.format(item.idx)) 
		else:
			serial_no_color=frappe.db.get_value('Serial No', item.serial_no_cf, 'car_color_cf')
			if serial_no_color and item.car_color_cf!=serial_no_color:
				frappe.throw(_("Item row {0}: has color {1}, whereas color in VIN Number(Serial No) is {2}. It should match.")
				.format(item.idx, frappe.bold(item.car_color_cf or None),frappe.bold(serial_no_color))) 

def before_save(self,method):
	if self.doctype in ['Sales Order','Sales Invoice']:
		margins = []
		discounts = []
		for item in self.get("items"):
			if item.get("serial_no_cf"):
				if not item.get("purchase_rate"):
					item.purchase_rate = frappe.db.get_value("Serial No",item.get("serial_no_cf"),"purchase_rate")
				margins.append(round(((item.rate - item.purchase_rate or 0)/item.rate)*100,2))
			if item.discount_percentage:
				discounts.append(item.discount_percentage)

		if margins:
			self.margin = min(margins)
		if discounts:
			self.discount = max(discounts)


@frappe.whitelist()
def create_stock_entry(sales_order):
	sales_order = frappe.get_doc(json.loads(sales_order))
	existing_se_list=frappe.db.get_list('Stock Entry Detail', filters={'sales_order_cf': sales_order.get("name")},fields=['parent'])	

	if len(existing_se_list)>0:
		return frappe.msgprint(_("Stock Entry {0} has been already created against this Sales Order".format(existing_se_list)))

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = 'Material Transfer'
	stock_entry.set_stock_entry_type()
	# stock_entry.to_warehouse=
	for so_item in sales_order.get("items"):
		se_item=stock_entry.append("items",{})
		se_item.item_code=so_item.item_code
		se_item.item_name=so_item.item_name
		se_item.car_color_cf=so_item.car_color_cf
		se_item.serial_no=so_item.serial_no_cf
		se_item.car_plate_no_cf=so_item.car_plate_no_cf
		se_item.car_odometer_cf=so_item.car_odometer_cf
		se_item.t_warehouse=None
		se_item.s_warehouse=frappe.db.get_value('Serial No', so_item.serial_no_cf, 'warehouse') or None
		se_item.car_source_cf=frappe.db.get_value('Serial No', so_item.serial_no_cf, 'car_source_cf') or None
		se_item.car_parking_no_cf=frappe.db.get_value('Serial No', so_item.serial_no_cf, 'car_parking_no_cf') or None
		se_item.car_line_no_cf=frappe.db.get_value('Serial No', so_item.serial_no_cf, 'car_line_no_cf') or None
		se_item.item_type_cf=so_item.item_type_cf
		se_item.qty=so_item.qty
		se_item.transfer_qty=so_item.qty
		se_item.uom=so_item.uom
		se_item.stock_uom=so_item.stock_uom
		se_item.conversion_factor=so_item.conversion_factor
		se_item.sales_order_cf=sales_order.get("name")
		se_item.sales_order_detail_cf=so_item.get("name")
	stock_entry.set_missing_values()
	return stock_entry.as_dict()					


    # for row in self.items:
    #     cost_center = row.cost_center
    #     item_type= row.item_type_cf
    #     result = frappe.get_all(
    #         'Child Config',
    #         filters={
    #             'parent': 'Config',
    #             'cost_center': cost_center,
	# 			'item_type_cf': item_type,
    #             'doctype_': 'Purchase Invoice'
    #         },
    #         fields=['account']
    #     )
        
    #     if result:
    #         row.expense_account = result[0]['account'] if result else None