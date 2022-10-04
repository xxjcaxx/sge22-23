# -*- coding: utf-8 -*-


from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
## from odoo.exceptions import Warning   (Es considera obsolet en favor de UserError)
from odoo.exceptions import UserError


class building_type(models.Model):
    _name = 'negocity.building_type'
    _description = 'Building types'

    name = fields.Char()
    energy = fields.Float()  # Pot ser positiu o negatiu i aumenta en el nivell
    oil = fields.Float()
    food = fields.Float()
    water = fields.Float()
    despair = fields.Float(default=0)
    junk = fields.Float()  # Quantitat de junk que necessita i que proporciona
    time = fields.Float(compute='_get_time')  # En hores
    image = fields.Image(max_width=200, max_height=200)
    image_small = fields.Image(related='image', max_width=40, max_height=40,
                               string="image")

    @api.depends('junk')
    def _get_time(self):
        for b in self:
            b.time = b.junk / 10


class building(models.Model):
    _name = 'negocity.building'
    _description = 'Buildings'

    name = fields.Char(related='type.name')
    type = fields.Many2one('negocity.building_type', ondelete='restrict')
    level = fields.Float(default=1)  # Possible widget
    ruined = fields.Float(default=50)  # 100% és ruina total i 0 està perfecte
    city = fields.Many2one('negocity.city', ondelete='cascade')

    junk_contributed = fields.Integer(default=0)
    junk_progress = fields.Float(compute='_get_junk_progress')
    workers = fields.Many2many('negocity.survivor', domain="[('id','in',workers_available)]")
    # workers = fields.Many2many('negocity.survivor', domain="[('city','=',city)]")
    workers_available = fields.Many2many('negocity.survivor', compute='_get_workers_available')
    time = fields.Float(compute='_get_time')
    date_start = fields.Datetime()
    date_end = fields.Datetime(compute='_get_time')
    progress = fields.Float()

    state = fields.Selection([('unfinished', 'Unfinished'), ('inprogress', 'In Progress'), ('finished', 'Finished')])

    # Coses del tipus
    image = fields.Image(related='type.image')
    energy = fields.Float(related='type.energy')  # Pot ser positiu o negatiu i aumenta en el nivell
    oil = fields.Float(related='type.oil')
    food = fields.Float(related='type.food')
    water = fields.Float(related='type.water')
    despair = fields.Float(related='type.despair')
    junk = fields.Float(related='type.junk')  # Quantitat de junk que necessita i que proporciona

    @api.depends('workers', 'city')
    def _get_workers_available(self):
        for b in self:
            b.workers_available = (b.city.survivors - b.workers).filtered(
                lambda w: len(w.city.buildings.workers.filtered(
                    lambda ww: ww.id == w.id))
                          == 0)

    @api.constrains('workers')
    def _check_workers(self):
        for b in self:
            for w in b.workers:
                if b.city.id != w.city.id:
                    raise ValidationError('The workers are not from the same city')

    @api.depends('junk_contributed')
    def _get_junk_progress(self):
        for b in self:
            contributed = b.junk_contributed
            expected = b.type.junk
            b.junk_progress = (contributed * 100) / expected

    @api.depends('type', 'workers', 'date_start')
    def _get_time(self):
        for b in self:
            if b.state != 'finished':
                # Primer traguem el temps total en la quantitat de treballadors actuals
                n_workers = len(b.workers)
                if n_workers > 0:
                    mean_illness = sum(b.workers.mapped('illnes')) / n_workers # Utilitzar sum() en compte de for és programació funcional
                    #for w in b.workers:
                    #    mean_illness = mean_illness + w.illnes
                    #mean_illness = mean_illness / n_workers
                    print('nnnnnnnnnnnnnn', b.type.time, n_workers, mean_illness)
                    b.time = b.type.time / math.log(n_workers * (101 - mean_illness), 2)

                else:
                    b.time = b.type.time
                remaining_percent = 100 - b.progress
                remaining_time = remaining_percent * b.time / 100
                # treure data final
                if b.date_start:
                    b.date_end = fields.Datetime.to_string(
                        fields.Datetime.from_string(fields.datetime.now()) + timedelta(hours=remaining_time))
                # time_remaining =  fields.Datetime.context_timestamp(self,b.date_end) -  fields.Datetime.context_timestamp(self, datetime.now())
                else:
                    b.date_end = ''

            else:
                b.date_end = False
                b.time = 0

    @api.model
    def create(self, values):
        record = super(building, self).create(values)
        if record.junk_contributed >= record.type.junk and record.date_start == False:
            record.write({'date_start': fields.datetime.now(), 'state': 'inprogress'})
        return record

    def write(self, values):
        record = super(building, self).write(values)
        if self.junk_contributed >= self.type.junk and not self.date_start:
            self.write({'date_start': fields.datetime.now(), 'state': 'inprogress'})
        return record

    @api.model
    def update_building(self):
        buildings_in_progress = self.search([('state', '=', 'inprogress')])
        print("Updating progress in: ", buildings_in_progress)
        for b in buildings_in_progress:
            percent_in_a_minute = 100 / (b.time * 60)
            b.write({'progress': b.progress + percent_in_a_minute})
            if b.progress >= 100:
                b.write({'progress': 100, 'state': 'finished', 'workers': [(5, 0, 0)],
                         'ruined': 0})  # Desvincule sense eliminar als treballadors
        ### Producció dels edificis
        buildings_in_production = self.search([('state', '=', 'finished'), ('ruined', '<', 100)])
        print("Updating production in: ", buildings_in_production)
        for b in buildings_in_production:
            factor = 100 - b.ruined
            energy = b.city.energy + b.energy
            oil = b.city.oil + b.oil
            water = b.city.water + b.water
            despair = b.city.despair + b.despair
            if despair <= 0:
                despair = 0
            if (energy > 0 or b.energy >= 0) and (oil > 0 or b.oil >= 0) and (water > 0 or b.water >= 0):
                print(b.name, b.city.name, energy, oil, water, despair)
                b.city.write({
                    'energy': energy,
                    'oil': oil,
                    'food': b.city.food + b.food,
                    'water': water,
                    'despair': despair,
                })

    def dismantle(self):
        for b in self:
            b.city.write({'junk': b.city.junk + b.junk})
            b.unlink()

    def repair(self):
        for b in self:
            junk_needed = b.junk - b.junk_contributed
            if b.city.junk > junk_needed:
                b.city.write({'junk': b.city.junk - junk_needed})
                b.write({'junk_contributed': b.junk})
            else:
                b.write({'junk_contributed': b.junk_contributed + b.city.junk})
                b.city.write({'junk': 0})
