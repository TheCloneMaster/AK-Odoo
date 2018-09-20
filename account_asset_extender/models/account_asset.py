# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    user_id = fields.Many2one('res.users', 'Assigned to', track_visibility='onchange')
    asset_number = fields.Char('Asset Number', size=64)
    model = fields.Char('Model', size=64)
    serial = fields.Char('Serial no.', size=64)
    manufacturer = fields.Char('Manufacturer')
    purchase_date = fields.Date('Purchase Date')
    purchase_amount = fields.Float('Purchase Price',digits=(10, 2), help="Price of the asset when bought")
    warranty_start_date = fields.Date('Warranty Start')
    warranty_end_date = fields.Date('Warranty End')


