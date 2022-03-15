# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from itertools import islice
import json
import xml.etree.ElementTree as ET
import logging
import re
import werkzeug.utils
import werkzeug.wrappers
import base64
import csv
import sys
import io
import tempfile

from odoo import fields
from odoo import http
from odoo.http import request, route
from odoo import http, tools, _
from odoo.exceptions import Warning
from odoo.addons.web.controllers.main import WebClient, Binary, Home

SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)
from datetime import datetime as dt
_logger = logging.getLogger(__name__)

class Website(Home):

    @http.route('/track/shipment', type='http', auth="public", website=True, cache=300)
    def track_shipment(self, **post):
        freight = request.env['freight.operation'].sudo().search([('name', '=', post['tracking_number'])])

        _logger.info("Freight Record")
        _logger.info(freight)
        if freight:
            return request.render('freight.freight_success',{'freight':freight})


class BookingsCustom(http.Controller):

    @http.route(['/createbooking'], type='http', auth='user', website=True, cache=300, csrf=False)
    def portal_my_bookings_create(self, redirect=None, **post):
        partners = request.env['res.partner'].search([])
        users = request.env['res.users'].search([])
        incoterms = request.env['freight.incoterms'].search([])
        move_type = request.env['freight.move.type'].search([])
        gateways = request.env['freight.port'].search([])
        airlines = request.env['freight.airline'].search([])
        vessels = request.env['freight.vessel'].search([])
        truckers = request.env['freight.trucker'].search([])

        values = {
            'partners':partners,
            'users':users,
            'incoterms':incoterms,
            'move_type':move_type,
            'gateways':gateways,
            'airlines':airlines,
            'vessels':vessels,
            'truckers':truckers,
        }
        return request.render("freight.portal_booking_create", values)

    @http.route(['/submit_booking'], type='http', auth='user', website=True, cache=300,  csrf=False)
    def portal_my_bookings_submit(self, **post):
        partners = request.env['res.partner']
        users = request.env['res.users']
        incoterms = request.env['freight.incoterms']
        move_type = request.env['freight.move.type']
        gateways = request.env['freight.port']
        airlines = request.env['freight.airline']
        vessels = request.env['freight.vessel']
        truckers = request.env['freight.trucker']
        operation = request.env['freight.booking']
        final_dict = {}
        dir = ''
        if post:
            if post.get('operation'):
                final_dict['operation'] = post.get('operation')
            if post.get('direction'):
                final_dict['direction'] = post.get('direction')
            if post.get('transport'):
                final_dict['transport'] = post.get('transport')
                dir = post.get('transport')
            if post.get('ocean'):
                final_dict['ocean_shipment_type'] = post.get('ocean')
            if post.get('land'):
                final_dict['inland_shipment_type'] = post.get('land')
            if post.get('shipper'):
                final_dict['shipper_id'] = partners.browse(int(post.get('shipper'))).id
            if post.get('consignee'):
                final_dict['consignee_id'] = partners.browse(int(post.get('consignee'))).id

            # if post.get('source_location_id'):
            #     final_dict['source_location_id'] = gateways.browse(int(post.get('source_location_id'))).id
            # if post.get('destination_location_id'):
            #     final_dict['destination_location_id'] = gateways.browse(int(post.get('destination_location_id'))).id
            if post.get('mawb'):
                final_dict['mawb_no'] = post.get('mawb')
            if post.get('flight_no'):
                final_dict['flight_no'] = post.get('flight_no')
            if post.get('airline'):
                final_dict['airline_id'] = airlines.browse(int(post.get('airline'))).id
            #Ocean Fields
            if post.get('shipping_line_id'):
                final_dict['shipping_line_id'] = partners.browse(int(post.get('shipping_line_id'))).id
            if post.get('vessel_id'):
                final_dict['vessel_id'] = vessels.browse(int(post.get('vessel_id'))).id
            if post.get('voyage_no'):
                final_dict['voyage_no'] = post.get('voyage_no')
            if post.get('obl'):
                final_dict['obl'] = post.get('obl')
            # Inland Fields
            if post.get('cmr_no'):
                final_dict['truck_ref'] = post.get('cmr_no')
            if post.get('trucker_number'):
                final_dict['trucker_number'] = post.get('trucker_number')
            if post.get('trucker'):
                final_dict['trucker'] = truckers.browse(int(post.get('trucker'))).id
            #General Data
            if post.get('barcode'):
                final_dict['barcode'] = post.get('barcode')
            if post.get('notes'):
                final_dict['notes'] = post.get('notes')
            if post.get('freight_pc'):
                final_dict['freight_pc'] = post.get('freight_pc')
            if post.get('other_pc'):
                final_dict['other_pc'] = post.get('other_pc')
            if post.get('trac_no'):
                final_dict['tracking_number'] = post.get('trac_no')
            if 'danger' in post.keys() and post.get('danger') == 'on':
                final_dict['dangerous_goods'] = True
                if 'danger_info' in post.keys():
                    final_dict['dangerous_goods_notes'] = post.get('danger_info')
            if post.get('agent_id'):
                final_dict['agent_id'] = partners.browse(int(post.get('agent_id'))).id
            if post.get('operator_id'):
                final_dict['operator_id'] = users.browse(int(post.get('operator_id'))).id
            if post.get('move_type'):
                final_dict['move_type'] = move_type.browse(int(post.get('move_type'))).id
            if post.get('incoterm'):
                final_dict['incoterm'] = incoterms.browse(int(post.get('incoterm'))).id
            if post.get('date'):
                final_dict['datetime'] = dt.strptime(post.get('date'), '%Y-%m-%dT%H:%M')
            if post.get('new_date'):
                final_dict['datetime'] = dt.strptime(post.get('new_date'), '%Y-%m-%dT%H:%M')
            if dir == 'air' or not dir:
                if post.get('air_source_location_id'):
                    final_dict['source_location_id']  = gateways.browse(int(post.get('air_source_location_id'))).id
                if post.get('air_destination_location_id'):
                    final_dict['destination_location_id'] = gateways.browse(int(post.get('air_destination_location_id'))).id
            if dir == 'ocean':
                if post.get('ocean_source_location_id'):
                    final_dict['source_location_id']  = gateways.browse(int(post.get('ocean_source_location_id'))).id
                if post.get('ocean_destination_location_id'):
                    final_dict['destination_location_id'] = gateways.browse(int(post.get('ocean_destination_location_id'))).id
            if dir == 'land':
                if post.get('land_source_location_id'):
                    final_dict['source_location_id']  = gateways.browse(int(post.get('land_source_location_id'))).id
                if post.get('land_destination_location_id'):
                    final_dict['destination_location_id'] = gateways.browse(int(post.get('land_destination_location_id'))).id

        final_dict.update({'state':'draft'})
        booking = operation.sudo().create(final_dict)
        for file in request.httprequest.files.getlist('file_booking'):
            data = file.read()
            mimetype = file.content_type
            attachment_id = request.env['ir.attachment'].create({
                'name':  file.filename,
                'mimetype': mimetype,
                'type': 'binary',
                'datas':base64.b64encode(data),
                'res_model': booking._name,
                'res_id': booking.id
            })
            booking.update({
                'attachment': [(4, attachment_id.id)],
            })
        del final_dict['state']
        return request.render("freight.portal_booking_create_thankyou", {'operation':booking})

    @http.route(['/freight_bookings'], type='http', auth="user", website=True, cache=300)
    def portal_my_bookings(self, **post):
        bookings = request.env['freight.booking']
        # make pager
        values = {}
        domain = ['|', ('create_uid', '=', False), ('create_uid', '=', request.env.user.id)]
        bookings_recs = bookings.search(domain)
        values.update({
            'bookings': bookings_recs.sudo(),
        })
        return request.render("freight.portal_my_bookings", values)

    @http.route(['/freight_bookings/details/<model("freight.booking"):booking>'], type='http', auth="user", website=True, cache=300)
    def portal_my_booking_detail(self, booking):
        track_ids = request.env['booking.tracker'].sudo().search([('booking_id', '=', booking.id)], order='id DESC')
        values = {
            'booking': booking.sudo(),
            'track_ids': track_ids,
        }

        return request.render("freight.portal_my_booking_detail", values)

    @http.route(['/post/comment'], type='http', auth="user", website=True)
    def post_comment(self, **kw):
        book_id = request.env['freight.booking'].sudo().browse(int(kw['book_id']))
        vals = {'name': tools.ustr(kw['comment']),
                'user_id': request.env.user.id,
                'date': fields.datetime.now(),
                'booking_id': book_id.id}
        request.env['booking.tracker'].sudo().create(vals)
        track_ids = request.env['booking.tracker'].sudo().search([('booking_id', '=', book_id.id)], order='id DESC')
        body = 'Note:%s noted by %s' % (tools.ustr(kw['comment']), request.env.user.partner_id.name)
        book_id.sudo().message_post(body=body)
        values = {}
        values.update({
            'booking': book_id.sudo(),
            'track_ids': track_ids,
        })
        return request.render("freight.portal_my_booking_detail", values)
