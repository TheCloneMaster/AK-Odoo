# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class account_asset(models.Model):
    _inherit = "account.asset.asset"

    state = fields.Selection(selection_add=[('cancel', 'Annule')])

    @api.multi
    def set_to_cancel(self):
        self.state = 'cancel'



