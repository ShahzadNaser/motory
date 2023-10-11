__version__ = '0.0.1'

import frappe
import json
from erpnext.stock import get_item_details

old_get_item_details = get_item_details.get_item_details

@frappe.whitelist()
def new_get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
    out = old_get_item_details(args, doc, for_validate, overwrite_warehouse)
    
    # Custom Code for changing income/expense account based on the account setting
    doc = json.loads(doc)
    args = json.loads(args)
    purchase_docs = ["Purchase Invoice"]
    sales_docs = ["Sales Invoice"]
    
    cur_item =  [row for row in doc.get("items") if row.get("name") == args.get("child_docname")][0]

    if args.get("doctype") in purchase_docs or args.get("doctype") in sales_docs:
        result = frappe.get_all(
            'Child Config', {
                'parent': 'Account Setting',
                'cost_center': out.get("cost_center"),
                'item_type_cf': cur_item.get("item_type_cf"),
                'doctype_': args.get("doctype")
            }, ['account']
        )

    
        if result:
            account = result[0]['account']
            
            if args.get("doctype") in sales_docs:
                out.income_account = account
            
            elif args.get("doctype") in purchase_docs:
                out.expense_account = account

    return out

# get_item_details.get_item_details = new_get_item_details