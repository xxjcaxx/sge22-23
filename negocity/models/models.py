# -*- coding: utf-8 -*-


from odoo import models, fields, api
import random
import math
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
## from odoo.exceptions import Warning   (Es considera obsolet en favor de UserError)
from odoo.exceptions import UserError


class event(models.Model):
    _name = 'negocity.event'
    _description = 'Events'

    name = fields.Char()
    player = fields.Many2many('res.partner')
    event = fields.Reference([('negocity.building','Building'),('negocity.travel','Travel'),('negocity.collision','Collision'),('negocity.player','Player'),('negocity.survivor','Survivor')])
    description = fields.Text()

    @api.model
    def clean_messages(self):
        yesterday = fields.Datetime.to_string(datetime.now()-timedelta(hours=24))
        old_messages = self.search([('creation_date','<',yesterday)])
        old_messages.unlink()



    ### TODO



    ### Wizards:  Create building , cReate travel, generate full game