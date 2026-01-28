# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class WizardRejectBooking(models.TransientModel):
    _name = 'wizard.reject.booking'
    _description = 'Wizard từ chối booking'

    booking_id = fields.Many2one('dat_phong_hop', string='Booking', required=True)
    ly_do_tu_choi = fields.Text(string='Lý do từ chối', required=True)
    
    def action_reject(self):
        self.booking_id.write({
            'state': 'rejected',
            'ly_do_tu_choi': self.ly_do_tu_choi
        })
        return {'type': 'ir.actions.act_window_close'}
