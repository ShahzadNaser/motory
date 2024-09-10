import frappe
from frappe import _, msgprint
from frappe.utils import cint, flt
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def get_gl_entries(self, warehouse_account=None):
        from erpnext.accounts.general_ledger import merge_similar_entries

        gl_entries = []

        self.make_customer_gl_entry(gl_entries)

        self.make_tax_gl_entries(gl_entries)
        self.make_exchange_gain_loss_gl_entries(gl_entries)
        self.make_internal_transfer_gl_entries(gl_entries)

        self.make_item_gl_entries(gl_entries)
        self.make_discount_gl_entries(gl_entries)

        # merge gl entries before adding pos entries
        gl_entries = merge_similar_entries(gl_entries)

        self.make_loyalty_point_redemption_gle(gl_entries)
        self.make_pos_gl_entries(gl_entries)

        self.make_write_off_gl_entry(gl_entries)
        self.make_gle_for_rounding_adjustment(gl_entries)
        self.make_expenses_entries(gl_entries)

        return gl_entries
  
    def make_expenses_entries(self,gl_entries):
        frappe.log_error(title="testin11111",message = str("1111111111"))
        if cint(self.update_stock):
            frappe.log_error(title="testin22222",message = str("2222222"))
            serial_nos_cond = "" 
            car_plate_nos_cond = ""
            cond = " docstatus = 1 "
            expenses = frappe._dict({})
            for item in self.get("items"):
                if item.get("serial_no"):
                    serial_nos_cond += '"{}",'.format(item.get("serial_no"))
                if item.get("car_plate_no_cf"):
                    car_plate_nos_cond += '"{}",'.format(item.get("car_plate_no_cf"))
            if serial_nos_cond:
                cond += " and serial_no in ({})".format(serial_nos_cond[:-1]) 

            if car_plate_nos_cond:
                cond += " {} car_plate_no in ({})".format("OR" if serial_nos_cond else "AND",car_plate_nos_cond[:-1])

            for row in frappe.db.sql(""" SELECT serial_no,car_plate_no,amount,account,expense_account from `tabExpense Item` where {}""".format(cond),as_dict=True,debug=True):
                serial_no = row.get("serial_no") or frappe.db.get_value("Serial No",{"car_plate_no_cf":row.get("car_plate_no")}) or row.get("car_plate_no")
                if serial_no not in expenses:
                    expenses[serial_no] = []
                expenses[serial_no].append(row)
            frappe.log_error(title="testin1",message = str(expenses))
            for item in self.get("items"):
                if expenses.get(item.get("serial_no")) or expenses.get(item.get("car_plate_no_cf")):
                    for row in expenses.get(item.get("serial_no")) or expenses.get(item.get("car_plate_no_cf")):
                        account_currency = get_account_currency(row.get("account"))
                        gl_entries.append(
                            self.get_gl_dict(
                                {
                                    "account": row.get("account"),
                                    "against": self.customer,
                                    "credit": flt(row.get("amount"), item.precision("base_net_amount")),
                                    "credit_in_account_currency": flt(row.get("amount"), item.precision("base_net_amount")),
                                    "cost_center": row.cost_center or item.cost_center or self.cost_center,
                                    "project": item.project or self.project,
                                },
                                account_currency,
                                item=item,
                            )
                        )
                        gl_entries.append(
                            self.get_gl_dict(
                                {
                                    "account": row.get("expense_account"),
                                    "against": self.customer,
                                    "debit": flt(row.get("amount"), item.precision("base_net_amount")),
                                    "debit_in_account_currency": flt(row.get("amount"), item.precision("base_net_amount")),
                                    "cost_center": row.cost_center or item.cost_center or self.cost_center,
                                    "project": item.project or self.project,
                                },
                                account_currency,
                                item=item,
                            )
                        )