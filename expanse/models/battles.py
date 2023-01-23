from odoo import fields, models, api



class battle(models.Model):
    _name = 'expanse.battle'
    _description = 'Battles'

    name = fields.Char()
    date_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    date_end = fields.Datetime(compute='_get_time')  # Calcul de dates
    time = fields.Float(compute='_get_time')
    distance = fields.Float(compute='_get_time')
    progress = fields.Float()
    state = fields.Selection([('1', 'Preparation'), ('2', 'Launched'), ('3', 'Finished')], default='1')
    player1 = fields.Many2one('res.partner')
    player2 = fields.Many2one('res.partner')
    colony1 = fields.Many2one('expanse.colony')
    colony2 = fields.Many2one('expanse.colony')
    spaceship1_list = fields.One2many('expanse.battle_spaceship_rel', 'battle_id')
    spaceship1_available = fields.Many2many('expanse.colony_spaceship_rel', compute='_get_spaceships_available')
    total_power = fields.Float()  # ORM Mapped
    winner = fields.Many2one()
    draft = fields.Boolean()

    @api.onchange('player1')
    def onchange_player1(self):
        self.name = self.player1.name
        return {
            'domain': {
                'colony1': [('id', 'in', self.player1.colonies.ids)],
                'player2': [('id', '!=', self.player1.id)],
            }
        }

    @api.onchange('player2')
    def onchange_player2(self):
        return {
            'domain': {
                'colony2': [('id', 'in', self.player2.colonies.ids)],
                'player1': [('id', '!=', self.player2.id)],
            }
        }

    @api.depends('colony1')
    def _get_spaceships_available(self):
        for b in self:
            b.spaceship1_available = b.colony1.spaceships.ids

    @api.depends('spaceship1_list', 'colony2', 'colony1')
    def _get_time(self):
        for b in self:
            b.time = 0
            b.distance = 0
            b.date_end = fields.Datetime.now()
            if len(b.colony1) > 0 and len(b.colony2) > 0 and len(b.spaceship1_list) > 0 and len(b.spaceship1_list.spaceship_id) > 0:
                b.distance = b.colony1.planet.distance(b.colony2.planet)
                min_speed = b.spaceship1_list.spaceship_id.sorted(lambda s: s.speed).mapped('speed')[0]
                b.time = b.distance / min_speed
                b.date_end = fields.Datetime.to_string(
                    fields.Datetime.from_string(b.date_start) + timedelta(minutes=b.time))

    def launch_battle(self):
        for b in self:
            if len(b.colony1) == 1 and len(b.colony2) == 1 and len(b.spaceship1_list) > 0 and b.state == '1':

                b.date_start = fields.Datetime.now()
                b.progress = 0
                for s in b.spaceship1_list:
                    spaceship_available = \
                        b.spaceship1_available.filtered(lambda s_a: s_a.spaceship_id.id == s.spaceship_id.id)[0]
                    spaceship_available.qty -= s.qty
                b.state = '2'

    def back(self):
        for b in self:
            if b.state == '2':
                b.state = '1'

    # In each round, all participating units(defenses+ships) randomly choose a target enemy unit.
    #
    # For each shooting unit:
    #
    #     If the Weaponry of the shooting unit is less than 1% of the Shielding of the target unit, the shot is bounced, and the target unit does not lose anything (i.e. shot is wasted).
    #     Else, if the weaponry is lower than the Shielding, then the shield absorbs the shot, and the unit does not lose Hull Plating: S = S - W.
    #     Else, the weaponry is sufficiently strong, i.e. W > S. Then the shield only absorbs part of the shoot and the rest is dealt to the hull: H = H - (W - S) and S = 0.
    #     If the Hull of the target ship is less than 70% of the initial Hull (H_i) of the ship (initial of the combat), then the ship has a probability of 1 - H/H_i of exploding. If it explodes, the hull is set to zero: H = 0. (but it can still be shot by the other units on this round, because they already target it.)
    #     Finally, if the shooting unit has rapid fire (with value r) against the target unit, it has a chance of (r-1)/r of choosing another target at random, and repeating the above steps for that new target.

    def execute_battle(self):
        for b in self:
            result = b.simulate_battle()

    def simulate_battle(self):
            b = self
            winner = False
            draft = False
            spaceships1 = b.spaceship1_list.mapped(lambda s: [s.spaceship_id.read(['id','damage','armor','capacity'])] * s.qty)
            spaceships1 = [spaceship for sublist in spaceships1 for spaceship in sublist]

            spaceships2 = b.colony2.spaceships.mapped(lambda s: [s.spaceship_id.read(['id','damage','armor','capacity'])] * s.qty)
            spaceships2 = [spaceship for sublist in spaceships2 for spaceship in sublist]

            for i in range(0, 6):  # 6 rondes com a màxim
                # Attack
                if len(spaceships1) > 0 and len(spaceships2) > 0:
                    print("ROUND",i,spaceships1, spaceships2)
                    for attacker in spaceships1:
                        target = random.choice(spaceships2)
                        if attacker['damage'] > target['armor'] / 100 or random.random() > 0.90:  # Bounce
                            target['armor'] -= random.random() * attacker['damage']

                    # Defense
                    for defender in spaceships2:
                        target = random.choice(spaceships1)
                        if defender['damage'] > target['armor'] / 100 or random.random() > 0.90:  # Bounce
                            target['armor'] -= random.random() * defender['damage']

                    spaceships1 = list(filter(lambda s: s['armor'] > 0, spaceships1))
                    spaceships2 = list(filter(lambda s: s['armor'] > 0, spaceships2))
            if len(spaceships1) == 0 and len(spaceships2) > 0:
                winner = b.player2.id
            if len(spaceships1) > 0 and len(spaceships2) == 0:
                winner = b.player1.id
            if len(spaceships1) > 0 and len(spaceships2) > 0:
                draft = True

            return {"winner": winner, "draft": draft}


