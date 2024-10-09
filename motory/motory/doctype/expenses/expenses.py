# Copyright (c) 2024, Shahzad Naser and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, formatdate,nowdate
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from erpnext.accounts.utils import get_fiscal_years


class Expenses(Document):
	def validate(self):
		# return
		self.status = "Draft"
		self.base_grand_total = 0
		self.total_taxes_and_charges = 0
		cn_or_vin = True 
		for row in self.get("expenses"):
			if not row.get("car_plate_no") and not row.get("serial_no") and not row.get("general_expense"):
				cn_or_vin = False
			self.base_grand_total += flt(row.get("amount"))
			if row.get("tax_rate"):
				row.tax_amount = flt(row.get("amount") * (row.get("tax_rate")/100)) or 0
    
			self.total_taxes_and_charges += flt(row.tax_amount)
			row.net_amount = flt(row.tax_amount) + flt(row.get("amount"))

		self.grand_total = flt(self.base_grand_total) + flt(self.total_taxes_and_charges)
		self.outstanding_amount = flt(self.grand_total) - flt(self.advance_paid)

		if not cn_or_vin:
			frappe.throw("Car Plate No. or Serial No must required in Expenses")

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
			if item.get("car_plate_no"):
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
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.credit_account,
						"credit": self.grand_total,
						"credit_in_account_currency": self.grand_total,
						"party": self.supplier,
						"voucher_type": "Expenses",
						"voucher_no": self.name,
						"posting_date": self.posting_date,
						"company": self.company,
						"party_type": "Supplier",
						"party": self.supplier,
						"cost_center": self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or ""
					},
					item=self,
				)
			)

			for item in self.expenses:
				serial_no = item.get("serial_no") or frappe.db.get_value('Serial No', {"car_plate_no_cf":item.get("car_plate_no")}, 'name') or ""
				sales_invoice = frappe.db.get_value('Sales Invoice Item', {"serial_no":serial_no,"docstatus":1}, 'parent') or frappe.db.get_value('Sales Invoice Item', {"car_plate_no_cf":serial_no,"docstatus":1}, 'parent') or ""
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": item.expense_account if sales_invoice else  item.account ,
							"debit": item.amount,
							"debit_in_account_currency": item.amount,
							"party_type": "Supplier",
							"against_voucher_type": "Expenses",
							"against_voucher": self.name,
							"cost_center": item.get("cost_center") or self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or "",
							"posting_date": self.posting_date,
							"company": self.company,
							"remarks": item.get("car_plate_no"),							
							"serial_no":serial_no
						},
						item=self,
					)
				)
				if item.get("tax_amount"):
					if item.account_head not in taxes:
						taxes[item.account_head] = flt(0)
					taxes[item.account_head] += flt(item.tax_amount)

			if taxes:
				for account_head in taxes: 
					gl_entries.append(self.get_gl_dict(
						{
							"account": account_head,
							"debit": taxes.get(account_head,0),
							"debit_in_account_currency": taxes.get(account_head,0),
							"against": self.credit_account,
							"against_voucher_type": "Expenses",
							"against_voucher": self.name,
							"cost_center": self.get("cost_center") or frappe.db.get_value("Company",self.company,"cost_center") or "",
							"posting_date": self.posting_date,
							"company": self.company
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

	def set_total_advance_paid(self):
		paid_amount = frappe.db.sql("""
			select ifnull(sum(debit), 0) as paid_amount
			from `tabGL Entry`
			where against_voucher_type = 'Expenses'
				and against_voucher = %s
				and party_type = 'Supplier'
				and party = %s
				and is_cancelled=0
		""", (self.name, self.supplier), as_dict=1)[0].paid_amount

		outsanding_amount = flt(self.grand_total) - flt(paid_amount)
		self.db_set("advance_paid", paid_amount)
		self.db_set("outstanding_amount", outsanding_amount)
		status = "Paid"
		if outsanding_amount == self.grand_total:
			status = "Unpaid"
		elif  0 < outsanding_amount < self.grand_total:
			status = "Partly Paid"

		frappe.db.set_value("Expenses", self.name , "status", status)

@frappe.whitelist()
def get_tax_details(item_tax_template=None):
	tax_details = {"account":"","tax_rate":0}
	if item_tax_template:
		tax_templates = frappe.db.get_value("Item Tax Template Detail",{"parent":item_tax_template},["tax_type as account","tax_rate"],as_dict=True)
		if tax_templates:
			return tax_templates
	return tax_details

@frappe.whitelist()
def get_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
	from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

	doc = frappe.get_doc(dt, dn)

	party_account = doc.get("credit_account")
	party_account_currency = doc.get("currency")
	payment_type = "Pay"

	outstanding_amount = flt(doc.grand_total) - flt(doc.advance_paid)

	paid_amount = received_amount = abs(outstanding_amount)
	# bank or cash
	bank = get_default_bank_cash_account(doc.company, "Bank", mode_of_payment="Bank Draft",account=bank_account)

	if not bank:
		bank = get_default_bank_cash_account(doc.company, "Cash", mode_of_payment="Cash",account=bank_account)
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Supplier"
	pe.party = doc.get("supplier")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type == "Receive" else bank.account
	pe.paid_to = party_account if payment_type == "Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type == "Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount

	bank_account = get_party_bank_account(pe.party_type, pe.party)
	pe.set("bank_account", bank_account)
	pe.set_bank_account_data()

	pe.append("references", {
		'reference_doctype': dt,
		'reference_name': dn,
		"bill_no": doc.get("name"),
		"due_date": doc.get("posting_date"),
		'total_amount': doc.grand_total,
		'outstanding_amount': outstanding_amount,
		'allocated_amount': outstanding_amount
	})

	pe.setup_party_account_field()
	pe.set_missing_values()
	if party_account and bank:
		pe.set_exchange_rate()
		pe.set_amounts()
	return pe
