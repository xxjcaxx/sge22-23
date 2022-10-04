# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError



class city(models.Model):
    _name = 'negocity.city'
    _description = 'Cities'

    def _generate_name(self):
        first = ["Uncanny", "Remote", "Abandoned", "Neglected", "Eastern", "Dead", "Whispering", "Unfriendly", "Unpleasant", "Nasty"
                                                                                                   "Darkest", "Broken",
                 "Rotten", "Sunny", "Dead", "Wild", "Forgotten", "Distressing", "Unlikeable", "Rough",
                 "Hard", "Sharp", "Thug", "Bully", "Disruptive", "Oily", "Burned", "Sunken", "Hollow"
                                                                                             "Burning", "Frozen", "Sad",
                 "Big", "Creepy", "Desolate", "Polluted", "Fecal", "Infected", "Tainted"]
        second = ["Tundra", "Badlands", "Flatlands", "Desert", "Flat", "Paramo", "Desierto",
                  "Dunghill", "Sands", "Rocks", "Dry Land", "Borderlands", "Frontier", "Ruins",
                  "Cliff", "Junk", "Crater", "City", "Suburbs", "Underground", "Dump", "Graveyard", "Plain", "Debris"]
        return random.choice(first) + " " + random.choice(second)

    name = fields.Char(default=_generate_name)

    energy = fields.Float()
    oil = fields.Float()
    food = fields.Float()
    water = fields.Float()
    despair = fields.Float(default=50)  # %
    radiation = fields.Float(default=50)  # %
    junk = fields.Float(default=1000)  # junk és la "moneda" del joc

    buildings = fields.One2many('negocity.building', 'city')
    unfinished_buildings = fields.Many2many('negocity.building', compute='_get_unfinished_buildings')
    survivors = fields.One2many('negocity.survivor', 'city')
    players = fields.Many2many('res.partner', compute='_get_players', string='Players with survivors')
    unemployed_survivors = fields.Many2many('negocity.survivor', compute='_get_unemployed')
    survivors_player = fields.Many2many('negocity.survivor', compute='_get_unemployed')
    vehicles_player = fields.Many2many('negocity.vehicle', compute='_get_unemployed')
    all_vehicles =  fields.One2many('negocity.vehicle', 'city')
    abandoned_vehicles = fields.Many2many('negocity.vehicle', compute='_get_vehicles')
    position_x = fields.Integer()
    position_y = fields.Integer()
    roads = fields.Many2many('negocity.road',compute='_get_roads')
    travels_going = fields.Many2many('negocity.travel', compute='_get_travels_coming')
    travels_coming = fields.Many2many('negocity.travel',compute='_get_travels_coming')
    #travel_collisions = fields.Many2many('negocity.collision', compute='_get_travels_coming')

    @api.depends('buildings')
    def _get_unfinished_buildings(self):
        for c in self:
            c.unfinished_buildings = c.buildings.filtered(lambda b: b.progress < 100)


    @api.depends('survivors')
    def _get_players(self):
        for c in self:
            players = c.survivors.filtered(lambda s: s.player.id != False).player.ids
            c.players = players

    @api.depends('all_vehicles')
    def _get_vehicles(self):
        for c in self:
            c.abandoned_vehicles = c.all_vehicles.filtered(lambda v: v.survivor.id == False)

    @api.depends('survivors')
    def _get_unemployed(self):
        for c in self:
            unemployed_survivors = c.survivors - c.buildings.workers  # Operacions en recordsets
            survivors_player = c.survivors 
            vehicles_player = c.survivors.vehicles
            if 'player' in self.env.context:
                unemployed_survivors = unemployed_survivors.filtered(lambda s: s.player.id == self.env.context['player'])
                survivors_player = survivors_player.filtered(lambda s: s.player.id == self.env.context['player'])
                vehicles_player = survivors_player.vehicles
            c.unemployed_survivors = unemployed_survivors
            c.survivors_player = survivors_player
            c.vehicles_player = vehicles_player
            

    @api.model
    def action_generate_cities(self):
        print('**************Generate')
        existent_cities = self.search([])
        existent_cities.unlink()
        board = [[0 for x in range(50)] for y in range(50)]
        new_cities = self

        if len(existent_cities) != -1:
            positions = [x for x in range(2500)]
            random.shuffle(positions)
            # print(positions)
            for i in range(0, 50):
                x = math.floor(positions[i] / 50)
                y = positions[i] % 50
                print(x, y)
                board[x][y] = 1
                new_city = self.create({
                    "energy": random.random() * 100,
                    "oil": random.random() * 100,
                    "food": random.random() * 100,
                    "water": random.random() * 100,
                    "radiation": random.random() * 100,
                    "position_x": x,
                    "position_y": y})
                new_cities = new_cities | new_city
                # Els edificis de la ciutat
                for i in range(0, random.randint(1, 10)):  # Pot crear fins a 10 edificis en ruines
                    tipus = random.choice(self.env['negocity.building_type'].search([]).ids)
                    self.env['negocity.building'].create({
                        'type': tipus,
                        'city': new_city.id,
                        'ruined': 100
                    })

            # Les carreteres
            all_roads = False
            i = 1
            while all_roads == False:
                all_roads = True

                for c in new_cities:
                    distancias = new_cities.sorted(key=lambda r: math.sqrt(
                        (r.position_x - c.position_x) ** 2
                        + (r.position_y - c.position_y) ** 2)
                                                   )
                    # Si no exiteix previament una igual
                    if len(distancias) > i:
                        # print('i:',i)
                        if (len(self.env['negocity.road'].search(
                                [('city_1', '=', distancias[i].id), ('city_2', '=', c.id)])) == 0):
                            # print(self.env['negocity.road'].search([('city_2','=', distancias[i].id),('city_1','=', c.id)]))
                            if (len(self.env['negocity.road'].search(
                                    [('city_2', '=', distancias[i].id), ('city_1', '=', c.id)])) == 0):
                                # print('Mateixa',c.id)
                                # Si no té colisió
                                # https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
                                def ccw(A, B, C):
                                    return (C.position_y - A.position_y) * (B.position_x - A.position_x) > (
                                                B.position_y - A.position_y) * (C.position_x - A.position_x)

                                # Return true if line segments AB and CD intersect
                                def intersect(A, B, C, D):
                                    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

                                colisionen = self.env['negocity.road'].search([]).filtered(
                                    lambda r: intersect(r.city_1, r.city_2, c, distancias[i]))
                                if len(colisionen) == 0:
                                    self.env['negocity.road'].create(
                                        {'city_1': c.id, 'city_2': distancias[i].id})  # la primera és ella mateixa
                                    all_roads = False
                i = i + 1
                print(all_roads, i)

    def create_npc(self):
        for c in self:
            template = random.choice(self.env['negocity.character_template'].search([]).mapped(lambda t: t.id))
            self.env['negocity.survivor'].create({'template': template, 'city': c.id})
    
    def _get_roads(self):
        for c in self:
            c.roads = self.env['negocity.road'].search(['|',('city_1','=', c.id),('city_2','=', c.id)]).ids


    def _get_travels_coming(self):
        for c in self:
           # c.travels_coming = self.env['negocity.travel'].search([('destiny','=',c.id),('date_end','>',fields.datetime.now())])  # No funciona perquè date_end és computed
            c.travels_coming = self.env['negocity.travel'].search([('destiny','=',c.id)]).filtered(lambda t: t.date_end >fields.datetime.now()) 
            #c.travels_going = self.env['negocity.travel'].search([('origin', '=', c.id), ('date_end', '>', fields.datetime.now())])
            c.travels_going = self.env['negocity.travel'].search([('origin', '=', c.id)]).filtered(lambda t: t.date_end >fields.datetime.now()) 
            # treure les colisions
