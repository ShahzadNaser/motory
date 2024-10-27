import frappe
from frappe import _
import json
from frappe.utils import get_link_to_form
from frappe.utils import  getdate, today, flt, get_datetime


@frappe.whitelist()
def add(invoice=None):
    response = {}
    params = get_post_params()
    if not params:
        return {"success":False,"message":"No request payload found"}
    if not params.get("reference_id"):
        return {"success":False,"message":"Reference ID missing in payload"}
    if params.get("reference_id"):
        jv = frappe.db.get_value("Journal Entry",{"cheque_no":params.get("reference_id")})
        if jv:
            return {"success":False,"message":"Reference ID {} is already linked with an payment {} in ERP.".format(params.get("reference_id"),jv)}
        
    try:
        jv = frappe.new_doc("Journal Entry")
        jv.company = frappe.defaults.get_global_default("company")
        jv.posting_date = getdate(params.get("invoice_date"))
        jv.cheque_no = params.get("reference_id")
        jv.user_remark = "Advance Payment"
        # jv.cost_center = "1004 - Marketing Services - ALJTech"
        jv.append("accounts",{
            'account': "1112039 - Al Rajhi Bank - Current Account - ALJ Technology",  
            'debit_in_account_currency':flt(params.get("amount")),
            'credit_in_account_currency':flt(0),
            # 'cost_center': "1004 - Marketing Services - ALJTech"
        })
        jv.append("accounts",{
            'account': "1112039 - Al Rajhi Bank - Current Account - ALJ Technology",  
            'debit_in_account_currency':flt(0),
            'credit_in_account_currency':flt(params.get("amount")),
            'party_type':"Customer",
            'party':"ADVANCE PAYMENT CUSTOMER",
            # 'cost_center': "1004 - Marketing Services - ALJTech"
        })
        jv.flags.ignore_permissions = 1
        jv.insert()
        jv.submit()
        frappe.db.commit()  # Commit to save the payment entry
        return {
                "success":True,
                "invoice":jv.name,
                "invoice_pdf_ar": "{}/api/method/motory.payment.pdf?invoice={}&_lang=ar".format(str(frappe.utils.get_url()),jv.name),
                "invoice_pdf_en": "{}/api/method/motory.payment.pdf?invoice={}&_lang=en".format(str(frappe.utils.get_url()),jv.name),
                "message":"Payment successfully added"
            }
    except Exception as e:
        frappe.log_error("Error on Adding payment",frappe.get_traceback())
        return {"success":False,"message":"Something went wroung please ask administrator to check logs"}


def get_post_params():
    return json.loads(frappe.request.data)

@frappe.whitelist(allow_guest=True)
def pdf(invoice=None,lang="en"):
    from frappe.utils.pdf import get_pdf
    try:
        html = frappe.get_print("Sales Invoice", invoice, "Motory.com Invoice", doc=frappe.get_doc("Sales Invoice",invoice), no_letterhead=0)
        options = {
            # "margin-right":"0mm",
            # "margin-left" :"0mm"
        }
        frappe.local.response.filename = "{}.pdf".format(invoice)
        frappe.local.response.filecontent = get_pdf(html,options=options)
        frappe.local.response.type = "pdf"
    except Exception as e:
        frappe.log_error("Error on getting print",frappe.get_traceback())
        return {"success":False,"message":"Something went wroung please ask administrator to check logs"}
