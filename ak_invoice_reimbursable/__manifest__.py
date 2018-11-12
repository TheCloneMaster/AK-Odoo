# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Costa Rica employee reimburse using electronic invoice',
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'author': "Akurey S.A.",
    'website': 'https://github.com/akurey/ak-odoo',
    'license': 'AGPL-3',
    'depends': ['base', 'hr_expense', 'cr_electronic_invoice'],
    'data': [
        'views/account_invoice_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_expense_views.xml',
    ],
}