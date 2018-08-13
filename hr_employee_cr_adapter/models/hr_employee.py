# copyright  2018 Carlos Wong, Akurey SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime
from odoo import models, fields


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

    initial_date = fields.Date(
        help="Set the initial date of the employee working for the company to compute vacation days",
        string="Initial Date"
    )
