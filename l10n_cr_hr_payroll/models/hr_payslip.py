# copyright  2018 Carlos Wong, Akurey SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import datetime


class hrPaySlipCR(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def is_month_first_day(self, date_from):
        dateFrom = fields.Date.from_string(date_from)
        if dateFrom.day == 1:
            return True
        else:
            return False

    
    @api.model
    def get_payments_of_this_month(self, date_from, employee_id, gross_rule):
        result = 0
        currentDate = fields.Date.from_string(date_from)
        first_day = "{0:0=4d}-".format(currentDate.year) + "{0:0=2d}-".format(currentDate.month) + "01"
        paySlips = self.env['hr.payslip'].search([('employee_id', '=', employee_id),('date_from', '>=', first_day),('date_from', '<', date_from)])

        if paySlips:
            for payslip in paySlips:
                slipline = self.env['hr.payslip.line'].search([('slip_id', '=', payslip.id),('name', '=', gross_rule)], limit=1)
                result = slipline.total

        return result

    @api.model
    def get_first_payment_tax(self, date_from, employee_id, tax_rule):
        result = 0
        currentDate = fields.Date.from_string(date_from)
        firstPaySlipDate = "{0:0=4d}-".format(currentDate.year) + "{0:0=2d}-".format(currentDate.month) + "01"
        firstPayslip = self.env['hr.payslip'].search([('date_from', '=', firstPaySlipDate),('employee_id', '=', employee_id)], limit=1)

        if firstPayslip:
            slipline = self.env['hr.payslip.line'].search([('slip_id', '=', firstPayslip.id),('name', '=', tax_rule)], limit=1)
            result = slipline.total
        
        return result
    


class hrContractCR(models.Model):
    _inherit = 'hr.contract'

    currency_id = fields.Many2one('res.currency', string='Contract Currency', help="Indicates the currency for this contract.", related=False, readonly=False)
