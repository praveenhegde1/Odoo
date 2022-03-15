# -*- coding: utf-8 -*-
###################################################################################
#
#    inteslar software trading llc.
#    Copyright (C) 2018-TODAY inteslar (<https://www.inteslar.com>).
#    Author:   (<https://www.inteslar.com>)
#
###################################################################################
{
    'name': 'Freight Management',
    'version': '14.0',
    'category': 'freight',
    'price': 790.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'live_test_url':'https://www.youtube.com/watch?v=66lKp26x75k',
    'website':'https://www.inteslar.com',
    'images': ['static/description/banner.jpg'],
    'author':'inteslar',
    'summary': 'Manage freight forwarding shipping activities in Air Ocean and Land',
    'description': """
Key Features
------------
* Freight Management
        """,
    'depends': ['base',
                'base_setup',
                'account',
                'product',
                'web',
                'contacts',
                'mail',
                'board',
                'calendar',
                'web',
                'sale_management',
                'website',
                'portal',
                'hr'],
    'data': [
        'data/freight_data.xml',
        'security/ir.model.access.csv',
        'report/bill_of_lading.xml',
        'report/airway_bill.xml',
        'views/freight_report.xml',
        'wizard/register_invoice_freight_view.xml',
        'views/freight_view.xml',
        'views/booking_view.xml',
        'views/freight_templates.xml',
    ],
    'qweb': [
        "static/src/xml/freight_dashboard.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}