# -*- coding: utf-8 -*-
# from odoo import http


# class Expanse(http.Controller):
#     @http.route('/expanse/expanse', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/expanse/expanse/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('expanse.listing', {
#             'root': '/expanse/expanse',
#             'objects': http.request.env['expanse.expanse'].search([]),
#         })

#     @http.route('/expanse/expanse/objects/<model("expanse.expanse"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('expanse.object', {
#             'object': obj
#         })
