# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class WizardExtendBooking(models.TransientModel):
    _name = 'wizard.extend.booking'
    _description = 'Wizard gia hạn booking'

    booking_id = fields.Many2one('dat_phong_hop', string='Booking', required=True)
    new_end_datetime = fields.Datetime(string='Thời gian kết thúc mới', required=True)
    max_end_time = fields.Datetime(string='Thời gian kết thúc tối đa', 
                                   help='Thời gian tối đa có thể gia hạn (do có booking sau)')
    ly_do_gia_han = fields.Text(string='Lý do gia hạn')
    
    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.new_end_datetime = self.booking_id.end_datetime
    
    def action_extend(self):
        """Gia hạn booking"""
        if not self.booking_id:
            raise ValidationError(_('Vui lòng chọn booking!'))
        
        if self.new_end_datetime <= self.booking_id.start_datetime:
            raise ValidationError(_('Thời gian kết thúc mới phải sau thời gian bắt đầu!'))
        
        if self.max_end_time and self.new_end_datetime > self.max_end_time:
            raise ValidationError(_(f'Không thể gia hạn quá {self.max_end_time.strftime("%d/%m/%Y %H:%M")}!'))
        
        # Kiểm tra trùng lịch với booking khác
        overlapping = self.env['dat_phong_hop'].search([
            ('phong_hop_id', '=', self.booking_id.phong_hop_id.id),
            ('id', '!=', self.booking_id.id),
            ('state', 'not in', ['cancelled', 'rejected', 'no_show', 'done']),
            ('start_datetime', '<', self.new_end_datetime),
            ('end_datetime', '>', self.booking_id.start_datetime)
        ])
        
        if overlapping:
            raise ValidationError(_('Không thể gia hạn vì có booking khác trong khoảng thời gian này!'))
        
        # Cập nhật thời gian kết thúc
        self.booking_id.write({
            'end_datetime': self.new_end_datetime,
            'ghi_chu': (self.booking_id.ghi_chu or '') + f'\n[Gia hạn] {self.ly_do_gia_han or ""}'
        })
        
        return {'type': 'ir.actions.act_window_close'}
