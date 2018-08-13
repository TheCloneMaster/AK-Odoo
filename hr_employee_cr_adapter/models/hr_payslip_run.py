# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    pay_date = fields.Date(
        help="Set the date this payroll was executed",
        string="Date when the payment was executed to calculate everything with the right exchange rate"
    )

    @api.onchange
    def _update_payslip_date(self)
        