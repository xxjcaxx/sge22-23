# -*- coding: utf-8 -*-


from email.policy import default
from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
## from odoo.exceptions import Warning   (Es considera obsolet en favor de UserError)
from odoo.exceptions import UserError


class road(models.Model):
    _name = 'negocity.road'
    _description = 'Road beween cities'

    name = fields.Char(compute='_get_name')
    city_1 = fields.Many2one('negocity.city', ondelete='cascade')
    city_2 = fields.Many2one('negocity.city', ondelete='cascade')
    distance = fields.Float(compute='_get_distance')

    @api.depends('city_1', 'city_2')
    def _get_name(self):
        for r in self:
            r.name = r.city_1.name + " <--> " + r.city_2.name

    @api.depends('city_1', 'city_2')
    def _get_distance(self):
        for r in self:
            r.distance = math.sqrt(
                (r.city_2.position_x - r.city_1.position_x) ** 2 + (r.city_2.position_y - r.city_1.position_y) ** 2)
            
   

class travel(models.Model):
    _name = 'negocity.travel'
    _description = 'Travels'

    name = fields.Char(compute='_get_name')
    origin = fields.Many2one('negocity.city', ondelete='cascade')
    destiny = fields.Many2one('negocity.city', ondelete='cascade')  # filtrat
    road = fields.Many2one('negocity.road', ondelete='cascade')  # computat
    date_departure = fields.Datetime()
    time = fields.Float(compute='_get_progress')
    date_end = fields.Datetime(compute='_get_progress')  # sera computat en funció de la distància
    progress = fields.Float(compute='_get_progress')
    state = fields.Selection([('preparation', 'Preparation'), ('inprogress', 'In Progress'), ('finished', 'Finished')],
                             default='preparation')

    player = fields.Many2one('res.partner')
    passengers = fields.Many2many('negocity.survivor')  # filtrats sols els que són de la ciutat origin i del player
    driver = fields.Many2one('negocity.survivor')
    vehicle = fields.Many2one('negocity.vehicle')
    oil_required = fields.Float(compute='_get_progress')
    oil_available = fields.Float(related='vehicle.gas_tank_level')
    collisions = fields.Many2many('negocity.collision',compute='_get_collisions')

    ######### Funcions utils ########
    @api.model
    def get_distance(self,road):
        time = road.distance  # En hores si va a 60k/h
        distance = time * 60
        return distance

    @api.model
    def get_oil_required(self,vehicle_id,road_id):
        vehicle = self.env['negocity.vehicle'].browse(vehicle_id)
        road = self.env['negocity.road'].browse(road_id)
        distance = self.get_distance(road)
        oil_required = (distance / 100) * vehicle.oil_consumption
        return oil_required

    @api.model
    def get_time(self,vehicle_id,road_id):
        vehicle = self.env['negocity.vehicle'].browse(vehicle_id)
        road = self.env['negocity.road'].browse(road_id)
        distance = self.get_distance(road)
        time = distance / vehicle.speed  #
        if time <= 0:
            time = 0.01

        return time


    @api.depends('origin', 'destiny', 'date_departure')
    def _get_name(self):
        for t in self:
            t.name = 'new Travel'
            if t.origin and t.destiny:
                t.name = t.origin.name + " --> " + t.destiny.name + " " + str(t.date_departure)

    @api.constrains('origin', 'destiny', 'road', 'player', 'passengers', 'driver', 'vehicle')
    def check_things(self):
        for t in self:
            if t.origin.id != t.road.city_1.id and t.origin.id != t.road.city_2.id or t.destiny.id != t.road.city_1.id and t.destiny.id != t.road.city_2.id:
                raise ValidationError('Incorrect Road')
            if t.driver.city.id != t.origin.id:
                raise ValidationError('Driver has to be in origin city')
            for p in t.passengers:
                if p.city.id != t.origin.id:
                    raise ValidationError('Passengers has to be in origin city')
            if t.vehicle.city.id != t.origin.id:
                raise ValidationError('Vehicle has to be in origin city')
            if t.driver.player.id != t.player.id:
                raise ValidationError('Driver has to be in player')
            for p in t.passengers:
                if p.player.id != t.player.id:
                    raise ValidationError('Passengers has to be in player')
                if p.illnes >= 100:
                    raise ValidationError('Passenger dead')
            if t.driver.illnes >= 100:
                raise ValidationError('Dead driver')
            if t.vehicle.junk_level >= 100:
                raise ValidationError('Junk vehicle')

    def launch_travel(self):
        for t in self:
            if t.oil_available >= t.oil_required:
                if t.vehicle.junk_level < 100:
                    t.date_departure = fields.datetime.now()
                    t.vehicle.city = False
                    t.driver.city = False
                    t.driver.travel = t.id
                    for p in t.passengers:
                        p.city = False
                    t.state = 'inprogress'
                    ## Mirar les collisions
                    current_travels = self.search([
                        ('destiny','=',t.origin.id),
                        ('road','=',t.road.id),
                        ('date_departure','!=',False),
                        ('date_end', '>', fields.datetime.now())])
                    for ct in current_travels:
                        self.env['negocity.collision'].create({
                            "name": ct.name + " " +t.name,
                            "travel1": ct.id,
                            "travel2": t.id,
                        })


                else:
                    raise UserError('Vehicle is not ready')
            else:
                raise UserError('Not Sufficient Oil for the travel')

    @api.onchange('origin')
    def _onchange_origin(self):
        if self.origin != False:
            roads_available = self.origin.roads  # self.env['negocity.road'].search(['|',('city_1','=', self.origin.id),('city_2','=', self.origin.id)])
            cities_available = roads_available.city_1 + roads_available.city_2 - self.origin
            players_in_city = self.origin.players.ids
            print(cities_available)
            return {
                'domain': {
                    'destiny': [('id', 'in', cities_available.ids)],
                    'player': [('id', 'in', players_in_city)]
                }
            }

    @api.onchange('destiny')
    def _onchange_destiny(self):
        if self.destiny != False:
            road_available = self.origin.roads & self.destiny.roads
            self.road = road_available.id
            return {}

    @api.onchange('player')
    def _onchange_player(self):
        if self.player != False:
            drivers_available = self.player.survivors.filtered(
                lambda s: s.city.id == self.origin.id and len(s.building) == 0)
            return {
                'domain': {
                    'driver': [('id', 'in', drivers_available.ids)],
                    'passengers': [('id', 'in', drivers_available.ids)]
                }
            }

    @api.onchange('driver')
    def _onchange_driver(self):
        if self.driver != False:
            vehicles = self.driver.vehicles
            return {
                'domain': {
                    'vehicle': [('id', 'in', vehicles.ids)]
                }
            }

    @api.depends('date_departure', 'road', 'vehicle')
    def _get_progress(self):
        for t in self:
            if t.road and t.vehicle:
                
                time = self.get_time(t.vehicle.id,t.road.id)
                t.time = time
                t.oil_required = self.get_oil_required(t.vehicle.id,t.road.id)
                #print(distance, t.vehicle.speed, time, t.oil_required)
                if t.date_departure:
                    d_dep = t.date_departure
                    data = fields.Datetime.from_string(d_dep)
                    data = data + timedelta(hours=time)
                    t.date_end = fields.Datetime.to_string(data)
                    time_remaining = fields.Datetime.context_timestamp(self,
                                                                       t.date_end) - fields.Datetime.context_timestamp(
                        self, datetime.now())
                    time_remaining = time_remaining.total_seconds() / 60 / 60
                    t.progress = (1 - time_remaining / time) * 100
                    if t.progress >= 100:
                        t.progress = 100
                else:
                    t.progress = 0
                    t.date_end = False

            else:
                t.progress = 0
                t.date_end = False
                t.oil_required = 0
                t.time = 0

    @api.model
    def update_travel(self):
        travels_in_progress = self.search([('state', '=', 'inprogress')])
        print("Updating progress in: ", travels_in_progress)
        for t in travels_in_progress:
            if t.progress >= 100:
                t.write({'state': 'finished'})

                ################  FALTA ELS PROBLEMES EN EL TRAVEL

                t.driver.write({'city': t.destiny.id})
                t.vehicle.write({'city': t.destiny.id, 'gas_tank_level': t.vehicle.gas_tank_level - t.oil_required})
                for p in t.passengers:
                    p.write({'city': t.destiny.id})
                self.env['negocity.event'].create(
                    {'name': 'Arrival travel ' + t.name, 'player': t.player, 'event': 'negocity.travel,' + str(t.id),
                     'description': 'Arrival travel... '})
                print('Arribal')

    def _get_collisions(self):
        for t in self:
            t.collisions = self.env['negocity.collision'].search(['|',('travel1','=',t.id),('travel2','=',t.id)]).ids