class battle_spaceship_rel(models.Model):
    _name = 'expanse.battle_spaceship_rel'
    _description = 'battle_spaceship_rel'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.spaceship')
    battle_id = fields.Many2one('expanse.battle')
    qty = fields.Integer()

class battle_spaceship_rel_wizard(models.TransientModel):
    _name = 'expanse.battle_spaceship_rel_wizard'
    _description = 'battle_spaceship_rel_wizard'

    name = fields.Char(related="spaceship_id.name")
    spaceship_id = fields.Many2one('expanse.spaceship')
    battle_id = fields.Many2one('expanse.battle_wizard')
    qty = fields.Integer()

class battle_wizard(models.TransientModel):
    _name = 'expanse.battle_wizard'
    _description = 'Battle wizard'

    def _default_player1(self):
        return self.env['res.partner'].browse(self._context.get('active_id'))  # El context conté, entre altre coses,

    name = fields.Char()
    date_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    date_end = fields.Datetime(compute='_get_time')  # Calcul de dates
    time = fields.Float(compute='_get_time')
    distance = fields.Float(compute='_get_time')
    state = fields.Selection([('1', 'Player1'), ('2', 'Player2'), ('3', 'Resume')], default='1')
    player1 = fields.Many2one('res.partner', default=_default_player1)
    player1_resume = fields.Many2one('res.partner', related='player1')
    player2 = fields.Many2one('res.partner')
    player2_resume = fields.Many2one('res.partner', related='player2')
    colony1 = fields.Many2one('expanse.colony')
    colony2 = fields.Many2one('expanse.colony')
    spaceship1_list = fields.One2many('expanse.battle_spaceship_rel_wizard', 'battle_id')
    spaceship1_available = fields.Many2many('expanse.colony_spaceship_rel', compute='_get_spaceships_available')
    total_power = fields.Float()  # ORM Mapped

    @api.onchange('player1')
    def onchange_player1(self):
        self.name = self.player1.name
        return {
            'domain': {
                'colony1': [('id', 'in', self.player1.colonies.ids)],
                'player2': [('id', '!=', self.player1.id)],
            }
        }

    @api.onchange('player2')
    def onchange_player2(self):
        return {
            'domain': {
                'colony2': [('id', 'in', self.player2.colonies.ids)],
                'player1': [('id', '!=', self.player2.id)],
            }
        }

    @api.depends('colony1')
    def _get_spaceships_available(self):
        for b in self:
            b.spaceship1_available = b.colony1.spaceships.ids

    @api.depends('spaceship1_list', 'colony2', 'colony1')
    def _get_time(self):
        for b in self:
            b.time = 0
            b.distance = 0
            b.date_end = fields.Datetime.now()
            if len(b.colony1) > 0 and len(b.colony2) > 0 and len(b.spaceship1_list) > 0 and len(
                    b.spaceship1_list.spaceship_id) > 0:
                b.distance = b.colony1.planet.distance(b.colony2.planet)
                min_speed = b.spaceship1_list.spaceship_id.sorted(lambda s: s.speed).mapped('speed')[0]
                b.time = b.distance / min_speed
                b.date_end = fields.Datetime.to_string(
                    fields.Datetime.from_string(b.date_start) + timedelta(minutes=b.time))

    def  action_previous(self):
        if self.state == '2':
            self.state = '1'
        elif self.state == '3':
            self.state = '2'
        return {
            'name': 'Create Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'expanse.battle_wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id
        }

    def action_next(self):
        if self.state == '1':
            self.state = '2'
        elif self.state == '2':
            if len(self.player2) < 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Player2 has to be choosed',
                        'type': 'danger',  # types: success,warning,danger,info
                        'sticky': False,
                    }
                }
            else:
                self.state = '3'
        return {
            'name': 'Create Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'expanse.battle_wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': dict(self._context, player1_context=self.player1.id),

        }

    def create_battle(self):
        new_battle = self.env['expanse.battle'].create({
            'name': self.name,
            'player1': self.player1.id,
            'player2': self.player2.id,
            'colony1': self.colony1.id,
            'colony2': self.colony2.id,
            'state': '1',
            'date_start': self.date_start,
        })
        for s in self.spaceship1_list:
            self.env['expanse.battle_spaceship_rel'].create({
            'spaceship_id' : s.spaceship_id.id,
            'battle_id' : new_battle.id,
            'qty' : s.qty,
            })
        return  {
            'name': 'Created Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'expanse.battle',
            'view_mode': 'form',
            'target': 'current',
            'res_id': new_battle.id,

        }