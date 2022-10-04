# -*- coding: utf-8 -*-

from odoo import models, fields, api

from datetime import datetime, timedelta


class player_premium(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_premium = fields.Boolean()
    date_end = fields.Datetime()

    def apply_premium(self,days):
        if self.is_premium:
            end = fields.Datetime.from_string(self.date_end)
            new_end = end + timedelta(days=days)
            self.date_end = fields.Datetime.to_string(new_end)
        else:
            new_end = datetime.now() + timedelta(days=days)
            self.date_end = fields.Datetime.to_string(new_end)
            self.is_premium = True

    @api.model
    def check_premium(self):
        players = self.search([('is_premium','=',True)])
        print('Premium Cron', players)
        for p in players:
            if p.date_end < fields.Datetime.now():
                p.is_premium = False


class travel_premium(models.Model):
    _name = 'negocity.travel'
    _inherit = 'negocity.travel'

    @api.model
    def get_time(self, vehicle_id, road_id):
        time = super(travel_premium,self).get_time(vehicle_id,road_id)
        if (self.env['negocity.vehicle'].browse(vehicle_id).survivor.player.is_premium == True):
            time = time/2
            print(time)
        else:
            print(time,self.env['negocity.vehicle'].browse(vehicle_id).survivor.player.name)
        return time

class product_premium(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    is_premium = fields.Boolean(default=False)

    days_premium = fields.Integer()

class sale_premium(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    premium_applied = fields.Boolean(default=False)

    def apply_premium(self):

        premium_products = self.order_line.filtered(lambda p: p.product_id.is_premium == True and self.premium_applied == False)
        for p in premium_products:
            self.partner_id.apply_premium(p.product_id.days_premium)
       # self.premium_applied = True

    def write(self,values):
        super(sale_premium,self).write(values)
        self.apply_premium()

    @api.model
    def create(self,values):
        record = super(sale_premium,self).create(values)
        record.apply_premium()
        return record