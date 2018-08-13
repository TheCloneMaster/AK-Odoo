# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Employee Costa Rica Adapter',
    'version': '11.0.1.0.0',
    'category': 'Human Resources',
    'author': "Akurey S.A.",
    'website': 'https://github.com/akurey/odoo',
    'license': 'AGPL-3',
    'depends': ['base', 'hr', 'account_cancel'],
    'data': [
        'views/hr_employee_view.xml',
        'views/res_currency_rate_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
