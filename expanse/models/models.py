# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
import string
from odoo.exceptions import ValidationError

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
        print("reset",self)
        self.env['expanse.planet'].search([]).unlink()
        images = self.env['expanse.template'].search([('type', '=', '2')]).mapped('image')
        for i in range(0,100): # Crear planetes
            self.env['expanse.planet'].create({   #ORM
                "name": name_generator(),
                "size": random.betavariate(1.5,1.1)*1000,
                "image": random.choice(images),
                "coordinates": str(random.randint(0,10000))+","+str(random.randint(0,10000))+","+str(random.randint(0,10000))
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
    spaceships = fields.Many2many('expanse.colony_spaceship_rel',compute='_get_spaceships')
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

    def distance(self,other_planet):
        c1 = list(map(lambda c: int(c),self.coordinates.split(',')))
        c2 = list(map(lambda c: int(c), other_planet.coordinates.split(',')))
        # d = ((x2 - x1)2 + (y2 - y1)2 + (z2 - z1)2)1/2
        distance = ((c2[0]-c1[0])**2 + (c2[1]-c1[1])**2 + (c2[2]-c1[2])**2)**0.5
        print(distance, c1, c2)


class colony(models.Model):
    _name = 'expanse.colony'
    _description = 'Colonies'

    name = fields.Char(required=True)
    planet = fields.Many2one('expanse.planet',ondelete="cascade")
    player = fields.Many2one('expanse.player',ondelete="cascade")
    player_avatar = fields.Image(related="player.avatar", string="Player Avatar")
    money = fields.Float(related="player.money")

    buildings = fields.One2many('expanse.building', 'colony')
    hangar_level = fields.Integer(default = 0)
    spaceships = fields.One2many('expanse.colony_spaceship_rel','colony_id')
    available_spaceships = fields.Many2many('expanse.spaceship',compute="_get_available_spaceships")

    water = fields.Float()
    energy = fields.Float()
    metal = fields.Float()
    hydrogen = fields.Float()
    food = fields.Float()

    @api.depends('hangar_level')
    def _get_available_spaceships(self): #ORM
        for c in self:
            c.available_spaceships = self.env['expanse.spaceship'].search([('hangar_required','<=',c.hangar_level)])

    def update_hangar(self): #ORM
        for c in self:
            required_money = 10**c.hangar_level
            available_money = c.player.money
            if(required_money <= available_money):
                c.hangar_level += 1
                c.player.money = c.player.money - required_money


class spaceship(models.Model):
    _name = 'expanse.spaceship'
    _description = 'Spaceships'

    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    capacity = fields.Float()
    armor = fields.Float()
    damage = fields.Float()
    hangar_required = fields.Integer()
    time = fields.Float(compute = '_get_construction_time')

    def _get_construction_time(self):
        for s in self:
            s.time = (s.capacity+ 3*s.damage+ 2*s.armor)/13000

    def fabricate(self): #ORM
        for s in self:
            print('fabrica',self.env.context['ctx_colony'])
            colony = self.env['expanse.colony'].browse(self.env.context['ctx_colony'])
            colony_spaceship_rel = colony.spaceships.filtered(lambda c: c.spaceship_id.id == s.id)
            if(len(colony_spaceship_rel) == 0): # no té encara cap nau d'aquest tipus
                colony_spaceship_rel = self.env['expanse.colony_spaceship_rel'].create({
                    "spaceship_id": s.id,
                    "colony_id": colony.id,
                    "qty" : 0
                })
            self.env['expanse.colony_spaceship_fabrication'].create({
                "spaceship_id": colony_spaceship_rel.id,
                "progress": 0
            })


class colony_spaceship_rel(models.Model):
    _name = 'expanse.colony_spaceship_rel'
    _description = 'colony_spaceship_rel'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.spaceship')
    colony_id = fields.Many2one('expanse.colony')
    qty = fields.Integer()
    fabrications = fields.One2many('expanse.colony_spaceship_fabrication','spaceship_id')
    fabrications_queue = fields.Integer(compute="_get_fabrications_queue")
    fabrications_progress = fields.Float(compute="_get_fabrications_queue")

    def _get_fabrications_queue(self):
        for c in self:
            c.fabrications_queue = len(c.fabrications)
            c.fabrications_progress = 0
            if( c.fabrications_queue >= 1):
                c.fabrications_progress = c.fabrications[0].progress


    def add_to_battle(self): #ORM
        for c in self:
            print(c,self.env.context)

class colony_spaceship_fabrication(models.Model):
    _name = 'expanse.colony_spaceship_fabrication'
    _description = 'Spaceship fabrication model'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.colony_spaceship_rel')
    progress = fields.Float() #ORM CRON



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

    def produce(self): #ORM CRON
        for b in self:
            colony = b.colony
            water = colony.water + b.water_production
            metal = colony.metal + b.metal_production

            colony.write({
                "water": water,
                "metal": metal
            })



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


class battle(models.Model):
    _name = 'expanse.battle'
    _description = 'Battles'

    name = fields.Char()
    date_start = fields.Datetime()
    date_end = fields.Datetime()      # Calcul de dates
    player1 = fields.Many2one('expanse.player')
    player2 = fields.Many2one('expanse.player')
    colony1 = fields.Many2one('expanse.colony')
    colony2 = fields.Many2one('expanse.colony')
    spaceship1_list = fields.One2many('expanse.battle_spaceship_rel','battle_id')
    spaceship1_available = fields.Many2many('expanse.colony_spaceship_rel',compute='_get_spaceships_available')
    total_power = fields.Float()   # ORM Mapped


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
    type = fields.Selection([('1','spaceships'),('2','planets')])