# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
import string
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import math


def name_generator():
    letters = list(string.ascii_lowercase)
    first = list(string.ascii_uppercase)
    vocals = ['a', 'e', 'i', 'o', 'u', 'y', '']
    name = random.choice(first)
    for i in range(0, random.randint(3, 5)):
        name = name + random.choice(letters) + random.choice(vocals)
    return name


class config(models.TransientModel):
    _inherit = 'res.config.settings'
    players = fields.Char(string='players',
                          config_parameter="expanse.players")

    def reset_universe(self):
        print("reset", self)
        self.env['expanse.planet'].search([]).unlink()
        images = self.env['expanse.template'].search([('type', '=', '2')]).mapped('image')
        for i in range(0, 100):  # Crear planetes
            self.env['expanse.planet'].create({  # ORM
                "name": name_generator(),
                "size": random.betavariate(1.5, 1.1) * 1000,
                "image": random.choice(images),
                "coordinates": str(random.randint(0, 10000)) + "," + str(random.randint(0, 10000)) + "," + str(
                    random.randint(0, 10000))
            })


class player(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Players of the game'

    #name = fields.Char(required=True, string="Player Name")
    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)
    avatar_tumb = fields.Image(related="avatar", max_width=50, max_height=50)
    colonies = fields.One2many('expanse.colony', 'player')
    colonies_qty = fields.Integer(compute="get_colonies_qty")
    spaceships = fields.Many2many('expanse.colony_spaceship_rel', compute='_get_spaceships')
    money = fields.Float()
    is_player = fields.Boolean(default=False)

    @api.depends('colonies')
    def get_colonies_qty(self):
        for p in self:
            p.colonies_qty = len(p.colonies)

    @api.depends('colonies')
    def _get_spaceships(self):
        for p in self:
            p.spaceships = p.colonies.spaceships

    def launch_player_wizard(self):
      #  return self.env.ref('expanse.player_wizard_action').read()
        return {
            'name': 'Create Player',
            'type': 'ir.actions.act_window',
            'res_model': 'expanse.player_wizard',
            'view_mode': 'form',
            'target': 'new'
        }

    def launch_battle_wizard(self):
        return self.env.ref('expanse.battle_wizard_action').read()[0]


class planet(models.Model):
    _name = 'expanse.planet'
    _description = 'Planets'

    name = fields.Char(required=True)
    image = fields.Image(max_width=200, max_height=200)
    size = fields.Float()
    gravity = fields.Float(compute='_get_gravity')
    colonies = fields.One2many('expanse.colony', 'planet')
    coordinates = fields.Char()

    @api.constrains('size')
    def check_planet_size(self):
        for planet in self:
            if planet.size > 1000 or planet.size < 1:
                raise ValidationError("Your planet is too big: %s" % planet.size)

    @api.depends('size')
    def _get_gravity(self):
        for planet in self:
            planet.gravity = 1

    def distance(self, other_planet):
        distance = 0
        if len(self) > 0 and len(other_planet) > 0:
            c1 = list(map(lambda c: int(c), self.coordinates.split(',')))
            c2 = list(map(lambda c: int(c), other_planet.coordinates.split(',')))
            # d = ((x2 - x1)2 + (y2 - y1)2 + (z2 - z1)2)1/2
            distance = ((c2[0] - c1[0]) ** 2 + (c2[1] - c1[1]) ** 2 + (c2[2] - c1[2]) ** 2) ** 0.5
        return distance


