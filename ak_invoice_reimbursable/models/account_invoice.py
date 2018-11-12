# -*- coding: utf-8 -*-
import requests
import logging
import re
import datetime
import pytz
import base64
import json
import xml.etree.ElementTree as ET
from dateutil.parser import parse
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

class InvoiceLineElectronic(models.Model):
    _inherit = "account.invoice.line"

    #TODO: Move this to AK-Project
    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            if not self.name:
                self.name = product.partner_ref

            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            
            if self.invoice_line_tax_ids == False or len(self.invoice_line_tax_ids) == 0:
                self._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase and (not self.name):
                    self.name += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    self.name += '\n' + product.description_sale

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}


class AccountSupplierInvoiceElectronic(models.Model):
    _inherit = "account.invoice"

    # Used to indicate this invoice is going to be used for reimburse
    invoice_reimbursable = fields.Boolean(string="Indicates if this invoice is for reimburse", required=False)


    @api.multi
    def charge_xml_data(self):
        if (self.type == 'out_invoice' or  self.type == 'out_refund') and self.xml_comprobante:
            #remove any character not a number digit in the invoice number
            self.number = re.sub(r"[^0-9]+", "", self.number)
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_comprobante).decode("utf-8"),
                                        count=1))  # quita el namespace de los elementos
            
            partner_id = root.findall('Receptor')[0].find('Identificacion')[1].text
            date_issuance = root.findall('FechaEmision')[0].text
            consecutive = root.findall('NumeroConsecutivo')[0].text


            partner = self.env['res.partner'].search(
                [('vat', '=', partner_id)])
            if partner and self.partner_id.id != partner.id:
                raise UserError('El cliente con identificación ' + partner_id + ' no coincide con el cliente de esta factura: ' + self.partner_id.vat)
            elif str(self.date_invoice) != date_issuance:
                raise UserError('La fecha del XML () ' + date_issuance + ' no coincide con la fecha de esta factura')
            elif self.number != consecutive:
                raise UserError('El número cosecutivo ' + consecutive + ' no coincide con el de esta factura')
            else:
                self.number_electronic = root.findall('Clave')[0].text
                self.date_issuance = date_issuance
                self.date_invoice = date_issuance

        elif self.xml_supplier_approval:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_supplier_approval).decode("utf-8"),
                                        count=1))  # quita el namespace de los elementos
            self.number_electronic = root.findall('Clave')[0].text
            self.date_issuance = root.findall('FechaEmision')[0].text
            self.currency_id = self.env['res.currency'].search([('name', '=', root.find('ResumenFactura').find('CodigoMoneda').text)], limit=1).id
            self.date_invoice = parse(self.date_issuance)
            partner = self.env['res.partner'].search(
                [('vat', '=', root.findall('Emisor')[0].find('Identificacion')[1].text)])

            if partner:
                self.partner_id = partner.id
            else:
                raise UserError('El proveedor con identificación ' + root.findall('Emisor')[0].find('Identificacion')[
                    1].text + ' no existe. Por favor creelo primero en el sistema.')

            self.reference = self.number_electronic[21:41]

            default_account_id = self.env['ir.config_parameter'].sudo().get_param('default_expense_account_id')
            lines = root.find('DetalleServicio').findall('LineaDetalle')
            new_lines = self.env['account.invoice.line']
            
            for line in lines:
                product_uom = self.env['product.uom'].search([('code', '=', line.find('UnidadMedida').text)], limit=1).id
                total_amount = float(line.find('MontoTotal').text)

                discount_percentage = 0.0
                discount_note = None
                discount_node = line.find('MontoDescuento')
                if discount_node:
                    discount_amount = float(discount_node.text or '0.0')
                    discount_percentage = discount_amount / total_amount * 100
                    discount_note = line.find('NaturalezaDescuento').text
                
                taxes = self.env['account.tax']
                tax_nodes = line.findall('Impuesto')
                total_tax = 0.0
                if tax_nodes:
                    for tax_node in tax_nodes:
                        if tax_node:
                            tax = self.env['account.tax'].search([('tax_code', '=', re.sub(r"[^0-9]+", "", tax_node.find('Codigo').text)), ('type_tax_use', '=', 'purchase')], limit=1)
                            tax_amount = float(tax_node.find('Monto').text)
                            if tax and tax.amount == float(re.sub(r"[^0-9.]+", "", tax_node.find('Tarifa').text)):
                                taxes += tax
                                total_tax += tax_amount
                            else:
                                raise UserError('Un tipo de impuesto en el XML no existe en la configuración: ' +  tax_node.find('Codigo').text)
                            
                            #TODO: insert exonerations

                invoice_line = self.env['account.invoice.line'].new({
                        'name': line.find('Detalle').text,
                        'invoice_id': self.id,
                        'price_unit': line.find('PrecioUnitario').text,
                        'quantity': line.find('Cantidad').text,
                        'uom_id': product_uom,
                        'sequence': line.find('NumeroLinea').text,
                        'discount': discount_percentage,
                        'discount_note': discount_note,
                        'total_amount': total_amount,
                        'amount_untaxed': float(line.find('SubTotal').text),
                        'invoice_line_tax_ids': taxes,
                        'total_tax': total_tax,
                        'account_id': default_account_id,
                    })
                new_lines += invoice_line
            
            self.invoice_line_ids = new_lines

            tax_node = root.findall('ResumenFactura')[0].findall('TotalImpuesto')
            if tax_node:
                self.amount_tax_electronic_invoice = tax_node[0].text
            self.amount_total_electronic_invoice = root.findall('ResumenFactura')[0].findall('TotalComprobante')[0].text

            self.compute_taxes()

        
        # if self.xml_respuesta_tributacion:
        #     root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_respuesta_tributacion).decode("utf-8"),
        #                                 count=1))  # quita el namespace de los elementos
        #     self.state_tributacion = 


    @api.onchange('xml_comprobante')
    def _onchange_xml_comprobante(self):
        if self.xml_comprobante:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_comprobante).decode("utf-8"),
                                        count=1))  # quita el namespace de los elementos
            self.fname_xml_comprobante = 'comprobante_' + root.findall('Clave')[0].text + '.xml'