class collision(models.Model):
    _name = 'negocity.collision'
    _description = 'Collision in travels'

    name = fields.Char(compute='_get_name')
    travel1 = fields.Many2one('negocity.travel')
    car1 = fields.Many2one('negocity.vehicle',related='travel1.vehicle')
    travel2 = fields.Many2one('negocity.travel')
    car2 = fields.Many2one('negocity.vehicle',related='travel2.vehicle')
    date = fields.Datetime(compute = '_get_date',store=True)
    finished = fields.Boolean()


    @api.depends('travel1', 'travel2', 'date')
    def _get_name(self):
        for c in self:
            c.name = 'new collision'
            if c.travel1 and c.travel2:
                c.name = c.travel1.vehicle.name + " <--> " + c.travel2.vehicle.name

    @api.depends('travel1', 'travel2')
    def _get_date(self):
        for c in self:
            if c.travel1.date_departure and c.travel2.date_departure:
                vel1 = c.travel1.vehicle.speed
                vel2 = c.travel2.vehicle.speed
                distance = c.travel1.road.distance * 60  # Ja que està en hores
                date1 = c.travel1.date_departure
                date2 = c.travel2.date_departure
                diference = fields.Datetime.from_string(date2) - fields.Datetime.from_string(date1)
                diference = diference.total_seconds()/60/60
                remaining_distance = distance - vel1*diference
                relative_speed = vel1 + vel2
                time = remaining_distance / relative_speed
                date = fields.Datetime.to_string(fields.Datetime.from_string(date2)+timedelta(hours=time))
                print('\033[93m GET DATE COLLISION **********',vel1,vel2,distance,date1,date2,diference,remaining_distance,relative_speed,time,date,'\033[0m')
                c.date = date

    @api.model
    def update_collisions(self):
        current_collisions = self.search([('finished','=',False),('date','<',fields.datetime.now())])
        print("Updating collisions: ",current_collisions)
        for c in current_collisions:
            # Simular batalla
            v1 = c.travel1.vehicle
            v2 = c.travel2.vehicle
            resistence1 = v1.resistence * (100-v1.junk_level)   / 100
            resistence2 = v2.resistence * (100-v2.junk_level) / 100
           
            damage1 = v1.damage
            damage2 = v2.damage

            while resistence1 > 0 and resistence2 > 0:
                resistence1 -= damage2
                resistence2 -= damage1

            if resistence1 <= 0:
                # Ha perdut en 1
                message = 'You loose '+c.travel1.driver.name
                message += ' '
                for p in c.travel1.passengers:
                    message += ' '+p.name+' '
                message += ' in the vehicle: '+v1.name
                self.env['negocity.event'].create(
                    {'name': 'Collision ' + c.name, 'player': c.travel1.player, 'event': 'negocity.collision,' + str(c.id),
                     'description': message})
                self.env['negocity.event'].create(
                    {'name': 'Collision ' + c.name, 'player': c.travel2.player, 'event': 'negocity.collision,' + str(c.id),
                     'description': 'You win collision with: '+v2.name})
                v2.junk_level = 100 -(100 * resistence2 / v2.resistence)  # el mal que li ha fet
                v2.stole_gas(v1)

                c.travel1.driver.kill()
                for p in c.travel1.passengers:
                    p.kill()
                v1.destroy()

            if resistence2 <= 0:
                # Ha perdut en 1
                message = 'You loose '+c.travel2.driver.name
                message += ' '
                for p in c.travel2.passengers:
                    message += ' '+p.name+' '
                message += ' in the vehicle: '+v2.name
               
                self.env['negocity.event'].create(
                    {'name': 'Collision ' + c.name, 'player': c.travel2.player, 'event': 'negocity.collision,' + str(c.id),
                     'description': message})
                self.env['negocity.event'].create(
                    {'name': 'Collision ' + c.name, 'player': c.travel1.player, 'event': 'negocity.collision,' + str(c.id),
                     'description': 'You win collision with: '+v1.name})
                v1.junk_level = 100- (100 * resistence1 / v1.resistence)
                v1.stole_gas(v2)

                c.travel2.driver.kill()
                for p in c.travel2.passengers:
                    p.kill()
                v2.destroy()

            c.finished = True

