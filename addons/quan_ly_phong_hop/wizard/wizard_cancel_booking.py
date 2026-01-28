# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class WizardCancelBooking(models.TransientModel):
    _name = 'wizard.cancel.booking'
    _description = 'Wizard hủy booking'

    booking_id = fields.Many2one('dat_phong_hop', string='Booking', required=True)
    ly_do_huy = fields.Text(string='Lý do hủy', required=True)
    
    def action_cancel(self):
        self.booking_id.write({
            'state': 'cancelled',
            'ly_do_huy': self.ly_do_huy
        })
        return {'type': 'ir.actions.act_window_close'}
