from . import __version__ as app_version

app_name = "motory"
app_title = "Motory"
app_publisher = "Shahzad Naser"
app_description = "motory"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "shahzadnaser1122@gmail.com"
app_license = "MIT"


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/motory/css/motory.css"
# app_include_js = "/assets/motory/js/motory.js"
app_include_js =  ["/assets/motory/js/markerjs2.js"]

# include js, css files in header of web template
# web_include_css = "/assets/motory/css/motory.css"
# web_include_js = "/assets/motory/js/motory.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "motory/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Item" : "public/js/item.js",
	"Quotation" : ["public/js/car_business_logic.js","public/js/quotation.js"],
	"Sales Order" : ["public/js/car_business_logic.js","public/js/sales_order.js"],
	"Sales Invoice" : ["public/js/car_business_logic.js","public/js/sales_invoice.js"],
	"Delivery Note" : ["public/js/car_business_logic.js","public/js/delivery_note.js"],
	"Purchase Receipt":"public/js/purchase_receipt.js",
	"Purchase Order":"public/js/purchase_order.js"
	}
doctype_list_js = {"Serial No" : "public/js/serial_no_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "motory.install.before_install"
# after_install = "motory.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "motory.uninstall.before_uninstall"
# after_uninstall = "motory.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "motory.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*"
	"Serial No": { 
		"validate": "motory.api.update_car_status"
		},
	"Stock Entry": { 
		"validate": ["motory.api.fetch_accessories_inspection_details","motory.api.validate_serial_no_and_qty"],
		"on_submit": ["motory.api.update_car_status","motory.api.copy_car_fields_to_serial_no_doc"],
		"on_update_after_submit" :  "motory.api.sync_accessories_inspection_details",
		"on_cancel": "motory.api.update_car_status"
		},
	"Purchase Receipt": { 
		"before_validate":"motory.api.copy_car_serial_to_vin",
		"validate": ["motory.api.fetch_accessories_inspection_details","motory.api.validate_single_serial_no"],
		"on_submit": ["motory.api.update_car_status","motory.api.copy_car_fields_to_serial_no_doc"],
		"on_update_after_submit": "motory.api.sync_accessories_inspection_details",
		"on_cancel": "motory.api.update_car_status"
	},
	"Purchase Invoice": { 
		"validate": ["motory.api.fetch_accessories_inspection_details","motory.api.validate_single_serial_no","motory.api.get_child_config_pi"],
		"on_submit": ["motory.api.update_car_status","motory.api.copy_car_fields_to_serial_no_doc"],
		"on_cancel": "motory.api.update_car_status"
	},
	"Sales Order": { 
		"validate": ["motory.api.validate_color","motory.api.validate_damaged_warehouse","motory.monkey_patch.calculate_taxes_and_totals.patch"],
		"before_save": "motory.api.before_save",
		"on_submit": "motory.api.update_car_status",
		"on_cancel": "motory.api.update_car_status"
	},
	"Sales Invoice": { 
		"before_validate":["motory.api.copy_car_serial_to_vin","motory.monkey_patch.calculate_taxes_and_totals.patch"],
		"validate": ["motory.api.validate_color","motory.api.validate_damaged_warehouse","motory.api.get_child_config"],
		"before_save": "motory.api.before_save",
		"on_submit":"motory.api.update_car_status",
		"on_cancel": "motory.api.update_car_status"
		},
	"Delivery Note": { 
		"before_validate":["motory.api.copy_car_serial_to_vin","motory.monkey_patch.calculate_taxes_and_totals.patch"],
		"validate": ["motory.api.fetch_accessories_inspection_details","motory.api.validate_color","motory.api.validate_damaged_warehouse","motory.api.fetch_used_car_details"],
		"on_submit": "motory.api.update_car_status",
		"on_cancel": "motory.api.update_car_status"
	},
	"Quotation": { 
	"validate": ["motory.api.validate_color","motory.api.validate_damaged_warehouse"],
		"on_submit": "motory.api.update_car_status",
		"on_cancel": "motory.api.update_car_status"
		},
	"Expense Entry": { 
		"on_submit": "motory.api.update_expense_in_serial_no",
		"on_cancel": "motory.api.update_expense_in_serial_no"
		},		
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"motory.tasks.all"
	# ],
	"daily": [
		"motory.api.update_car_status_to_available_for_expired_quotations"
	],
	# "hourly": [
	# 	"motory.tasks.hourly"
	# ],
	# "weekly": [
	# 	"motory.tasks.weekly"
	# ]
	# "monthly": [
	# 	"motory.tasks.monthly"
	# ]
}

# Testing
# -------

# before_tests = "motory.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "motory.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "motory.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"motory.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
