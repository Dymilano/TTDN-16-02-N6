# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WizardMultiRoomBooking(models.TransientModel):
    _name = 'wizard.multi.room.booking'
    _description = 'Wizard đặt nhiều phòng cho một sự kiện'

    parent_booking_id = fields.Many2one('dat_phong_hop', string='Booking gốc', required=True)
    name = fields.Char(string='Tiêu đề cuộc họp', required=True)
    start_datetime = fields.Datetime(string='Thời gian bắt đầu', required=True)
    end_datetime = fields.Datetime(string='Thời gian kết thúc', required=True)
    host_id = fields.Many2one('nhan_vien', string='Người chủ trì', required=True)
    muc_dich = fields.Text(string='Mục đích cuộc họp', required=True)
    
    phong_hop_ids = fields.Many2many('phong_hop', string='Chọn các phòng', required=True)
    
    def action_create_bookings(self):
        """Tạo các booking cho nhiều phòng"""
        if not self.phong_hop_ids:
            raise ValidationError(_('Vui lòng chọn ít nhất một phòng!'))
        
        created_bookings = self.env['dat_phong_hop']
        
        for room in self.phong_hop_ids:
            # Kiểm tra trùng lịch
            overlapping = self.env['dat_phong_hop'].search([
                ('phong_hop_id', '=', room.id),
                ('state', 'not in', ['cancelled', 'rejected', 'no_show', 'done']),
                ('start_datetime', '<', self.end_datetime),
                ('end_datetime', '>', self.start_datetime)
            ])
            
            if overlapping:
                raise ValidationError(_(f'Phòng {room.ten_phong or room.ma_phong} đã được đặt trong khoảng thời gian này!'))
            
            # Tạo booking
            booking_vals = {
                'name': self.name,
                'phong_hop_id': room.id,
                'start_datetime': self.start_datetime,
                'end_datetime': self.end_datetime,
                'host_id': self.host_id.id,
                'muc_dich': self.muc_dich,
                'is_multi_room': True,
                'state': 'draft'
            }
            new_booking = self.env['dat_phong_hop'].create(booking_vals)
            created_bookings |= new_booking
        
        # Liên kết các booking với nhau
        if created_bookings:
            for booking in created_bookings:
                related_ids = created_bookings.filtered(lambda b: b.id != booking.id)
                booking.write({'related_booking_ids': [(6, 0, related_ids.ids)]})
            
            # Cập nhật booking gốc
            if self.parent_booking_id:
                self.parent_booking_id.write({
                    'is_multi_room': True,
                    'related_booking_ids': [(6, 0, created_bookings.ids)]
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Các booking đã tạo',
            'res_model': 'dat_phong_hop',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_bookings.ids)],
            'target': 'current'
        }
