# -*- coding: utf-8 -*-


from itertools import filterfalse
from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
## from odoo.exceptions import Warning   (Es considera obsolet en favor de UserError)
from odoo.exceptions import UserError


class survivor(models.Model):
    _name = 'negocity.survivor'
    _description = 'Survivors'

    def _generate_name(self):
        first = ["Commander", "Bullet", "Imperator", "Doof", "Duff", "Immortal", "Big", "Grease", "Junk", "Rusty"
                                                                                                          "Gas", "War",
                 "Feral", "Blood", "Lead", "Max", "Sprog", "Allan", "Smoke", "Wagon", "Baron", "Leather", "Rotten"
                                                                                                          "Salt",
                 "Slake", "Sick", "Sickly", "Nuke", "Oil", "Night", "Water", "Tank", "Rig", "People", "Nocturne",
                 "Satanic"
                 "Dead", "Wandering", "Suffering", "Unfit", "Deadly", "Mike", "Nomad", "Mad", "Jhonny", "Unpredictable",
                 "Freakish", "Snake", "Praying"]
        second = ["Killer", "Rider", "Cutter", "Guts", "Eater", "Warrior", "Colossus", "Blaster", "Gunner", "Smith",
                  "Doe"
                  "Farmer", "Rock", "Claw", "Boy", "Girl", "Driver", "Ace", "Quick", "Blitzer", "Fury", "Roadster",
                  "Interceptor", "Bastich", "Dweller", "Thief", "Bleeder", "Face", "Mutant", "Anomaly", "Risk",
                  "Garcia", "Salamanca", "Goodman", "Sakura", "Bleding Gums", "Absent", "Hybrid", "Desire", "Bubblegum"
            , "Serpente", "Petal", "Dust", "Mantis", "Preacher", "Harkonnen", "Heisenberg", "Vonn Newman"]
        print('****************************GENERATE')
        return random.choice(first) + " " + random.choice(second)

    name = fields.Char(default=_generate_name)
    desperation = fields.Float(default=50)
    mutations = fields.Float(default=1)
    illnes = fields.Float(default=1)
    template = fields.Many2one('negocity.character_template', ondelete='restrict')
    avatar = fields.Image(max_width=200, max_height=400, related='template.image')

    city = fields.Many2one('negocity.city', ondelete='restrict')

   
    player = fields.Many2one('res.partner',  ondelete='set null' )
    vehicles = fields.One2many('negocity.vehicle', 'survivor')
    def get_default_junk(self):
        print(self.env.context)
        if 'default_junk' in self.env.context:
            return self.env.context['default_junk']
        else:
            return 0     
    junk = fields.Integer(default=0)
    building = fields.Many2many('negocity.building')

    travel = fields.Many2one('negocity.travel')

    
    def donate_junk(self):
        for s in self:
            s.city.junk =  s.city.junk + s.junk
            s.junk = 0

    def kill(self):
        for s in self:
            s.illnes = 100
            for v in s.vehicles:
                v.survivor = False
            self.env['negocity.event'].create(
                    {'name': 'Survivor Killed ' + s.name, 'player': s.player, 'event': 'negocity.survivor,' + str(s.id),
                     'description': 'Survivor Killed '+str(s.name)})
    def reanimate(self):
        for s in self:
            s.illnes = 0

    def assign_random_car(self):
        for s in self:
            vehicle = self.env['negocity.vehicle_template'].get_random_vehicle()
            vehicle.write({
                'survivor': s.id,
                'city': s.city.id,
            })

    @api.model
    def update_survivor(self):
        alive_survivors = self.search([('illnes','<',100)])
        print("Updating survivors in: ",alive_survivors)
        for s in alive_survivors:
            basic_needs = 1
            if s.city:
            # menja
                if s.city.food > 0:
                    s.city.food = s.city.food - 1
                    basic_needs -= 0.5
                if s.city.water > 0:
                    s.city.water = s.city.water - 1
                    basic_needs -= 1
    
    
            illnes = s.illnes + basic_needs + (s.mutations/10) 
           
            if illnes >= 100:
                s.kill()  # S'ha mort
            if illnes < 0:
                illnes = 0

            # Actualizamos su felicidad en función de si come y bebe, de la desesperacion de la ciudad i sus edificios y de si está ocupado o no
            desperation =  s.desperation + basic_needs  
            if s.city.despair > 50:
                desperation += 1
            if desperation <= 0:
                desperation = 0

            if desperation >=100:
                desperation = 100
                if random.random() > 0.99:
                    s.kill()  # Es suicida
                if random.random() > 0.99:
                    victim = random.choice(s.city.survivors.ids)
                    self.browse(victim).kill() # Mata a un altre supervivent aleatoriament en la ciutat
            
            mutations = s.mutations
            if s.city.radiation > 50 and random.random() < s.city.radiation/5000 :
                mutations = s.mutations + 1
            

            s.write({'illnes': illnes, 'desperation': desperation, 'mutations': mutations})
            #print(s.read(['name','illnes','desperation','mutations']))
           
            
            # Actualizamos sus mutaciones en función de la radiación