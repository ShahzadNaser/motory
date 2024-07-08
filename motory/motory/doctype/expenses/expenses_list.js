frappe.listview_settings['Expenses'] = {
	get_indicator: function(doc) {
		const status_colors = {
			"Draft": "grey",
			"Unpaid": "orange",
			"Paid": "green",
			"Partly Paid": "yellow",
			"Cancelled": "Red"
		};
		return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
	},
	right_column: "grand_total"
};
