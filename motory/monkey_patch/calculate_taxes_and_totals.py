import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

def calculate_net_total(self):
    self.doc.total_qty = self.doc.total = self.doc.base_total = self.doc.net_total = self.doc.base_net_total = 0.0

    temp_list = ["total", "base_total", "net_total", "base_net_total"]

    if frappe.get_meta(self.doc.doctype).get_field("net_profit_margin"):
        self.doc.net_profit_margin = 0.0
        temp_list.append("net_profit_margin")

    for item in self.doc.get("items"):
        self.doc.total += item.amount
        self.doc.total_qty += item.qty
        self.doc.base_total += item.base_amount
        self.doc.net_total += item.net_amount
        self.doc.base_net_total += item.base_net_amount
        if frappe.get_meta(self.doc.doctype).get_field("net_profit_margin"):
            self.doc.net_profit_margin +=  (item.rate - item.get("purchase_rate" or 0) * item.qty)

    # print("==================calculate_net_total=========================")
    self.doc.round_floats_in(self.doc, temp_list)

def get_current_tax_amount(self, item, tax, item_tax_map):
    tax_rate = self._get_tax_rate(tax, item_tax_map)
    current_tax_amount = 0.0

    if tax.charge_type == "Actual":
        # distribute the tax amount proportionally to each item row
        actual = flt(tax.tax_amount, tax.precision("tax_amount"))
        current_tax_amount = item.net_amount*actual / self.doc.net_total if self.doc.net_total else 0.0

    elif tax.charge_type == "On Net Total":
        current_tax_amount = (tax_rate / 100.0) * item.net_amount
    elif tax.charge_type == "On Previous Row Amount":
        current_tax_amount = (tax_rate / 100.0) * \
            self.doc.get("taxes")[cint(tax.row_id) - 1].tax_amount_for_current_item
    elif tax.charge_type == "On Previous Row Total":
        current_tax_amount = (tax_rate / 100.0) * \
            self.doc.get("taxes")[cint(tax.row_id) - 1].grand_total_for_current_item
    elif tax.charge_type == "On Item Quantity":
        current_tax_amount = tax_rate * item.qty

    elif tax.charge_type == "On Profit Margin":
        current_tax_amount = (tax_rate / 100.0) * (item.net_amount - ((item.get("purchase_rate") or 0) * item.qty))

    if not (self.doc.get("is_consolidated") or tax.get("dont_recompute_tax")):
        self.set_item_wise_tax(item, tax, tax_rate, current_tax_amount)

    # print("==================get_current_tax_amount=========================")

    return current_tax_amount

def patch(doc,method):
    calculate_taxes_and_totals.get_current_tax_amount = get_current_tax_amount
    calculate_taxes_and_totals.calculate_net_total = calculate_net_total