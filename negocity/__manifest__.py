# -*- coding: utf-8 -*-
{
    'name': "negocity",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','product','sale'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
'views/travels.xml',
        'views/cities.xml','views/players.xml','views/survivors.xml',
        'views/buildings.xml',  'views/vehicles.xml', 'views/collisions.xml',
        'views/templates.xml',
        'demo/character_templates.xml','demo/vehicles_templates.xml',
        'demo/building_types.xml',

        'crons/crons.xml',
'views/views.xml',
        'views/premium.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        
        'demo/demo.xml',
    ],

    'assets': {
    'web.assets_backend': [
        "/negocity/static/src/css/negocity.css",
    ],},
}
