# -*- coding: utf-8 -*-

from odoo import models, fields, api


class player(models.Model):
     _name = 'expanse.player'
     _description = 'Players of the game'

     name = fields.Char(required=True)
     password = fields.Char()
