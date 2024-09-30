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
    if not params.get("service_type") or params.get("service_type") not in ["Marketing","Valuation"]:
        return {"success":False,"message":"Service Type must be one of Marketing or Valuation"}
    if not params.get("reference_id"):
        return {"success":False,"message":"Reference ID missing in payload"}
    if params.get("reference_id"):
        sales_invoice = frappe.db.get_value("Sales Invoice",{"reference_id":params.get("reference_id")})
        if sales_invoice:
            return {"success":False,"message":"Reference ID {} is already linked with an invoice {} in ERP.".format(params.get("reference_id"),sales_invoice)}
        
    try:
        si = frappe.new_doc("Sales Invoice")
        si.company = frappe.defaults.get_global_default("company")
        si.posting_date = getdate(params.get("invoice_date"))
        si.due_date = getdate(params.get("invoice_date"))
        si.update_stock = 0
        si.set_posting_time = 1
        si.reference_id = params.get("reference_id")
        si.cost_center = "1004 - Marketing Services - ALJTech"
        if params.get("service_type") == "Marketing":
            si.customer = "الايرادات من الاعلانت الخدمة الذاتية"
        elif params.get("service_type") == "Valuation":
            si.customer = "Motory Vehicle Premium Valuation Service"
        si.customer_details = "{}{}{}\n{} \n{}".format(params.get("customer_name_en"),"\n" if params.get("customer_name_ar") else "",params.get("customer_name_ar"),params.get("email"),params.get("cell_no"))
        si.append("items",{
            'item_code': "Marketing Services - خدمات التسويق",
            'item_name':"Marketing Services - خدمات التسويق",
            'uom':'Nos',
            'qty':  1,
            'rate':flt(flt(params.get("amount"))/1.15),
            'item_tax_template': "B1 - KSA Sales VAT 15% - مبيعات"
        })
        si.taxes_and_charges = "B1 - Goods / Services Domestic Supply 15%"
        si.set("payment_schedule",[])
        si.flags.ignore_permissions = 1
        si.insert()
        si.submit()
        frappe.db.commit()  # Commit to save the payment entry
        return {
                "success":True,
                "invoice":si.name,
                "invoice_pdf_ar": "{}/api/method/motory.sales_invoice.pdf?invoice={}&_lang=ar".format(str(frappe.utils.get_url()),si.name),
                "invoice_pdf_en": "{}/api/method/motory.sales_invoice.pdf?invoice={}&_lang=en".format(str(frappe.utils.get_url()),si.name),
                "message":"Invoice successfully created"
            }
    except Exception as e:
        frappe.log_error("Error on Creating Customer",frappe.get_traceback())
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
