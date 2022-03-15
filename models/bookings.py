# -*- coding: utf-8 -*-
###################################################################################
#
#    inteslar software trading llc.
#    Copyright (C) 2018-TODAY inteslar (<https://www.inteslar.com>).
#    Author:   (<https://www.inteslar.com>)
#
###################################################################################
import logging
from odoo import api, fields, models, _
from random import choice
from string import digits
from json import dumps
import json
import datetime
from datetime import datetime as dt


class Bookings(models.Model):
    _name = 'freight.booking'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Freight Bookings'

    def _get_default_stage_id(self):
        return self.env['shipment.stage'].search([], order='sequence', limit=1)

    def _default_random_barcode(self):
        return "".join(choice(digits) for i in range(8))

    barcode = fields.Char(string="Barcode", help="ID used for shipment identification.",
                          default=_default_random_barcode, copy=False)
    color = fields.Integer('Color')
    stage_id = fields.Many2one('shipment.stage', 'Stage', default=_get_default_stage_id,
                               group_expand='_read_group_stage_ids')
    name = fields.Char(string='Name', copy=False)
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export')]), string='Direction')
    state = fields.Selection(([('draft', 'Draft'), ('converted', 'Converted')]), string='Status', default='draft')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]), string='Transport')
    operation = fields.Selection([('direct', 'Direct'), ('house', 'House'), ('master', 'Master')], string='Operation')
    ocean_shipment_type = fields.Selection(([('fcl', 'FCL'), ('lcl', 'LCL')]), string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'FTL'), ('ltl', 'LTL')]), string='Inland Shipment Type')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    source_location_id = fields.Many2one('freight.port', 'Source Location', index=True, required=True)
    destination_location_id = fields.Many2one('freight.port', 'Destination Location', index=True, required=True)
    obl = fields.Char('OBL', help='Original Bill Of Landing')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No')
    datetime = fields.Datetime('Date')
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('freight.trucker', 'Trucker')
    trucker_number = fields.Char('Trucker No')
    agent_id = fields.Many2one('res.partner', 'Agent')
    operator_id = fields.Many2one('res.users', 'User')
    freight_pc = fields.Selection(([('collect', 'Collect'), ('prepaid', 'Prepaid')]), string="Freight PC")
    other_pc = fields.Selection(([('collect', 'Collect'), ('prepaid', 'Prepaid')]), string="Other PC")
    notes = fields.Text('Notes')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    move_type = fields.Many2one('freight.move.type', 'Move Type')
    tracking_number = fields.Char('Tracking Number')
    declaration_number = fields.Char('Declaration Number')
    declaration_date = fields.Date('Declaration Date')
    custom_clearnce_date = fields.Datetime('Customs Clearance Date')
    incoterm = fields.Many2one('freight.incoterms', 'Incoterm')
    parent_id = fields.Many2one('freight.operation', 'Parent')
    book_vals = fields.Char('Booking Vals')
    freight_id = fields.Many2one('freight.operation', 'Freight Operation')
    attachment = fields.Many2many('ir.attachment', 'attach_booking_rel', 'doc_id', 'booking_id',
                                  string="Attachment",
                                  help='You can attach the copy of your document', copy=False)
    track_ids = fields.One2many('booking.tracker', 'booking_id', 'Tracker Lines')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['shipment.stage'].search([])
        return stage_ids

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('freight.booking') or _('New')
        booking = super(Bookings, self).create(values)
        return booking

    def convert_fields_to_dict(self):
        final_dict  = {}
        if self.operation:
            final_dict['operation'] = self.operation
        if self.direction:
            final_dict['direction'] = self.direction
        if self.transport:
            final_dict['transport'] = self.transport
        if self.ocean_shipment_type:
            final_dict['ocean_shipment_type'] = self.ocean_shipment_type
        if self.inland_shipment_type:
            final_dict['inland_shipment_type'] = self.inland_shipment_type
        if self.shipper_id:
            final_dict['shipper_id'] = self.shipper_id.id or False
        if self.consignee_id:
            final_dict['consignee_id'] = self.consignee_id.id or False

        if self.source_location_id:
            final_dict['source_location_id'] = self.source_location_id.id or False
        if self.destination_location_id:
            final_dict['destination_location_id'] = self.destination_location_id.id or False
        if self.mawb_no:
            final_dict['mawb_no'] = self.mawb_no
        if self.flight_no:
            final_dict['flight_no'] = self.flight_no
        if self.airline_id:
            final_dict['airline_id'] = self.airline_id.id or False
        # Ocean Fields
        if self.shipping_line_id:
            final_dict['shipping_line_id'] =self.shipping_line_id.id or False
        if self.vessel_id:
            final_dict['vessel_id'] = self.vessel_id.id or False
        if self.voyage_no:
            final_dict['voyage_no'] = self.voyage_no
        if self.obl:
            final_dict['obl'] = self.obl
        # Inland Fields
        if self.truck_ref:
            final_dict['truck_ref'] = self.truck_ref
        if self.trucker_number:
            final_dict['trucker_number'] = self.trucker_number
        if self.trucker:
            final_dict['trucker'] = self.trucker.id or False
        # General Data
        if self.barcode:
            final_dict['barcode'] = self.barcode
        if self.notes:
            final_dict['notes'] = self.notes
        if self.freight_pc:
            final_dict['freight_pc'] = self.freight_pc
        if self.other_pc:
            final_dict['other_pc'] = self.other_pc
        if self.tracking_number:
            final_dict['tracking_number'] = self.tracking_number
        if  self.dangerous_goods:
            final_dict['dangerous_goods'] = True
            if self.dangerous_goods_notes:
                final_dict['dangerous_goods_notes'] = self.dangerous_goods_notes
        if self.agent_id:
            final_dict['agent_id'] = self.agent_id.id or False
        if self.operator_id:
            final_dict['operator_id'] = self.operator_id.id or False
        if self.move_type:
            final_dict['move_type'] = self.move_type.id or False
        if self.incoterm:
            final_dict['incoterm'] = self.incoterm.id or False
        if self.datetime:
            final_dict['datetime'] = self.datetime
        res = {}
        for key, val in final_dict.items():
            if key != 'name':
                res.update({
                    'default_' + key: val
                })
        return res

    def convert_to_operation(self):
        name_act = ''
        for book in self:
            res = self.convert_fields_to_dict()
            if res.get('operation') == 'master':
                name_act = 'Master'
                res['name'] = self.env['ir.sequence'].next_by_code('operation.master') or _('New')
            elif res.get('operation') == 'house':
                name_act = 'House'
                res['name'] = self.env['ir.sequence'].next_by_code('operation.house') or _('New')
            elif res.get('operation') == 'direct':
                name_act = 'Direct'
                res['name'] = self.env['ir.sequence'].next_by_code('operation.direct') or _('New')
            form_view = self.env.ref('freight.view_freight_operation_form')
            res.update({'default_booking_id': book.id})
            book.write({'state':'converted'})
            return {
                'name': name_act,
                'res_model': 'freight.operation',
                'type': 'ir.actions.act_window',
                'views': [(form_view and form_view.id, 'form')],
                'context':res,
            }

    def reset_book(self):
        for rec in self:
            rec.state = 'draft'
            if rec.freight_id:
                freight = rec.freight_id
                freight.booking_id = False
                rec.freight_id = False


    def button_shipping(self):
        action = {
            'name': _('Shipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.operation',
            'target': 'current',
        }
        ope = self.env['freight.operation'].search([('booking_id', '=', self.id)], limit=1)
        action['domain'] =[('id', '=', ope.id)]
        action['res_id'] = ope.id
        action['view_mode'] = 'form'
        return action


class BookingTracker(models.Model):
    _name = 'booking.tracker'

    name = fields.Char('Note')
    user_id = fields.Many2one('res.users','User ID')
    date = fields.Datetime('Date')
    actual_date = fields.Datetime('Actual')
    vendor_attachment = fields.Binary(attachment=True, string="Attachment")
    booking_id = fields.Many2one('freight.booking', 'Tender')


    @api.depends('date')
    def compute_actual(self):
        for line in self:
            line.actual_date = datetime.strptime(str(line.create_date), "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)