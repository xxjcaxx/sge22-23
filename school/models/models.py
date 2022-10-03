# -*- coding: utf-8 -*-

from odoo import models, fields, api


class student(models.Model):
    _name = 'school.student'
    _description = 'The students'
    name = fields.Char(string="Nombre",required=True)
    year = fields.Integer()
    topic_id = fields.Many2many("school.topic")

class topic(models.Model):
    _name = 'school.topic'
    _description = 'The topics'
    name = fields.Char(string="Topic name",required=True)
    student_ids = fields.Many2many("school.student")