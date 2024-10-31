import frappe
from frappe import _
import json
from frappe.utils import get_link_to_form
from frappe.utils import  getdate, today, flt, get_datetime


@frappe.whitelist()
def add_marketing_invoice(invoice=None):
    response = {}
    params = get_post_params()
    if not params:
        return {"success":False,"message":"No request payload found"}
    if not params.get("service_type"):
        return {"success":False,"message":"Service Type is missing in payload"}
    if not params.get("amount"):
        return {"success":False,"message":"Amount is missing in payload"}
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
        si.supply_date_cf = getdate(params.get("invoice_date"))
        si.update_stock = 0
        si.set_posting_time = 1
        si.reference_id = params.get("reference_id")
        si.service_type = params.get("service_type")
        si.cost_center = "1004 - Marketing Services - ALJTech"
        si.customer = "الإيرادات من الإعلانات الخدمة الذاتية"
        si.sub_customer_en = params.get("customer_name_en","")
        si.sub_customer_ar = params.get("customer_name_ar","")
        si.customer_details = "{}\n{}".format(params.get("email"),str(params.get("cell_no")).replace("+",""))
        si.append("items",{
            'item_code': "Marketing Services",
            'item_name': "Marketing Services",
            'uom':'Nos',
            'qty':  1,
            'rate':flt(flt(params.get("amount"))/1.15),
            'item_tax_template': "B1 - KSA Sales VAT 15% - مبيعات"
        })
        si.taxes_and_charges = "B1 - Goods / Services Domestic Supply 15%"
        si.set("payment_schedule",[])
        si.flags.ignore_permissions = 1
        si.insert()
        # si.submit()
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


@frappe.whitelist()
def add_valuation_invoice(invoice=None):
    response = {}
    params = get_post_params()
    if not params:
        return {"success":False,"message":"No request payload found"}
    if not params.get("service_type"):
        return {"success":False,"message":"Service Type is missing in payload"}
    if not params.get("items"):
        return {"success":False,"message":"Sales Items are missing in payload"}
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
        si.supply_date_cf = getdate(params.get("invoice_date"))
        si.update_stock = 0
        si.set_posting_time = 1
        si.reference_id = params.get("reference_id")
        si.service_type = params.get("service_type")
        si.cost_center = "1004 - Marketing Services - ALJTech"
        si.customer = "Motory Vehicle Premium Valuation Service"
        si.sub_customer_en = params.get("customer_name_en","")
        si.sub_customer_ar = params.get("customer_name_ar","")
        si.customer_details = "{}\n{}".format(params.get("email"),str(params.get("cell_no")).replace("+",""))        for row in params.get("items",[]):            
            si.append("items",{
                'item_code': row.get("item_name"),
                'item_name': row.get("item_name"),
                'uom':'Nos',
                'qty':  1,
                'rate':flt(flt(row.get("rate"))/1.15),
                'item_tax_template': "B1 - KSA Sales VAT 15% - مبيعات"
            })
        si.taxes_and_charges = "B1 - Goods / Services Domestic Supply 15%"
        si.set("payment_schedule",[])
        si.flags.ignore_permissions = 1
        si.insert()
        # si.submit()
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
