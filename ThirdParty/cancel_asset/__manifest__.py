# -*- coding: utf-8 -*-
# module template
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Cancel assets',
    'version': '10.0',
    'category': 'Sales',
    'license': 'AGPL-3',
    'author': "Odoo Tips",
    'website': 'http://www.gotodoo.com/',
    'depends': ['account','account_asset',
                ],

    'images': ['images/main_screenshot.png'],
    'data': [
             'views/cancel_asset_view.xml',
             ],
    'installable': True,
    'application': True,
}