class colony(models.Model):
    _name = 'expanse.colony'
    _description = 'Colonies'

    name = fields.Char(required=True)
    planet = fields.Many2one('expanse.planet', ondelete="cascade", required=True)
    player = fields.Many2one('res.partner', domain="[('is_player','=',True)]", ondelete="cascade")
    player_avatar = fields.Image(related="player.avatar", string="Player Avatar")
    money = fields.Float(related="player.money")

    buildings = fields.One2many('expanse.building', 'colony')
    buildings_available = fields.Many2many('expanse.building_type', compute='_get_available_buildings')
    hangar_level = fields.Integer(default=0)
    required_money_hangar = fields.Float(compute='_get_required_money_hangar')
    spaceships = fields.One2many('expanse.colony_spaceship_rel', 'colony_id')
    available_spaceships = fields.Many2many('expanse.spaceship', compute="_get_available_spaceships")

    water = fields.Float()
    energy = fields.Float()
    metal = fields.Float()
    hydrogen = fields.Float()
    food = fields.Float()

    water_production = fields.Float(compute='_get_total_productions')
    energy_production = fields.Float(compute='_get_total_productions')
    metal_production = fields.Float(compute='_get_total_productions')
    hydrogen_production = fields.Float(compute='_get_total_productions')
    food_production = fields.Float(compute='_get_total_productions')

    def _get_required_money_hangar(self):
        for c in self:
            c.required_money_hangar = 10 ** c.hangar_level

    def _get_available_buildings(self):
        for c in self:
            c.buildings_available = self.env['expanse.building_type'].search([('price_base','<=',c.money)])

    @api.depends('hangar_level')
    def _get_available_spaceships(self):  # ORM
        for c in self:
            c.available_spaceships = self.env['expanse.spaceship'].search([('hangar_required', '<=', c.hangar_level)])

    def update_hangar(self):  # ORM
        for c in self:
            required_money = c.required_money_hangar  # Smartbutton
            available_money = c.player.money
            if (required_money <= available_money):
                c.hangar_level += 1
                c.player.money = c.player.money - required_money

    @api.depends('buildings')
    def _get_total_productions(self):
        for c in self:
            c.water_production =  sum(c.buildings.mapped('water_production'))
            c.metal_production = sum(c.buildings.mapped('metal_production'))
            c.hydrogen_production =  sum(c.buildings.mapped('hydrogen_production'))
            c.food_production =  sum(c.buildings.mapped('food_production'))
            c.energy_production =  sum(c.buildings.mapped('energy_production'))

    @api.model
    def produce(self):  # ORM CRON
        self.search([]).produce_colony()

    def produce_colony(self):
        for colony in self:
            water = colony.water + colony.water_production
            metal = colony.metal + colony.metal_production
            hydrogen = colony.hydrogen + colony.hydrogen_production
            food = colony.food + colony.food_production
            energy = colony.energy_production

            colony.write({
                "water": water,
                "metal": metal,
                "hydrogen": hydrogen,
                "food": food,
                "energy": energy
            })


class spaceship(models.Model):
    _name = 'expanse.spaceship'
    _description = 'Spaceships'

    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    capacity = fields.Float()
    armor = fields.Float()
    damage = fields.Float()
    hangar_required = fields.Integer()
    time = fields.Float(compute='_get_construction_time')
    speed = fields.Float(compute='_get_construction_time')
    metal_required = fields.Float(compute='_get_construction_time')

    def _get_construction_time(self):
        for s in self:
            s.time = (s.capacity + 3 * s.damage + 2 * s.armor) / 13000
            s.speed = 100000000 / (9 * s.capacity + 15 * s.armor + 5 * s.damage)
            s.metal_required = s.capacity + 2 * s.armor + 0.5 * s.damage

    def fabricate(self):  # ORM
        for s in self:
            print('fabrica', self.env.context['ctx_colony'])
            colony = self.env['expanse.colony'].browse(self.env.context['ctx_colony'])
            colony_spaceship_rel = colony.spaceships.filtered(lambda c: c.spaceship_id.id == s.id)
            if (len(colony_spaceship_rel) == 0):  # no té encara cap nau d'aquest tipus
                colony_spaceship_rel = self.env['expanse.colony_spaceship_rel'].create({
                    "spaceship_id": s.id,
                    "colony_id": colony.id,
                    "qty": 0
                })
            self.env['expanse.colony_spaceship_fabrication'].create({
                "spaceship_id": colony_spaceship_rel.id,
                "time_remaining": s.time
            })


class colony_spaceship_rel(models.Model):
    _name = 'expanse.colony_spaceship_rel'
    _description = 'colony_spaceship_rel'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.spaceship')
    colony_id = fields.Many2one('expanse.colony')
    qty = fields.Integer()
    fabrications = fields.One2many('expanse.colony_spaceship_fabrication', 'spaceship_id')
    fabrications_queue = fields.Integer(compute="_get_fabrications_queue")
    fabrications_progress = fields.Float(compute="_get_fabrications_queue")

    def _get_fabrications_queue(self):
        for c in self:
            c.fabrications_queue = len(c.fabrications)
            c.fabrications_progress = 0
            if (c.fabrications_queue >= 1):
                c.fabrications_progress = c.fabrications[0].progress

    def add_to_battle(self):  # ORM
        for c in self:
            if (c.qty > 0):
                battle_id = self.env['expanse.battle'].browse(self.env.context['ctx_battle'])[0]
                current_spaceships = battle_id.spaceship1_list.filtered(
                    lambda s: s.spaceship_id.id == c.spaceship_id.id)
                if len(current_spaceships) == 0:
                    current_spaceships = self.env['expanse.battle_spaceship_rel'].create({
                        "spaceship_id": c.spaceship_id.id,
                        "battle_id": battle_id.id,
                        "qty": 0
                    })
                if current_spaceships.qty < c.qty:
                    current_spaceships.qty += 1
                # c.qty -= 1
    def add_to_battle_wizard(self):
        for c in self:
            if (c.qty > 0):
                battle_id = self.env['expanse.battle_wizard'].browse(self.env.context['ctx_battle'])[0]
                current_spaceships = battle_id.spaceship1_list.filtered(
                    lambda s: s.spaceship_id.id == c.spaceship_id.id)
                if len(current_spaceships) == 0:
                    current_spaceships = self.env['expanse.battle_spaceship_rel_wizard'].create({
                        "spaceship_id": c.spaceship_id.id,
                        "battle_id": battle_id.id,
                        "qty": 0
                    })
                if current_spaceships.qty < c.qty:
                    current_spaceships.qty += 1
                # c.qty -= 1
        return {
            'name': 'Create Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'expanse.battle_wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': battle_id.id
        }

