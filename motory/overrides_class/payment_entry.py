import frappe
from frappe import _
from frappe import ValidationError, _, scrub, throw
from frappe.utils import cint, comma_or, flt, getdate, nowdate
from erpnext.accounts.doctype.invoice_discounting.invoice_discounting import (
	get_party_account_based_on_invoice_discounting,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry,InvalidPaymentEntry

class CustomPaymentEntry(PaymentEntry):
    def validate_reference_documents(self):
        if self.party_type == "Student":
            valid_reference_doctypes = ("Fees")
        elif self.party_type == "Customer":
            valid_reference_doctypes = ("Sales Order", "Sales Invoice", "Journal Entry", "Dunning")
        elif self.party_type == "Supplier":
            valid_reference_doctypes = ("Purchase Order", "Purchase Invoice", "Journal Entry", "Expenses")
        elif self.party_type == "Employee":
            valid_reference_doctypes = ("Expense Claim", "Journal Entry", "Employee Advance", "Gratuity")
        elif self.party_type == "Shareholder":
            valid_reference_doctypes = ("Journal Entry")
        elif self.party_type == "Donor":
            valid_reference_doctypes = ("Donation")

        for d in self.get("references"):
            if not d.allocated_amount:
                continue
            if d.reference_doctype not in valid_reference_doctypes:
                frappe.throw(_("Reference Doctype must be one of {0}")
                    .format(comma_or(valid_reference_doctypes)))

            elif d.reference_name:
                if not frappe.db.exists(d.reference_doctype, d.reference_name):
                    frappe.throw(_("{0} {1} does not exist").format(d.reference_doctype, d.reference_name))
                else:
                    ref_doc = frappe.get_doc(d.reference_doctype, d.reference_name)

                    if d.reference_doctype != "Journal Entry":
                        if self.party != ref_doc.get(scrub(self.party_type)):
                            frappe.throw(_("{0} {1} is not associated with {2} {3}")
                                .format(d.reference_doctype, d.reference_name, self.party_type, self.party))
                    else:
                        self.validate_journal_entry()

                    if d.reference_doctype in ("Sales Invoice", "Purchase Invoice", "Expense Claim", "Fees"):
                        if self.party_type == "Customer":
                            ref_party_account = get_party_account_based_on_invoice_discounting(d.reference_name) or ref_doc.debit_to
                        elif self.party_type == "Student":
                            ref_party_account = ref_doc.receivable_account
                        elif self.party_type=="Supplier":
                            ref_party_account = ref_doc.credit_to
                        elif self.party_type=="Employee":
                            ref_party_account = ref_doc.payable_account

                        if ref_party_account != self.party_account:
                                frappe.throw(_("{0} {1} is associated with {2}, but Party Account is {3}")
                                    .format(d.reference_doctype, d.reference_name, ref_party_account, self.party_account))

                    if ref_doc.docstatus != 1:
                        frappe.throw(_("{0} {1} must be submitted")
                            .format(d.reference_doctype, d.reference_name))

    def update_advance_paid(self):
        if self.payment_type in ("Receive", "Pay") and self.party:
            for d in self.get("references"):
                if d.allocated_amount \
                    and d.reference_doctype in ("Sales Order", "Purchase Order", "Employee Advance", "Gratuity", "Expenses"):
                        frappe.get_doc(d.reference_doctype, d.reference_name).set_total_advance_paid()

    def validate_payment_against_negative_invoice(self):
        return
        if ((self.payment_type=="Pay" and self.party_type=="Customer")
                or (self.payment_type=="Receive" and self.party_type=="Supplier")):

            total_negative_outstanding = sum(abs(flt(d.outstanding_amount))
                for d in self.get("references") if flt(d.outstanding_amount) < 0)

            paid_amount = self.paid_amount if self.payment_type=="Receive" else self.received_amount
            additional_charges = sum([flt(d.amount) for d in self.deductions])

            if not total_negative_outstanding:
                frappe.throw(_("Cannot {0} {1} {2} without any negative outstanding invoice")
                    .format(self.payment_type, ("to" if self.party_type=="Customer" else "from"),
                        self.party_type), InvalidPaymentEntry)

            elif paid_amount - additional_charges > total_negative_outstanding:
                frappe.throw(_("Paid Amount cannot be greater than total negative outstanding amount {0}")
                    .format(total_negative_outstanding), InvalidPaymentEntry)
