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
    if not params.get("customer_name") and not params.get("customer_name_en"):
        return {"success":False,"message":"Customer Name required in english and arabic."}
    if params.get("customer_type")=="dealer" and not params.get("company_name") and not params.get("company_name_en"):
        return {"success":False,"message":"Company Name required in english and arabic."}
    if not params.get("mazad_user_id"):
        return {"success":False,"message":"Mazad User ID must required."}
    if not params.get("amount"):
        return {"success":False,"message":"Amount is required."}
    if params.get("reference_id"):
        jv = frappe.db.get_value("Journal Entry",{"cheque_no":params.get("reference_id")})
        if jv:
            return {"success":False,"message":"Reference ID {} is already linked with an payment {} in ERP.".format(params.get("reference_id"),jv)}
        
    try:
        # Create the customer
        party = frappe.db.get_value("Customer",{"mazad_user_id": params.get("mazad_user_id")},"name")
        if not party:
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": params.get("company_name_en") or params.get("company_name") if params.get("customer_type")=="dealer" else params.get("customer_name_en") or params.get("customer_name"),
                "customer_name_in_arabic": params.get("company_name") if params.get("customer_type")=="dealer" else params.get("customer_name"),
                "iban": params.get("iban"),
                "personal_id": params.get("national_id"),
                "mazad_user_id": params.get("mazad_user_id"),
                "commercial_number": params.get("cr_number"),
                "customer_type": "Company" if params.get("customer_type")=="dealer" else "Individual",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "custom_b2c":  0 if params.get("customer_type")=="dealer" else 1
            })
            if params.get("customer_type")=="dealer":
                customer.representative = params.get("customer_name_en")
                customer.representative_arabic = params.get("customer_name")
            customer.flags.ignore_permissions = 1
            customer.insert()
            frappe.db.commit()  # Commit to save the customer
            party = customer.name		

        jv = frappe.new_doc("Journal Entry")
        jv.company = frappe.defaults.get_global_default("company")
        jv.posting_date = getdate(params.get("posting_date"))
        jv.cheque_date = getdate(params.get("posting_date"))
        jv.cheque_no = params.get("reference_id")
        jv.user_remark = "Advance Payment"
        # jv.cost_center = "1004 - Marketing Services - ALJTech"
        jv.append("accounts",{
            'account': "1112039 - Al Rajhi Bank - Current Account - ALJ Technology",  
            'debit_in_account_currency':flt(params.get("amount")),
            'credit_in_account_currency':flt(0),
        })
        jv.append("accounts",{
            'account': "1142001 - Account Receivable - ALJ Technology",  
            'debit_in_account_currency':flt(0),
            'credit_in_account_currency':flt(params.get("amount")),
            'party_type':"Customer",
            'party':party,
            'is_advance':"Yes"
        })
        jv.flags.ignore_permissions = 1
        jv.insert()
        jv.submit() 
        frappe.db.commit()  # Commit to save the payment entry
        return {
                "success":True,
                "invoice":jv.name,
                "invoice_pdf_ar": "{}/api/method/motory.payment.pdf?id={}&_lang=ar".format(str(frappe.utils.get_url()),jv.name),
                "invoice_pdf_en": "{}/api/method/motory.payment.pdf?id={}&_lang=en".format(str(frappe.utils.get_url()),jv.name),
                "message":"Payment successfully added"
            }
    except Exception as e:
        frappe.log_error("Error on Adding payment",frappe.get_traceback())
        return {"success":False,"message":"Something went wroung please ask administrator to check logs"}

@frappe.whitelist()
def refund(invoice=None):
    response = {}
    params = get_post_params()
    if not params:
        return {"success":False,"message":"No request payload found"}
    if not params.get("mazad_user_id"):
        return {"success":False,"message":"Mazad User ID must required."}
    if not params.get("amount"):
        return {"success":False,"message":"Amount is required."}
    if params.get("reference_id"):
        jv = frappe.db.get_value("Journal Entry",{"cheque_no":params.get("reference_id")})
        if jv:
            return {"success":False,"message":"Reference ID {} is already linked with an payment {} in ERP.".format(params.get("reference_id"),jv)}
        
    try:
        # Create the customer
        party = frappe.db.get_value("Customer",{"mazad_user_id": params.get("mazad_user_id")},"name")
        if not party:
            {"success":False,"message":"Customer not found against Mazad User ID."}

        jv = frappe.new_doc("Journal Entry")
        jv.company = frappe.defaults.get_global_default("company")
        jv.posting_date = getdate(params.get("posting_date"))
        jv.cheque_date = getdate(params.get("posting_date"))
        jv.cheque_no = params.get("reference_id")
        jv.user_remark = "Refund Advance Payment"
        jv.append("accounts",{
            'account': "1112039 - Al Rajhi Bank - Current Account - ALJ Technology",  
            'debit_in_account_currency':flt(0),
            'credit_in_account_currency':flt(params.get("amount")),
        })
        jv.append("accounts",{
            'account': "1142001 - Account Receivable - ALJ Technology",  
            'debit_in_account_currency':flt(params.get("amount")),
            'credit_in_account_currency':flt(0),
            'party_type':"Customer",
            'party':party,
            'is_advance':"No"
        })
        jv.flags.ignore_permissions = 1
        jv.insert()
        jv.submit()
        frappe.db.commit()  # Commit to save the payment entry
        return {
                "success":True,
                "invoice":jv.name,
                "invoice_pdf_ar": "{}/api/method/motory.payment.pdf?id={}&_lang=ar".format(str(frappe.utils.get_url()),jv.name),
                "invoice_pdf_en": "{}/api/method/motory.payment.pdf?id={}&_lang=en".format(str(frappe.utils.get_url()),jv.name),
                "message":"Payment successfully added"
            }
    except Exception as e:
        frappe.log_error("Error on Adding payment",frappe.get_traceback())
        return {"success":False,"message":"Something went wroung please ask administrator to check logs"}


def get_post_params():
    return json.loads(frappe.request.data)

@frappe.whitelist(allow_guest=True)
def pdf(id=None,lang="en"):
    from frappe.utils.pdf import get_pdf
    try:
        html = frappe.get_print("Journal Entry", id, "Advance Payment Template", doc=frappe.get_doc("Journal Entry",id), no_letterhead=0)
        options = {
            # "margin-right":"0mm",
            # "margin-left" :"0mm"
        }
        frappe.local.response.filename = "{}.pdf".format(id)
        frappe.local.response.filecontent = get_pdf(html,options=options)
        frappe.local.response.type = "pdf"
    except Exception as e:
        frappe.log_error("Error on getting print",frappe.get_traceback())
        return {"success":False,"message":"Something went wroung please ask administrator to check logs"}
