# -*- coding: utf-8 -*-


from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
## from odoo.exceptions import Warning   (Es considera obsolet en favor de UserError)
from odoo.exceptions import UserError


class vehicle(models.Model):
    _name = 'negocity.vehicle'
    _description = 'vehicles'
    name = fields.Char()
    # type = fields.Selection([('truck','Truck'),('car','Car'),('bus','Bus')])
    oil_consumption = fields.Float()
    gas_tank = fields.Float()
    gas_tank_level = fields.Float(default=0)
    speed = fields.Float()
    passengers = fields.Integer()
    junk_level = fields.Float()
    damage = fields.Float()  # Un turisme 10, un camió armat 10000 per fer-se una idea
    resistence = fields.Float()
    survivor = fields.Many2one('negocity.survivor')
    city = fields.Many2one('negocity.city')
    template = fields.Many2one('negocity.vehicle_template')
    img = fields.Image(max_width=400, max_height=200, string="Image")
    img_computed = fields.Image(compute='_get_img')

    def _get_img(self):
        for v in self:
            if v.img != False:
                v.img_computed = v.img
            else:
                v.img_computed = v.template.image

    def fill_gas_tank(self):
        for v in self:
            gas_available = v.city.oil
            if gas_available > v.gas_tank:
                v.gas_tank_level = v.gas_tank
                v.city.oil = gas_available - v.gas_tank_level
            else:
                v.gas_tank_level = v.city.oil
                v.city.oil = 0

    def donate_gas_tank(self):
        for v in self:
            v.city.oil = v.city.oil + v.gas_tank_level
            v.gas_tank_level = 0

    def destroy(self):
        for v in self:
            v.junk_level = 100
            v.gas_tank_level = 0

    def repair(self):
        for v in self:
            if v.survivor:
                needed_junk = v.resistence
                junk_available = v.survivor.junk
                if needed_junk <= junk_available:
                    v.junk_level = 0
                    v.survivor.junk -= needed_junk
                else:
                    v.survivor.junk = 0
                    v.junk_level = 100 - (junk_available / needed_junk) * 100

    def stole_gas(self,v2):
        self.gas_tank_level = self.gas_tank_level + v2.gas_tank_level  # Es queda en la gasolina
        if self.gas_tank_level > self.gas_tank:
            self.gas_tank_level = self.gas_tank
        v2.gas_tank_level = 0