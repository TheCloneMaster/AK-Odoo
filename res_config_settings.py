# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.Model):
    _name = 'res.config.settings.cr.payroll'
    _inherit = 'res.config.settings'
    
    rent_tax_first_value = fields.float('Lower value on the rent range tax',help='Indicate the first value on the Rent Tax Range',default=799000)

    @api.model
    def get_default_rent_tax_first_value(self, cr, uid, fields, context=None):
        rent_tax_first_value=self.env['ir.config_parameter'].get_param('rent_tax_first_value', False)
        irconfigparam = self.env['ir.config_parameter']
        return{
                'show_separate_invoice': rent_tax_first_value
        }

    @api.model
    def set_default_rent_tax_first_value(self, cr, uid, ids, context=None):
        self.ensure_one()
        irconfigparam = self.env['ir.config_parameter']
        irconfigparam.set_param('rent_tax_first_value', self.rent_tax_first_value)
