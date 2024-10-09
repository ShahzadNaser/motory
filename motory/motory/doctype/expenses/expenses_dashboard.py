from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'expenses',
		'non_standard_fieldnames': {
			'Payment Entry': 'reference_name',
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': ['Payment Entry']
			}
		]
	}
