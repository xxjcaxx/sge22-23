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

class course(models.Model):
    _name = 'school.course'
    _description = 'Courses'

    name = fields.Char()
    topics = fields.Many2many('school.topic')
    students = fields.Many2many('school.student')
    repeaters = fields.Many2many(comodel_name='school.student', # El model en el que es relaciona
                            relation='course_students_repeaters_rel', # (opcional) el nom del la taula en mig
                            column1='course_id', # (opcional) el nom en la taula en mig de la columna d'aquest model
                            column2='student_id')  # (opcional) el nom de la columna de l'altre model.

class teacher(models.Model):
    _name = 'res.partner'
    _description = 'The teachers'
    _inherit = 'res.partner'
    #name = fields.Char(string="Nombre",required=True)
    year = fields.Integer()
    topic_id = fields.Many2many("school.topic")