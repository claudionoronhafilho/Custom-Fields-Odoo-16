# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "All in one add custom fields -Global Custom Fields",
    "version": "16.0.0.1",
    "category": "Extra Tools",
    'summary': "Add custom fields global custom field add dynamic fields custom dynamic fields all in one add new fields all in one custom add fields update view update custom fields update fields assign custom fields update global custom fields easy to add custom field",
    "description": """
	
				add custom fields,
				global field,
				global tabs,
				gubal custome fields and tabs,
	
	""",
    "author": "BrowseInfo",
    "website": "https://www.browseinfo.in",
    "price": 89,
    'license': 'OPL-1',
    "currency": 'EUR',
    "depends": ['base', 'sale_management', 'purchase', 'project', 'stock', 'account', 'product', 'crm'],
    "data": [
        'security/global_custom_fields_security.xml',
        'security/ir.model.access.csv',
        'views/global_custom_fields.xml',
        'views/custom_fields_view.xml',
        'views/global_custom_tabs_view.xml',
        'views/global_custom_fields_menu.xml',
    ],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "live_test_url": 'https://youtu.be/xvBKAb-ax0Y',
    "images": ["static/description/Banner.gif"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
