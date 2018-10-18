# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Costa Rica - Payroll',
    'version': '11.0.1.0.0',
    'category': 'Localization',
    'author': "Akurey S.A.",
    'website': 'https://github.com/akurey/ak-odoo',
    'license': 'AGPL-3',
    'depends': ['base', 'hr_payroll_account'],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