class colony_spaceship_fabrication(models.Model):
    _name = 'expanse.colony_spaceship_fabrication'
    _description = 'Spaceship fabrication model'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.colony_spaceship_rel')
    progress = fields.Float()  # ORM CRON
    time_remaining = fields.Float()

    @api.model
    def update_fabrication(self):
        for s in self.env['expanse.colony_spaceship_rel'].search([]).filtered(lambda rel: len(rel.fabrications) > 0):
                print(s.fabrications)
                spaceship_in_queue = s.fabrications[0]
                time = spaceship_in_queue.time_remaining - 1
                progress = 100 - 100*(time / s.spaceship_id.time)
                if time <= 0:
                    s.qty += 1
                    #print("Deleted",spaceship_in_queue)
                    spaceship_in_queue.unlink()

                else:
                    spaceship_in_queue.write({"time_remaining": time, "progress": progress})
                    print("Updated", spaceship_in_queue)

class building(models.Model):
    _name = 'expanse.building'
    _description = 'Buildings'

    name = fields.Char(related='type.name')
    image = fields.Image(related='type.image')
    type = fields.Many2one('expanse.building_type', ondelete="restrict")
    level = fields.Integer(default=1)
    colony = fields.Many2one('expanse.colony', ondelete="cascade")
    price_base = fields.Float(related='type.price_base')
    water_production = fields.Float(compute='_get_productions')
    energy_production = fields.Float(compute='_get_productions')
    metal_production = fields.Float(compute='_get_productions')
    hydrogen_production = fields.Float(compute='_get_productions')
    food_production = fields.Float(compute='_get_productions')
    stopped = fields.Boolean(compute='_get_productions')
    temporal = fields.Integer()

    @api.constrains('level')
    def check_level(self):
        for b in self:
            if b.level > 10:
                raise ValidationError("Level cant be more than 10")

    def _get_productions(self):
        for b in self:
            level = b.level
            # Expected productions
            water_production = b.type.water_production * level
            metal_production = b.type.metal_production * level
            hydrogen_production = b.type.hydrogen_production * level
            food_production = b.type.food_production * level
            energy = b.type.energy_production * level

            if water_production + b.colony.water >= 0 and metal_production + b.colony.metal >= 0 and hydrogen_production + b.colony.hydrogen >= 0 and food_production + b.colony.food >= 0 and energy + b.colony.energy >= 0:
                b.water_production = water_production
                b.metal_production = metal_production
                b.hydrogen_production = hydrogen_production
                b.food_production = food_production
                b.energy_production = energy
                b.stopped = False
            else:
                b.water_production = 0
                b.metal_production = 0
                b.hydrogen_production = 0
                b.food_production = 0
                b.energy_production = 0
                b.stopped = True

    def update_level(self):
        for b in self:
            if b.colony.money >= (b.price_base ** b.level):
                b.level += 1
                b.colony.player.money -= (b.price_base ** b.level)
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'You need '+str(b.price_base ** b.level)+' money',
                        'type': 'danger',  # types: success,warning,danger,info
                        'sticky': False
                    }
                }

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

    def build(self):  # ORM
        for b in self:
            colony_id = self.env['expanse.colony'].browse(self.env.context['ctx_colony'])[0]
            if colony_id.money >= b.price_base:
                self.env['expanse.building'].create({
                    "colony": colony_id.id,
                    "type": b.id
                })
                colony_id.player.money -= b.price_base





class template(models.Model):
    _name = 'expanse.template'
    _description = 'Templates'


    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    type = fields.Selection([('1', 'spaceships'), ('2', 'planets')])


class player_wizard(models.TransientModel):
    _name = 'expanse.player_wizard'
    _description = 'Wizard per crear players'

    def _default_client(self):
        return self.env['res.partner'].browse(self._context.get('active_id'))  # El context conté, entre altre coses,
        # el active_id del model que està obert.
    name = fields.Many2one('res.partner',default=_default_client, required=True)
    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)

    @api.model
    def default_get(self, default_fields):
        result = super(player_wizard, self).default_get(default_fields)
        result['avatar'] =self.env.ref('expanse.template_player_placeholder').image
        return result


    def create_player(self):
        self.ensure_one()
        self.name.write({'password': self.password,
                         'avatar': self.avatar,
                         'is_player': True
                         })


