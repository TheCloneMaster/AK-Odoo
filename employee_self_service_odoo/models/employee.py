# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.multi
    def write(self, vals):
        rec = super(HrEmployee, self).write(vals)
        uid = self._context.get('uid')
        group = self.env['res.groups'].search([('name', '=', 'Employee')])
        categ_id = group.category_id.id
        officer_group = self.env['res.groups'].search([('name','=','Officer'),('category_id','=',categ_id)])
        employee = self.env['res.users'].browse(uid)
        
        if self.user_has_groups('hr.group_hr_user'):
            return rec
            
        if self.user_has_groups('base.group_user'):
            if self.user_id == employee:
                return rec
            else:
                raise UserError(_('You have no rights for update other employees data.'))
