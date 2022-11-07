# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
from odoo.exceptions import ValidationError


class config(models.TransientModel):
    _inherit = 'res.config.settings'
    players = fields.Char(string='players',
                             config_parameter="expanse.players")


    def reset_universe(self):
        print("reset",self)

class player(models.Model):
    _name = 'expanse.player'
    _description = 'Players of the game'

    name = fields.Char(required=True, string="Player Name")
    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)
    avatar_tumb = fields.Image(related="avatar", max_width=50, max_height=50)
    colonies = fields.One2many('expanse.colony', 'player')
    colonies_qty = fields.Integer(compute="get_colonies_qty")

    @api.depends('colonies')
    def get_colonies_qty(self):
        for p in self:
            p.colonies_qty = len(p.colonies)


class planet(models.Model):
    _name = 'expanse.planet'
    _description = 'Planets'

    name = fields.Char(required=True)
    image = fields.Image(max_width=200, max_height=200)
    size = fields.Float()
    gravity = fields.Float(compute='_get_gravity')
    colonies = fields.One2many('expanse.colony', 'planet')

    @api.constrains('size')
    def check_planet_size(self):
        for planet in self:
            if planet.size > 1000 or planet.size < 1:
                raise ValidationError("Your planet is too big: %s" % planet.size)

    @api.depends('size')
    def _get_gravity(self):
        for planet in self:
            planet.gravity = 1


class colony(models.Model):
    _name = 'expanse.colony'
    _description = 'Colonies'

    name = fields.Char(required=True)
    planet = fields.Many2one('expanse.planet',ondelete="cascade")
    player = fields.Many2one('expanse.player',ondelete="cascade")
    player_avatar = fields.Image(related="player.avatar")
    creation_date = fields.Datetime(default=fields.Datetime.now)
    buildings = fields.One2many('expanse.building', 'colony')
    hangar_level = fields.Integer(default = 0)


class spaceship(models.Model):
    _name = 'expanse.spaceship'
    _description = 'Spaceships'

    name = fields.Char()


class building(models.Model):
    _name = 'expanse.building'
    _description = 'Buildings'

    name = fields.Char()
    image = fields.Image(related='type.image')
    type = fields.Many2one('expanse.building_type',ondelete="restrict")
    level = fields.Integer(default=1)
    colony = fields.Many2one('expanse.colony',ondelete="cascade")
    price_base = fields.Float(related='type.price_base')
    water_production = fields.Float(related='type.water_production')
    energy_production = fields.Float(related='type.energy_production')
    metal_production = fields.Float(related='type.metal_production')
    hydrogen_production = fields.Float(related='type.hydrogen_production')
    food_production = fields.Float(related='type.food_production')

    @api.constrains('level')
    def check_level(self):
        for b in self:
            if b.level > 10:
                raise ValidationError("Level cant be more than 10")

    def produce(self):
        for b in self:
            print("Produce",b.food_production)

class building_type(models.Model):
    _name = 'expanse.building_type'
    _description = 'Building types'

    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    price_base = fields.Float()
    water_production = fields.Float()
    energy_production = fields.Float()
    metal_production = fields.Float()
    hydrogen_production = fields.Float()
    food_production = fields.Float()

