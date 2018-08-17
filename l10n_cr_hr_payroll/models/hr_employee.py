# copyright  2018 Carlos Wong, Akurey SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import datetime



class hr_employee(models.Model):
    _inherit = 'hr.employee'

    marital_exoneration = fields.Boolean(
        help="Indicates if the marital exoneration should be applied in taxes computation",
        string="Apply exoneration?"
    )

    children_exoneration = fields.Boolean(
        help="Indicates if the exoneration because of children should be applied in taxes computation",
        string="Apply exoneration for children?"
    )

    supplementary_pension = fields.Float(
        'Supplementary Pension', 
        digits=(10,2), 
        help='Monthly amount used for a supplementary pension that can be exonerate from rent tax and CCSS',
        default=0
    )

    initial_date = fields.Date(
        help="Set the initial date of the employee working for the company to compute vacation days",
        string="Initial Date"
    )

    first_day = fields.Integer(
        compute='_compute_first_day',
        store=True
    )
    
    @api.one
    @api.depends('initial_date')
    def _compute_first_day(self):
        if self.initial_date:
            selectedDate = datetime.datetime.strptime(self.initial_date, "%Y-%m-%d")
            self.first_day = int(selectedDate.strftime("%d"))
        else:
            self.first_day = 0
            