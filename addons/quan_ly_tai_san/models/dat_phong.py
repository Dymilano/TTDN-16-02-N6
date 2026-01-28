# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DatPhong(models.Model):
    _name = 'dat_phong'
    _description = 'Đặt phòng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(string='Tiêu đề', required=True)
    tai_san_id = fields.Many2one('tai_san', string='Tài sản', required=True, ondelete='cascade')
    room_id = fields.Many2one('tai_san.location', string='Phòng', domain=[('location_type', '=', 'room')], required=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string='Người đặt', required=True)
    start_datetime = fields.Datetime(string='Thời gian bắt đầu', required=True, default=fields.Datetime.now)
    end_datetime = fields.Datetime(string='Thời gian kết thúc', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('in_progress', 'Đang sử dụng'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    ghi_chu = fields.Text(string='Ghi chú')

    @api.constrains('start_datetime', 'end_datetime')
    def _check_datetime(self):
        for rec in self:
            if rec.start_datetime >= rec.end_datetime:
                raise ValidationError(_('Thời gian kết thúc phải sau thời gian bắt đầu!'))
            
            # Check for overlapping bookings for the same room
            overlapping = self.search([
                ('room_id', '=', rec.room_id.id),
                ('id', '!=', rec.id),
                ('state', 'not in', ['cancelled', 'done']),
                ('start_datetime', '<', rec.end_datetime),
                ('end_datetime', '>', rec.start_datetime)
            ])
            if overlapping:
                raise ValidationError(_('Phòng này đã được đặt trong khoảng thời gian này!'))

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
