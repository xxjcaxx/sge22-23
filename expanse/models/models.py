# -*- coding: utf-8 -*-

from odoo import models, fields, api


class player(models.Model):
     _name = 'expanse.player'
     _description = 'Players of the game'

     name = fields.Char(required=True)
     password = fields.Char()
     avatar = fields.Image(max_width = 200, max_height=200)
     colonies = fields.One2many('expanse.colony','player')

class planet(models.Model):
     _name = 'expanse.planet'
     _description = 'Planets'

     name = fields.Char(required=True)
     image = fields.Image(max_width = 200, max_height=200)
     size = fields.Float()
     colonies = fields.One2many('expanse.colony', 'planet')

class colony(models.Model):
     _name = 'expanse.colony'
     _description = 'Colonies'

     name = fields.Char(required=True)
     planet = fields.Many2one('expanse.planet')
     player = fields.Many2one('expanse.player')

class spaceship(models.Model):
     _name = 'expanse.spaceship'
     _description = 'Spaceships'