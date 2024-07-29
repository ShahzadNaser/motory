# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1

import frappe, json
from frappe.utils import flt, fmt_money, money_in_words
import base64
import erpnext
import math

def get_context(context):
	context.no_cache = 1
	'''Return query string arg.'''
	query_string = frappe.local.request.query_string
	context = {"doc":frappe._dict({})}
	doc = {}
	receipt_str = ""
	try:
		receipt_str = str(query_string).replace("b'","'")
		if receipt_str:
			doc = frappe.db.sql("""select * from `tabPayment Entry`
				where name={}""".format(str(receipt_str)), as_dict=True)
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()),title="Error while Fetching Payment")
	if doc:
		context = {"doc":doc[0]}
		return context

def custom_round(number):
    decimal_part = number - int(number)  # Extract the decimal part of the number
    if decimal_part >= 0.5:
        return math.ceil(number)  # Round up
    else:
        return math.floor(number)