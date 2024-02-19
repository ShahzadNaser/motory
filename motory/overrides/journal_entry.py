import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry

class CustomJournalEntry(JournalEntry):
    def make_gl_entries(self, cancel=0, adv_adj=0):
        from erpnext.accounts.general_ledger import make_gl_entries

        gl_map = []
        for d in self.get("accounts"):
            if d.debit or d.credit:
                r = [d.user_remark, self.remark]
                r = [x for x in r if x]
                remarks = "\n".join(r)

                gl_map.append(
                    self.get_gl_dict({
                        "account": d.account,
                        "party_type": d.party_type,
                        "due_date": self.due_date,
                        "party": d.party,
                        "against": d.against_account,
                        "debit": flt(d.debit, d.precision("debit")),
                        "credit": flt(d.credit, d.precision("credit")),
                        "account_currency": d.account_currency,
                        "debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
                        "credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
                        "against_voucher_type": d.reference_type,
                        "against_voucher": d.reference_name,
                        "remarks": remarks,
                        "voucher_detail_no": d.reference_detail_no,
                        "cost_center": d.cost_center,
                        "project": d.project,
                        "finance_book": self.finance_book
                    }, item=d)
                )

        if self.voucher_type in ('Deferred Revenue', 'Deferred Expense'):
            update_outstanding = 'No'
        else:
            update_outstanding = 'Yes'

        if gl_map:
            make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, update_outstanding=update_outstanding, merge_entries=False)