class city_transient(models.TransientModel):
    _name = 'negocity.city_transient'

    city = fields.Many2one('negocity.city')
    wizard = fields.Many2one('negocity.travel_wizard')

    def select(self):
        road_available = self.wizard.origin.roads & self.city.roads

        self.wizard.write({'destiny': self.city.id,'road': road_available.id})

        return {
            'name': 'Negocity travel wizard action',
            'type': 'ir.actions.act_window',
            'res_model': self.wizard._name,
            'res_id': self.wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.wizard._context
        }


class survivor_transient(models.TransientModel):
    _name = 'negocity.survivor_transient'

    survivor = fields.Many2one('negocity.survivor')
    avatar = fields.Image(related='survivor.avatar')


    def select(self):
        wizard = self._context.get('travel_wizard_context')
        wizard = self.env['negocity.travel_wizard'].browse(wizard)
        print(wizard,'*************************')
        wizard.write({'passengers': [(4,self.survivor.id,0)]})
        return {
            'name': 'Negocity travel wizard action',
            'type': 'ir.actions.act_window',
            'res_model': wizard._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': wizard._context
        } 

class travel_wizard(models.TransientModel):
    _name = 'negocity.travel_wizard'
    _description = 'Wizard of travels'

    def _get_origin(self):
        city = self.env.context.get('city_context')
        return city

    def _get_player(self):
        player = self.env.context.get('player_context')
        return player

    name = fields.Char()
    origin = fields.Many2one('negocity.city', default = _get_origin)
    oil = fields.Float(related='origin.oil')
    origin_resume = fields.Many2one('negocity.city', related='origin')
    cities_available = fields.One2many('negocity.city_transient','wizard')

    destiny = fields.Many2one('negocity.city')  # filtrat
    destiny_resume = fields.Many2one('negocity.city', related='destiny')
    road = fields.Many2one('negocity.road')  # computat
    road_resume = fields.Many2one('negocity.road', related='road')  # computat
    date_departure = fields.Datetime(default = fields.Datetime.now, string='Date Departure (now)')
    time = fields.Float(compute='_get_time')
    date_end = fields.Datetime()  # sera computat en funció de la distància
    player = fields.Many2one('res.partner', default = _get_player )
    player_resume = fields.Many2one('res.partner', related='player' )
    passenger_available = fields.Many2many('negocity.survivor_transient', compute="_get_passenger_available")
    passengers = fields.Many2many('negocity.survivor')
    passengers_resume = fields.Many2many('negocity.survivor',related='passengers')
    driver = fields.Many2one('negocity.survivor')
    driver_resume = fields.Many2one('negocity.survivor',related='driver')
    vehicle = fields.Many2one('negocity.vehicle')
    vehicle_resume = fields.Many2one('negocity.vehicle',related='vehicle')
    oil_required = fields.Float(compute='_get_time')
    oil_required_resume = fields.Float(related='oil_required')
    not_oil= fields.Boolean(compute='_get_oil')
    oil_available = fields.Float(related='vehicle.gas_tank_level')
    oil_available_resume = fields.Float(related='vehicle.gas_tank_level')

    @api.depends('road','vehicle')
    def _get_time(self):
        for t in self:
            t.time = 0
            t.date_end = False
            t.oil_required = 0
            print('time0',t.vehicle,t.road)
            if t.vehicle and t.road:
                print('time')
                t.time = self.env['negocity.travel'].get_time(t.vehicle.id,t.road.id)
                t.oil_required = self.env['negocity.travel'].get_oil_required(t.vehicle.id, t.road.id)
                if t.date_departure:
                    d_dep = t.date_departure
                    data = fields.Datetime.from_string(d_dep)
                    data = data + timedelta(hours=t.time)
                    t.date_end = fields.Datetime.to_string(data)

    @api.onchange('origin')
    def _onchange_origin(self):
        if len(self.origin)>0:
            print('Onchange origin **************')
            roads_available = self.origin.roads
            cities_available = roads_available.city_1 + roads_available.city_2 - self.origin
            self.cities_available.unlink()
            for city in cities_available:
                self.env['negocity.city_transient'].create({'city': city.id, 'wizard': self.id})

        
            return {
                # 'domain': {
                #     'destiny': [('id', 'in', (self.cities_available.city).ids)],
                # }
            }


    @api.onchange('destiny')
    def _onchange_destiny(self):
        if len(self.destiny)>0:
           
            road_available = self.origin.roads & self.destiny.roads
            #self.search([('id','=',self._origin.id)]).write({'road': road_available.id})
            self._origin.write({'road': road_available.id})
            self.road = road_available.id
            
            return {}

    

    @api.depends('driver')
    def _get_passenger_available(self):
        passengers = self.env['negocity.survivor_transient']
        self.passenger_available = passengers

        if len(self.driver)>0 and len(self.origin)>0:
            passenger_available = self.origin.survivors.filtered(lambda s: s.player.id == self.player.id).filtered(lambda s: s.id != self.driver.id)

            print(passenger_available,self.origin.survivors,self.driver)
            
            for s in passenger_available:
                print(s)
                passengers = passengers + self.env['negocity.survivor_transient'].create({'survivor': s.id})

            print(passengers)
            self.passenger_available = passengers



    @api.onchange('driver')
    def _onchange_driver(self):
        if len(self.driver)>0 and len(self.origin)>0:
            print("*********** ONchange driver", self.driver, self.origin)
           


            return {
                'domain': {
                     'vehicle': [('survivor','=',self.driver.id),('city','=',self._context.get('origin_context'))],
                    'passengers': [('id','in',self.passenger_available.survivor.ids)],
                 }
            }


    @api.depends('vehicle')
    def _get_oil(self):
        print(self.oil_available , self.oil_required)
        self.not_oil = self.oil_available < self.oil_required

    state = fields.Selection([('origin','Origin'),('destiny','Destiny'),('driver','Driver'),('dates','Dates')], default = 'origin')
    ready = fields.Boolean(compute='_get_ready')

    def next(self):
        title = ''
        state = self.state
        if state == 'origin' and self.ready:
            self.state = 'destiny'
            title = 'Choose the destiny'
        elif state == 'destiny' and self.ready:
            self.state = 'driver'
            title = 'Choose the driver, car and passengers'
        elif state == 'driver' and self.ready:
            self.state = 'dates'
            title = 'It is all rigth?'

        if state == 'driver' and not self.ready:
            return {
               'type': 'ir.actions.client',
                'tag': 'display_notification',
               'params': {
            'message': 'Not sufficient Oil, vehicle or driver',
           'type': 'danger',  #types: success,warning,danger,info
            'sticky': False,
    }
}

        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self._context, cities_available_context= (self.cities_available.city).ids, origin_context = self.origin.id),
            #'domain': {'destiny': [('id', 'in', (self.cities_available.city).ids)]}
        }

    def previous(self):
        state = self.state
        if state == 'destiny':
            self.state = 'origin'
        elif state == 'driver':
            self.state = 'destiny'
        elif state == 'dates':
            self.state = 'driver'

        return {
            'name': 'Negocity travel wizard action',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self._context
        } 

       

        

    @api.depends('origin','player')
    def _get_ready(self):
        self.ready = False
        if (self.state == 'origin' and len(self.origin)==1 and len(self.player)==1):
            self.ready = True
        if (self.state == 'destiny' and len(self.destiny)==1):
            self.ready = True
        if (self.state == 'driver' and len(self.driver)==1 and len(self.vehicle)==1) and self.not_oil == False:
            self.ready = True
        

    def create_travel(self):
        travel = self.env['negocity.travel'].create({
           'origin': self.origin.id,
            'destiny': self.destiny.id,
            'road' : self.road.id,
            'date_departure': self.date_departure,
            'state': 'preparation',
            'player': self.player.id,
            'passengers': self.passengers.ids,
            'driver' : self.driver.id,
            'vehicle' : self.vehicle.id
        })
        return {
            'name': 'Negocity travel',
            'type': 'ir.actions.act_window',
            'res_model': 'negocity.travel',
            'res_id': travel.id,
            'view_mode': 'form',
            'target': 'current'
        }