# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class PhongHop(models.Model):
    _name = 'phong_hop'
    _description = 'Danh mục phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ma_phong'

    ma_phong = fields.Char(string='Mã phòng', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    ten_phong = fields.Char(string='Tên phòng', required=True)
    
    # Thông tin cơ bản
    suc_chua = fields.Integer(string='Sức chứa', required=True, default=10)
    location_id = fields.Many2one('tai_san.location', string='Địa điểm', domain=[('location_type', 'in', ['site', 'building', 'floor', 'room'])], required=True)
    
    # Loại phòng
    loai_phong = fields.Selection([
        ('small', 'Nhỏ (< 10 người)'),
        ('medium', 'Vừa (10-30 người)'),
        ('large', 'Lớn (30-50 người)'),
        ('training', 'Phòng đào tạo'),
        ('board', 'Phòng họp Ban giám đốc'),
        ('conference', 'Hội trường'),
        ('other', 'Khác')
    ], string='Loại phòng', required=True, default='medium')
    
    # Tiện ích
    co_may_chieu = fields.Boolean(string='Máy chiếu', default=False)
    co_tv = fields.Boolean(string='TV/Màn hình', default=False)
    co_vc_device = fields.Boolean(string='Thiết bị Video Conference', default=False)
    co_bang_trang = fields.Boolean(string='Bảng trắng', default=False)
    co_micro = fields.Boolean(string='Micro', default=False)
    co_camera = fields.Boolean(string='Camera', default=False)
    co_wifi = fields.Boolean(string='WiFi', default=True)
    co_aircon = fields.Boolean(string='Điều hòa', default=True)
    tien_ich_khac = fields.Text(string='Tiện ích khác')
    
    # Khung giờ hoạt động
    gio_bat_dau = fields.Float(string='Giờ bắt đầu', default=8.0, help='Giờ bắt đầu hoạt động (VD: 8.0 = 8:00)')
    gio_ket_thuc = fields.Float(string='Giờ kết thúc', default=18.0, help='Giờ kết thúc hoạt động (VD: 18.0 = 18:00)')
    hoat_dong_ca_ngay = fields.Boolean(string='Hoạt động cả ngày', default=False)
    
    # Quy định đặt phòng
    thoi_luong_toi_thieu = fields.Integer(string='Thời lượng tối thiểu (phút)', default=30)
    thoi_luong_toi_da = fields.Integer(string='Thời lượng tối đa (phút)', default=480)
    lead_time = fields.Integer(string='Lead time (ngày)', default=30, help='Số ngày tối đa có thể đặt trước')
    buffer_time_before = fields.Integer(string='Buffer trước (phút)', default=15, help='Thời gian buffer trước cuộc họp để dọn phòng')
    buffer_time_after = fields.Integer(string='Buffer sau (phút)', default=15, help='Thời gian buffer sau cuộc họp để dọn phòng')
    
    # Trạng thái
    state = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('maintenance', 'Bảo trì'),
        ('out_of_service', 'Ngừng hoạt động')
    ], string='Trạng thái', default='available', required=True, tracking=True)
    
    # Liên kết với tài sản
    tai_san_id = fields.Many2one('tai_san', string='Tài sản liên kết', help='Phòng họp được coi là một tài sản')
    tai_san_trong_phong_ids = fields.Many2many('tai_san', 'phong_hop_tai_san_rel', 'phong_hop_id', 'tai_san_id', 
                                               string='Tài sản trong phòng')
    
    # Thông tin khác
    mo_ta = fields.Text(string='Mô tả')
    hinh_anh = fields.Image(string='Hình ảnh', max_width=800, max_height=600)
    
    # Quan hệ
    booking_ids = fields.One2many('dat_phong_hop', 'phong_hop_id', string='Lịch đặt phòng')
    bao_tri_ids = fields.One2many('bao_tri_phong_hop', 'phong_hop_id', string='Lịch sử bảo trì')
    tai_san_phong_hop_ids = fields.One2many('tai_san_phong_hop', 'phong_hop_id', string='Tài sản phòng họp')
    
    # Tính toán
    ty_le_su_dung = fields.Float(string='Tỷ lệ sử dụng (%)', compute='_compute_ty_le_su_dung', store=True)
    so_luong_booking = fields.Integer(string='Số lượng booking', compute='_compute_booking_stats', store=True)
    so_luong_no_show = fields.Integer(string='Số lượng no-show', compute='_compute_booking_stats', store=True)
    
    _sql_constraints = [
        ('ma_phong_unique', 'unique(ma_phong)', 'Mã phòng đã tồn tại!'),
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_phong', _('New')) == _('New'):
            vals['ma_phong'] = self.env['ir.sequence'].next_by_code('phong.hop') or _('New')
        record = super(PhongHop, self).create(vals)
        # Gửi bus notification để dashboard cập nhật real-time
        self._notify_dashboard_update()
        return record
    
    def write(self, vals):
        result = super(PhongHop, self).write(vals)
        # Gửi bus notification khi có thay đổi quan trọng
        if any(key in vals for key in ['state', 'location_id', 'suc_chua']):
            self._notify_dashboard_update()
        return result
    
    def _notify_dashboard_update(self):
        """Gửi bus notification để dashboard cập nhật real-time"""
        try:
            self.env['bus.bus']._sendone(
                'dashboard_phong_hop',
                'dashboard_phong_hop/update',
                {
                    'message': 'Dashboard update required',
                    'timestamp': fields.Datetime.now().isoformat()
                }
            )
        except Exception as e:
            _logger.warning("Error sending dashboard update notification: %s", str(e))
    
    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.start_datetime', 'booking_ids.end_datetime')
    def _compute_ty_le_su_dung(self):
        for rec in self:
            # Tính tỷ lệ sử dụng trong tháng hiện tại
            today = fields.Date.today()
            from dateutil.relativedelta import relativedelta
            month_start = today.replace(day=1)
            month_end = (today + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
            
            bookings = rec.booking_ids.filtered(lambda b: 
                b.start_datetime and b.end_datetime and
                b.start_datetime.date() >= month_start and 
                b.start_datetime.date() <= month_end and
                b.state in ['confirmed', 'checked_in', 'in_progress', 'done'])
            
            total_minutes = 0
            for booking in bookings:
                try:
                    duration = (booking.end_datetime - booking.start_datetime).total_seconds() / 60
                    total_minutes += duration
                except:
                    continue
            
            # Tính tổng số phút có thể sử dụng trong tháng
            days_in_month = month_end.day
            working_hours = rec.gio_ket_thuc - rec.gio_bat_dau if not rec.hoat_dong_ca_ngay else 24
            total_available_minutes = days_in_month * working_hours * 60
            
            if total_available_minutes > 0:
                rec.ty_le_su_dung = min((total_minutes / total_available_minutes) * 100, 100.0)
            else:
                rec.ty_le_su_dung = 0.0
    
    @api.depends('booking_ids', 'booking_ids.state')
    def _compute_booking_stats(self):
        for rec in self:
            rec.so_luong_booking = len(rec.booking_ids.filtered(lambda b: b.state != 'cancelled'))
            rec.so_luong_no_show = len(rec.booking_ids.filtered(lambda b: b.state == 'no_show'))
    
    @api.constrains('thoi_luong_toi_thieu', 'thoi_luong_toi_da')
    def _check_thoi_luong(self):
        for rec in self:
            if rec.thoi_luong_toi_thieu > rec.thoi_luong_toi_da:
                raise ValidationError(_('Thời lượng tối thiểu không thể lớn hơn thời lượng tối đa!'))
    
    @api.constrains('gio_bat_dau', 'gio_ket_thuc')
    def _check_gio_hoat_dong(self):
        for rec in self:
            if not rec.hoat_dong_ca_ngay:
                if rec.gio_bat_dau >= rec.gio_ket_thuc:
                    raise ValidationError(_('Giờ bắt đầu phải trước giờ kết thúc!'))
    
    def action_schedule_maintenance(self):
        """Tạo phiếu bảo trì cho phòng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lên lịch bảo trì',
            'res_model': 'bao_tri_phong_hop',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.id,
                'default_state': 'draft'
            }
        }
    
    def action_add_assets_to_room(self):
        """Mở wizard để thêm tài sản vào phòng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thêm tài sản vào phòng',
            'res_model': 'wizard.add.assets.to.room',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.id,
            }
        }
    
    def action_view_assets_from_module(self):
        """Mở danh sách tài sản từ module quản lý tài sản để gắn vào phòng"""
        self.ensure_one()
        # Lấy danh sách tài sản đã có trong phòng để loại trừ
        existing_asset_ids = self.tai_san_phong_hop_ids.mapped('tai_san_id').ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chọn tài sản từ danh sách',
            'res_model': 'tai_san',
            'view_mode': 'tree,form',
            'domain': [
                ('is_shared_asset', '=', True),
                ('id', 'not in', existing_asset_ids)
            ],
            'context': {
                'default_is_shared_asset': True,
                'create': False,
                'select_multi': True,
                'phong_hop_id': self.id,
            },
            'target': 'current',
        }
    
    def action_add_selected_assets(self, asset_ids):
        """Thêm các tài sản đã chọn vào phòng"""
        self.ensure_one()
        if not asset_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        # Tạo các bản ghi tai_san_phong_hop
        created_count = 0
        for asset_id in asset_ids:
            existing = self.env['tai_san_phong_hop'].search([
                ('phong_hop_id', '=', self.id),
                ('tai_san_id', '=', asset_id)
            ])
            if not existing:
                self.env['tai_san_phong_hop'].create({
                    'phong_hop_id': self.id,
                    'tai_san_id': asset_id,
                })
                created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã thêm %s tài sản vào phòng %s') % (created_count, self.ten_phong),
                'type': 'success',
                'sticky': False,
            }
        }
