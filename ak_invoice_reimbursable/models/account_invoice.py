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


            partner = self.env['res.partner'].search([('vat', '=', partner_id)])
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
                            tax_amount = float(tax_node.find('Monto').text)
                            if tax_amount > 0:
                                tax = self.env['account.tax'].search([('tax_code', '=', re.sub(r"[^0-9]+", "", tax_node.find('Codigo').text)), ('type_tax_use', '=', 'purchase')], limit=1)
                                tax_amount = float(tax_node.find('Monto').text)
                                if tax and tax.amount == float(re.sub(r"[^0-9.]+", "", tax_node.find('Tarifa').text)):
                                    taxes += tax
                                    total_tax += tax_amount
                                else:
                                    raise UserError('Un tipo de impuesto en el XML no existe en la configuración: ' + tax_node.find('Codigo').text)
                            # TODO: insert exonerations

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

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.with_context(ctx).write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            inv_account_currency = False
            if company_currency.id != inv.account_id.currency_id.id:
                inv_account_currency = inv.account_id.currency_id.with_context(date=self.date_invoice)

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = inv.date or inv.date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': (diff_currency and amount_currency) or (inv_account_currency and (inv_account_currency.rate * t[1])),
                        'currency_id': (diff_currency and inv.currency_id.id) or (inv_account_currency and inv_account_currency.id),
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': (diff_currency and total_currency) or (inv_account_currency and (inv_account_currency.rate * total)),
                    'currency_id': (diff_currency and inv.currency_id.id) or (inv_account_currency and inv_account_currency.id),
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity==0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

            if line.account_id.currency_id.id and (line.account_id.currency_id.id != self.company_id.currency_id.id):
                currency_rate = line.account_id.currency_id.with_context(date=self.date_invoice).rate
                move_line_dict = {
                    'invl_id': line.id,
                    'type': 'src',
                    'name': line.name.split('\n')[0][:64],
                    'price_unit': line.price_unit,
                    'quantity': line.quantity,
                    'price': line.price_subtotal,
                    'account_id': line.account_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'currency_id': line.account_id.currency_id.id,
                    'currency_amount': line.price_subtotal * currency_rate,
                    'tax_ids': tax_ids,
                    'invoice_id': self.id,
                    'analytic_tag_ids': analytic_tag_ids
                }
            else:
                move_line_dict = {
                    'invl_id': line.id,
                    'type': 'src',
                    'name': line.name.split('\n')[0][:64],
                    'price_unit': line.price_unit,
                    'quantity': line.quantity,
                    'price': line.price_subtotal,
                    'account_id': line.account_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'tax_ids': tax_ids,
                    'invoice_id': self.id,
                    'analytic_tag_ids': analytic_tag_ids
                }
            res.append(move_line_dict)
        return res

    @api.onchange('xml_comprobante')
    def _onchange_xml_comprobante(self):
        if self.xml_comprobante:
            root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', base64.b64decode(self.xml_comprobante).decode("utf-8"),
                                        count=1))  # quita el namespace de los elementos
            self.fname_xml_comprobante = 'comprobante_' + root.findall('Clave')[0].text + '.xml'

    @api.model
    def message_new(self, msg, custom_values=None):
        reimbursable_email = self.env['ir.config_parameter'].sudo().get_param('reimbursable_email')
        
        # Is it for reimburse
        reimbursable = reimbursable_email in msg['to']

        # TODO: Se identifican los XMLs por clave y por tipo y los PDFs se meten todos en una lista para adjuntarlos a todas las facturas en este email.
        # Porque no tenemos un metodo seguro de buscar la clave dentro del PDF
        invoices = dict()
        pdfs_list = list()
        for attachment in msg['attachments']:
            if attachment.fname.endswith('.xml'):
                root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', attachment.content.decode("utf-8"), count=1))
                clave = root.find('Clave').text
                if clave not in invoices: 
                    invoices[clave] = dict()
                if root.tag == 'FacturaElectronica':
                    invoices[clave]['invoice_attachment'] = attachment
                elif root.tag == 'MensajeHacienda':
                    invoices[clave]['respuesta_hacienda'] = attachment
            elif attachment.fname.endswith('.pdf'):
                pdfs_list.append(attachment)

        for clave in invoices:
            invoice = False
            if 'invoice_attachment' in invoices[clave]:
                # Check if it is already an invoice registered with the Clave
                invoice = self.env['account.invoice'].search([('number_electronic', '=', clave)])
                partner = False
                if not invoice:
                    root = ET.fromstring(re.sub(' xmlns="[^"]+"', '', invoices[clave]['invoice_attachment'].content.decode("utf-8"), count=1))

                    # Revisar si el proveedor ya existe, si no, se crea
                    partner_id = root.findall('Emisor')[0].find('Identificacion')[1].text
                    partner = self.env['res.partner'].search([('vat', '=', partner_id)])

                    if not partner:
                        partner_node = root.find('Emisor')
                        location_node = partner_node.find('Ubicacion')
                        partner = self.env['res.partner'].sudo().new({
                            'name': partner_node.find('Nombre').text,
                            'commercial_name': partner_node.find('Nombre').text,
                            'identification_id': partner_node.find('Identificacion')[0].text,
                            'vat': partner_node.find('Identificacion')[1].text,
                            'Provincia': location_node.find('Provincia').text,
                            'Canton': location_node.find('Canton').text,
                            'Distrito': location_node.find('Distrito').text,
                            'Barrio': location_node.find('Barrio').text,
                            'street': location_node.find('OtrasSenas').text,
                            'phone_code': partner_node.find('Telefono')[0].text,
                            'phone': partner_node.find('Telefono')[1].text,
                        })
                    
                    # TODO: Crear el invoice: Asignar el proveedor, asignar el xml de la factura, attachear los archivos y llamar al metodo charge_xml_data
                    invoice = self.env['account.invoice'].sudo().new({
                                                            'partner_id': partner_id,
                                                            'xml_supplier_approval': base64.b64encode(invoices[clave]['invoice_attachment'].content),
                                                            'fname_xml_supplier_approval': invoices[clave]['invoice_attachment'].fname,
                                                            'invoice_reimbursable': reimbursable,
                                                            })

                    invoice.charge_xml_data()

                    
                else:
                    # TODO: The invoice already exist. What should we do? ignore the file?
                    print("falta implementar")

            if 'respuesta_hacienda' in invoices[clave]:
                # Check if it is already an invoice registered with the Clave
                if not invoice:
                    invoice = self.env['account.invoice'].search([('electronic_number', '=', clave)])

                if invoice:
                    fname = 'respuesta_' + clave + '.xml'
                    ir_id = self.env['ir.attachment'].search([('datas_fname', '=', 'respuesta_' + clave + '.xml'), ('res_model', '=', self._name), ('res_id', '=', invoice.id)])
                    if not ir_id:
                        invoice.fname_xml_respuesta_tributacion = fname
                        invoice.xml_respuesta_tributacion = invoices[clave]['respuesta_hacienda'].content
                        document_vals = {'name': 'respuesta_' + clave + '.xml',
                                        'datas': invoice.xml_respuesta_tributacion,
                                        'datas_fname': fname,
                                        'res_model': self._name,
                                        'res_id': invoice.id,
                                        'type': 'binary',
                                        }
                        ir_id = self.env['ir.attachment'].sudo().create(document_vals)

                else:
                    # TODO: What should we do if we receive the XMl "Respuesta Hacienda", but there is no invoice for this XML.
                    # send an email to contabilidad@akurey.com alert?
                    print("falta implementar")

            # If there is an invoice with this "Clave" (invoice) attach pdfs
            if invoice:
                for pdf in pdfs_list:
                    ir_id = self.env['ir.attachment'].search([('datas_fname', '=', pdf.fname),('res_model', '=', self._name),('res_id', '=', invoice.id)])
                    if not ir_id:
                        document_vals = {'name': pdf.fname,
                                        'datas': base64.b64encode(pdf.content),
                                        'datas_fname': pdf.fname,
                                        'res_model': self._name,
                                        'res_id': invoice.id,
                                        'type': 'binary',
                                        }
                        ir_id = self.env['ir.attachment'].sudo().create(document_vals)

                if len(pdfs_list) > 1:
                    # TODO: Notificar por email que hay una mezcla de PDFs en esta factura para que el encargo revise
                    print("falta implementar")
            else:
                # TODO: Notificar que llego un PDF sin XML
                print("IMplementar notificar por email")

            if invoice and (not invoice.state_invoice_partner):
                # Enviar el MensajeReceptor. Poner el valor de aceptado en state_invoice_partner y Llamar al método send_acceptance_message
                invoice.state_invoice_partner = '1'
                invoice.send_acceptance_message()


