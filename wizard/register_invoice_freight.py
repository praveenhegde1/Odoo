# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import os.path
import base64
import time

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from werkzeug import url_encode
from datetime import date, datetime
from time import gmtime, strftime

_logger = logging.getLogger(__name__)

class RegisterInvoice(models.TransientModel):

    _name = "register.invoice"
    _description = "Create Invoice"

    def _default_service_ids(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        freight_services = self.env['freight.service'].browse(active_ids)
        return freight_services.ids

    partner_id = fields.Many2one('res.partner', 'Partner')
    service_ids = fields.Many2many('freight.service', default=_default_service_ids)
    invoice_type = fields.Selection([('customer','Customer'),('vendor','Vendor')], string='Invoice Type')
    type = fields.Selection([('agent','Agent'),('consignee','Consignee'),('shipper','Shipper')], string='Invoice to')

    # @api.onchange('type')
    # def onchage_type(self):
    #     for line in self:
    #         if line.type == 'agent':
    #             return {'domain': {'partner_id': [('agent', '=', True)]}}
    #         elif line.type == 'consignee':
    #             return {'domain': {'partner_id': [('consignee', '=', True)]}}
    #         elif line.type == 'shipper':
    #             return {'domain': {'partner_id': [('shipper', '=', True)]}}

    def create_invoice(self):
        _logger.info('Coming Inside Invoice FUnction >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        freight_services = self.env['freight.service'].browse(active_ids)
        line = []
        for service in self.service_ids:
            _logger.info(service.name)
            _logger.info('Coming Inside for loop FUnction >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            if service.service_id.property_account_income_id.id:
                income_account = service.service_id.property_account_income_id.id
            elif service.service_id.categ_id.property_account_income_categ_id.id:
                income_account = service.service_id.categ_id.property_account_income_categ_id.id
            else:
                raise UserError(_('Please define income '
                                  'account for this product: "%s" (id:%d).')
                                % (service.service_id.name, service.service_id.id))
            tot = service.qty * service.sale
            if self.invoice_type == 'customer':
                line.append((0,0, {'name': service.name,
                                'account_id': income_account,
                                'quantity': service.qty,
                                'credit': service.qty * service.sale,
                                'price_unit': service.sale,
                                'product_id': service.service_id.id,
                                'price_subtotal':service.qty * service.sale}))
                line.append((0,0, {'account_id': self.partner_id.property_account_receivable_id.id,
                                'quantity': 1,
                                'debit': service.qty * service.sale,
                                'price_unit': -tot,
                                'exclude_from_invoice_tab': True,
                                'price_subtotal':-tot}))
            else:
                line.append((0, 0, {'name': service.name,
                                'account_id': service.service_id.property_account_expense_id.id or service.service_id.categ_id.property_account_expense_categ_id.id,
                                'quantity': service.qty,
                                'price_unit': service.cost,
                                'debit': service.qty * service.sale,
                                'product_id': service.service_id.id,
                                'price_subtotal': service.qty * service.cost}))
                line.append((0, 0, {'account_id': self.partner_id.property_account_payable_id.id,
                                'quantity': service.qty,
                                'price_unit': -tot,
                                'credit': service.qty * service.sale,
                                'exclude_from_invoice_tab': True,
                                'price_subtotal': -tot}))
        _logger.info(line)
        if self.invoice_type == 'customer':
            invoices = self.env['account.move'].create({
                            'move_type': 'out_invoice',
                            'partner_id': self.partner_id.id,
                            'freight_operation_id': service.shipment_id.id,
                            'invoice_line_ids':line})
            return {
                    'name': _('Customer Invoice'),
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'res_model': 'account.move',
                    'context': "{'move_type':'out_invoice'}",
                    'type': 'ir.actions.act_window',
                    'res_id': invoices.id,
                }
        else:
            invoices = self.env['account.move'].create({
                            'move_type': 'in_invoice',
                            'partner_id': self.partner_id.id,
                            'freight_operation_id': service.shipment_id.id,
                            'invoice_line_ids': line,
            })
            return {
                    'name': _('Vendor Invoice'),
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'res_model': 'account.move',
                    'context': "{'move_type':'in_invoice'}",
                    'type': 'ir.actions.act_window',
                    'res_id': invoices.id,
                }