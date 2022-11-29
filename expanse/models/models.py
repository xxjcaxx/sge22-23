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
    _name = 'expanse.player'
    _description = 'Players of the game'

    name = fields.Char(required=True, string="Player Name")
    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)
    avatar_tumb = fields.Image(related="avatar", max_width=50, max_height=50)
    colonies = fields.One2many('expanse.colony', 'player')
    colonies_qty = fields.Integer(compute="get_colonies_qty")
    spaceships = fields.Many2many('expanse.colony_spaceship_rel', compute='_get_spaceships')
    money = fields.Float()

    @api.depends('colonies')
    def get_colonies_qty(self):
        for p in self:
            p.colonies_qty = len(p.colonies)

    @api.depends('colonies')
    def _get_spaceships(self):
        for p in self:
            p.spaceships = p.colonies.spaceships


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
    player = fields.Many2one('expanse.player', ondelete="cascade")
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


class battle(models.Model):
    _name = 'expanse.battle'
    _description = 'Battles'

    name = fields.Char()
    date_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    date_end = fields.Datetime(compute='_get_time')  # Calcul de dates
    time = fields.Float(compute='_get_time')
    distance = fields.Float(compute='_get_time')
    progress = fields.Float()
    state = fields.Selection([('1', 'Preparation'), ('2', 'Launched'), ('3', 'Finished')], default='1')
    player1 = fields.Many2one('expanse.player')
    player2 = fields.Many2one('expanse.player')
    colony1 = fields.Many2one('expanse.colony')
    colony2 = fields.Many2one('expanse.colony')
    spaceship1_list = fields.One2many('expanse.battle_spaceship_rel', 'battle_id')
    spaceship1_available = fields.Many2many('expanse.colony_spaceship_rel', compute='_get_spaceships_available')
    total_power = fields.Float()  # ORM Mapped
    winner = fields.Many2one()
    draft = fields.Boolean()

    @api.onchange('player1')
    def onchange_player1(self):
        self.name = self.player1.name
        return {
            'domain': {
                'colony1': [('id', 'in', self.player1.colonies.ids)],
                'player2': [('id', '!=', self.player1.id)],
            }
        }

    @api.onchange('player2')
    def onchange_player2(self):
        return {
            'domain': {
                'colony2': [('id', 'in', self.player2.colonies.ids)],
                'player1': [('id', '!=', self.player2.id)],
            }
        }

    @api.depends('colony1')
    def _get_spaceships_available(self):
        for b in self:
            b.spaceship1_available = b.colony1.spaceships.ids

    @api.depends('spaceship1_list', 'colony2', 'colony1')
    def _get_time(self):
        for b in self:
            b.time = 0
            b.distance = 0
            b.date_end = fields.Datetime.now()
            if len(b.colony1) > 0 and len(b.colony2) > 0 and len(b.spaceship1_list) > 0 and len(b.spaceship1_list.spaceship_id) > 0:
                b.distance = b.colony1.planet.distance(b.colony2.planet)
                min_speed = b.spaceship1_list.spaceship_id.sorted(lambda s: s.speed).mapped('speed')[0]
                b.time = b.distance / min_speed
                b.date_end = fields.Datetime.to_string(
                    fields.Datetime.from_string(b.date_start) + timedelta(minutes=b.time))

    def launch_battle(self):
        for b in self:
            if len(b.colony1) == 1 and len(b.colony2) == 1 and len(b.spaceship1_list) > 0 and b.state == '1':

                b.date_start = fields.Datetime.now()
                b.progress = 0
                for s in b.spaceship1_list:
                    spaceship_available = \
                        b.spaceship1_available.filtered(lambda s_a: s_a.spaceship_id.id == s.spaceship_id.id)[0]
                    spaceship_available.qty -= s.qty
                b.state = '2'

    def back(self):
        for b in self:
            if b.state == '2':
                b.state = '1'

    # In each round, all participating units(defenses+ships) randomly choose a target enemy unit.
    #
    # For each shooting unit:
    #
    #     If the Weaponry of the shooting unit is less than 1% of the Shielding of the target unit, the shot is bounced, and the target unit does not lose anything (i.e. shot is wasted).
    #     Else, if the weaponry is lower than the Shielding, then the shield absorbs the shot, and the unit does not lose Hull Plating: S = S - W.
    #     Else, the weaponry is sufficiently strong, i.e. W > S. Then the shield only absorbs part of the shoot and the rest is dealt to the hull: H = H - (W - S) and S = 0.
    #     If the Hull of the target ship is less than 70% of the initial Hull (H_i) of the ship (initial of the combat), then the ship has a probability of 1 - H/H_i of exploding. If it explodes, the hull is set to zero: H = 0. (but it can still be shot by the other units on this round, because they already target it.)
    #     Finally, if the shooting unit has rapid fire (with value r) against the target unit, it has a chance of (r-1)/r of choosing another target at random, and repeating the above steps for that new target.

    def execute_battle(self):
        for b in self:
            result = b.simulate_battle()

    def simulate_battle(self):
            b = self
            winner = False
            draft = False
            spaceships1 = b.spaceship1_list.mapped(lambda s: [s.spaceship_id.read(['id','damage','armor','capacity'])] * s.qty)
            spaceships1 = [spaceship for sublist in spaceships1 for spaceship in sublist]

            spaceships2 = b.colony2.spaceships.mapped(lambda s: [s.spaceship_id.read(['id','damage','armor','capacity'])] * s.qty)
            spaceships2 = [spaceship for sublist in spaceships2 for spaceship in sublist]

            for i in range(0, 6):  # 6 rondes com a màxim
                # Attack
                if len(spaceships1) > 0 and len(spaceships2) > 0:
                    print("ROUND",i,spaceships1, spaceships2)
                    for attacker in spaceships1:
                        target = random.choice(spaceships2)
                        if attacker['damage'] > target['armor'] / 100 or random.random() > 0.90:  # Bounce
                            target['armor'] -= random.random() * attacker['damage']

                    # Defense
                    for defender in spaceships2:
                        target = random.choice(spaceships1)
                        if defender['damage'] > target['armor'] / 100 or random.random() > 0.90:  # Bounce
                            target['armor'] -= random.random() * defender['damage']

                    spaceships1 = list(filter(lambda s: s['armor'] > 0, spaceships1))
                    spaceships2 = list(filter(lambda s: s['armor'] > 0, spaceships2))
            if len(spaceships1) == 0 and len(spaceships2) > 0:
                winner = b.player2.id
            if len(spaceships1) > 0 and len(spaceships2) == 0:
                winner = b.player1.id
            if len(spaceships1) > 0 and len(spaceships2) > 0:
                draft = True

            return {"winner": winner, "draft": draft}


class battle_spaceship_rel(models.Model):
    _name = 'expanse.battle_spaceship_rel'
    _description = 'battle_spaceship_rel'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.spaceship')
    battle_id = fields.Many2one('expanse.battle')
    qty = fields.Integer()


class template(models.Model):
    _name = 'expanse.template'
    _description = 'Templates'

    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    type = fields.Selection([('1', 'spaceships'), ('2', 'planets')])
