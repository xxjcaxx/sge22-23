# -*- coding: utf-8 -*-
from odoo import http
import json
from odoo import tools
from odoo.fields import Integer

class banner_city_controller(http.Controller):
    @http.route('/negocity/city_banner', auth='user', type='json')
    def banner(self):
        return {
            'html': """
                <div  class="negocity_banner" style="height: 200px; background-size:100%; background-image: url(/negocity/static/src/img/negocity_city.jpg)">
                <div class="negocity_button" style="position: static; color:#fff;">
                <a class="banner_button" type="action" data-reload-on-close="true" 
                role="button" data-method="action_generate_cities" data-model="negocity.city">Generate Citiess</a>
                </div>
                </div> """
        }
# Podem resoldre el botó en un altre controller o amb una acció

################## API REST  ######################

    @http.route('/negocity/api/<model>', auth="none", cors='*', methods=["POST","PUT","OPTIONS"], csrf=False, type='json')
    def apipost(self, **args):
       print('APIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
       print(args, http.request.httprequest.method)
       model = args['model']
       if( http.request.httprequest.method == 'POST'):   #  {"jsonrpc":"2.0","method":"call","params":{"planet":{"name":"Trantor","average_temperature":20},"password":"1234"}}
           record = http.request.env['negocity.'+model].sudo().create(args[model])
           return record.read()
       if( http.request.httprequest.method == 'GET'):
           if 'id' in args:
               record = http.request.env['negocity.'+model].sudo().search([('id','=',args[model]['id'])])
           else:
               record = http.request.env['negocity.'+model].sudo().search([])
           return record.read()
       if( http.request.httprequest.method == 'PUT' or  http.request.httprequest.method == 'PATCH'):
           record = http.request.env['negocity.'+model].sudo().search([('id','=',args[model]['id'])])[0]
           record.write(args[model])
           return record.read()
       if(http.request.httprequest.method == 'DELETE'):
           record = http.request.env['negocity.'+model].sudo().search([('id','=',args[model]['id'])])[0]
           print(record)
           record.unlink()
           return record.read()

       return http.request.env['ir.http'].session_info()


    @http.route('/negocity/api/<model>', auth="none", cors='*', methods=["GET","DELETE"], csrf=False, type='http')
    def apiget(self, **args):
        print('APIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIGET')
        print(args, http.request.httprequest.method)
        model = args['model']
        id = []
        if 'id' in args:
           id = [('id','=',args['id'])]
       
        if (http.request.httprequest.method == 'GET'):
            record = http.request.env['negocity.' + model].sudo().search(id)
           # print(record.read())
            return http.Response(
            json.dumps(record.read(), default=tools.date_utils.json_default),
            status=200,
            mimetype='application/json'
           )
        if (http.request.httprequest.method == 'DELETE'):
            record = http.request.env['negocity.' + model].sudo().search([('id', '=', args[model]['id'])])[0]
            print(record)
            record.unlink()
            return http.Response(
                json.dumps(record.read()),
                status=200,
                mimetype='application/json'
            )

        return http.request.env['ir.http'].session_info()



##################### LOGIN



    @http.route('/negocity/login', auth='public', cors='*', type='json')
    def negocity_login(self, user, password, **kw):
        passs = http.request.env['negocity.player'].sudo().search([('login', '=', user)])
        
        if (passs):
            if passs[0].password == password:
                return {"login": "si", "id": passs[0].id, "name": passs[0].name}
            else:
                print('no pass')
                return {"login": "no"}
        else:
            print('no user')
            return {"login": "no"}


###############################  API NEGOCITY  #############


    @http.route('/negocity/api/survivors/<player>', auth="none", cors='*', methods=["GET","DELETE"], csrf=False, type='http')
    def survivors(self, **args):
        print('Survivors')
        print(args, http.request.httprequest.method)
        player = args['player']
       
        if (http.request.httprequest.method == 'GET'):
            record = http.request.env['negocity.survivor'].sudo().search([('player.id','=',player)])
           # print(record.read())
            return http.Response(
            json.dumps(record.read(), default=tools.date_utils.json_default),
            status=200,
            mimetype='application/json'
           )
        if (http.request.httprequest.method == 'DELETE'):
            record = http.request.env['negocity.survivor'].sudo().search([('id', '=', args['survivor']['id'])])[0]
            print(record)
            record.unlink()
            return http.Response(
                json.dumps(record.read()),
                status=200,
                mimetype='application/json'
            )

        return http.request.env['ir.http'].session_info()

    @http.route('/negocity/api/cities/<player>', auth="none", cors='*', methods=["GET","DELETE"], csrf=False, type='http')
    def cities(self, **args):
        print(' \033[93m API Cities \033[0m')
        print(args, http.request.httprequest.method)
        player = args['player']
       
        if (http.request.httprequest.method == 'GET'):
            record = http.request.env['negocity.city'].sudo().search([]).filtered(lambda c: int(player) in c.players.ids)
            print('RECORD: ',record.read())
            return http.Response(
            json.dumps(record.read(), default=tools.date_utils.json_default),
            status=200,
            mimetype='application/json'
           )
      
        return http.request.env['ir.http'].session_info()


    @http.route('/negocity/api/travel-query/', auth="none", cors='*', methods=["GET"], csrf=False, type='http')
    def travel_query(self, **args):
        print(' \033[93m API Travel Query \033[0m')
        print(args, http.request.httprequest.method)
        vehicle = int(args['vehicle'])
        road = int(args['road'])
       
        if (http.request.httprequest.method == 'GET'):
            oil = http.request.env['negocity.travel'].sudo().get_oil_required(vehicle,road)
            time = http.request.env['negocity.travel'].sudo().get_time(vehicle,road)
            print("OIL", oil, "Time" ,time)
            return http.Response(
             json.dumps({"oil_required": oil, "time": time, "vehicle": vehicle ,"road": road},  default=tools.date_utils.json_default),
             status=200,
             mimetype='application/json'
            )
      
        return http.request.env['ir.http'].session_info()



#class Negocity(http.Controller):
#     @http.route('/negocity/negocity/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/negocity/negocity/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('negocity.listing', {
#             'root': '/negocity/negocity',
#             'objects': http.request.env['negocity.negocity'].search([]),
#         })

#     @http.route('/negocity/negocity/objects/<model("negocity.negocity"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('negocity.object', {
#             'object': obj
#         })
