# Copyright (c) 2024, Shahzad Naser and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, formatdate
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from erpnext.accounts.utils import get_fiscal_years


class Expenses(Document):
	def validate(self):
		# return
		self.base_grand_total = 0
		self.total_taxes_and_charges = 0
  
		for row in self.get("expenses"):
			self.base_grand_total += flt(row.get("amount"))
			if row.get("tax_rate"):
				row.tax_amount = flt(row.get("amount") * (row.get("tax_rate")/100)) or 0
    
			self.total_taxes_and_charges += flt(row.tax_amount)
			row.net_amount = flt(row.tax_amount) + flt(row.get("amount"))
		self.grand_total = flt(self.base_grand_total) + flt(self.total_taxes_and_charges)
		self.outstanding_amount = self.grand_total - self.advance_paid

	def before_submit(self):
		self.status = "Unpaid"
	def before_cancel(self):
		self.status = "Cancelled"

	def on_submit(self):
		# self.create_gl_entries()
		self.make_gl_entries()
		self.update_serial_no()

	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Payment Entry",
			"Journal Entry",
			"Payment Ledger Entry"
		)
		self.make_gl_entries(cancel=1)
		self.update_serial_no(cancel=1)

	def update_serial_no(self,cancel=0):
		update_dict = frappe._dict({})
		for item in self.expenses:
			if not update_dict.get(item.get("car_plate_no")):
				update_dict[item.get("car_plate_no")] = item.get("net_amount") or 0
			else:
				update_dict[item.get("car_plate_no")] += item.get("net_amount") or 0

		for car_plate_no in update_dict:
			expense = frappe.db.get_value('Serial No', {"car_plate_no_cf":car_plate_no}, 'total_expense_cf') or 0
			total_expense =  flt(expense)+flt(update_dict.get(car_plate_no))
			if cancel:
				total_expense =  flt(expense) - flt(update_dict.get(car_plate_no))

			frappe.db.set_value('Serial No', {"car_plate_no_cf":car_plate_no} , 'total_expense_cf',total_expense)
			frappe.db.commit()

	def make_gl_entries(self, cancel=False):
		gl_entries = self.get_gl_entries()
		for gl in gl_entries:
			print(gl)
		make_gl_entries(gl_map=gl_entries, cancel=cancel,merge_entries=False)

	def get_gl_entries(self):
		gl_entries = []
		taxes = {}
		if self.get("expenses"):
			for item in self.expenses:
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": self.credit_account,
							"credit": item.net_amount,
							"credit_in_account_currency": item.net_amount,
							"against": item.account,
							"voucher_type": "Expenses",
							"voucher_no": self.name,
							"posting_date": self.posting_date,
							"company": self.company,
							"party_type": "Supplier",
							"party": self.supplier,
							"cost_center": self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or "",
							"remarks": item.get("car_plate_no")
						},
						item=self,
					)
				)

				gl_entries.append(
					self.get_gl_dict(
						{
							"account": item.account,
							"debit": item.amount,
							"debit_in_account_currency": item.amount,
							"against": self.credit_account,
							"against_voucher_type": "Expenses",
							"against_voucher": self.name,
							"cost_center": item.get("cost_center") or self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or "",
							"posting_date": self.posting_date,
							"company": self.company,
							"remarks": item.get("car_plate_no"),							
						},
						item=self,
					)
				)
				if item.get("tax_amount"):
					gl_entries.append(self.get_gl_dict(
						{
							"account": item.account_head,
							"debit": item.tax_amount,
							"debit_in_account_currency": item.tax_amount,
							"against": self.credit_account,
							"against_voucher_type": "Expenses",
							"against_voucher": self.name,
							"cost_center": item.get("cost_center") or self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or "",
							"posting_date": self.posting_date,
							"company": self.company,
							"remarks": item.get("car_plate_no"),							
						},
						item=self,
					))
			return gl_entries

	def get_gl_dict(self, args, account_currency=None, item=None):
		"""this method populates the common properties of a gl entry record"""

		posting_date = args.get('posting_date') or self.get('posting_date')
		fiscal_years = get_fiscal_years(posting_date, company=self.company)
		if len(fiscal_years) > 1:
			frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
				formatdate(posting_date)))
		else:
			fiscal_year = fiscal_years[0][0]

		gl_dict = frappe._dict({
			'company': self.company,
			'posting_date': posting_date,
			'fiscal_year': fiscal_year,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'remarks': self.get("remarks") or "",
			'debit': 0,
			'credit': 0,
			'debit_in_account_currency': 0,
			'credit_in_account_currency': 0,
			'is_opening': self.get("is_opening") or "No",
			'party_type': None,
			'party': None
		})

		accounting_dimensions = get_accounting_dimensions()
		dimension_dict = frappe._dict()

		for dimension in accounting_dimensions:
			dimension_dict[dimension] = self.get(dimension)
			if item and item.get(dimension):
				dimension_dict[dimension] = item.get(dimension)

		gl_dict.update(dimension_dict)
		gl_dict.update(args)

		return gl_dict


@frappe.whitelist()
def get_tax_details(item_tax_template=None):
	tax_details = {"account":"","tax_rate":0}
	if item_tax_template:
		tax_templates = frappe.db.get_value("Item Tax Template Detail",{"parent":item_tax_template},["tax_type as account","tax_rate"],as_dict=True)
		if tax_templates:
			return tax_templates
	return tax_details