# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class DichVuPhongHop(models.Model):
    _name = 'dich_vu_phong_hop'
    _description = 'Dịch vụ kèm theo phòng họp'

    booking_id = fields.Many2one('dat_phong_hop', string='Booking', required=True, ondelete='cascade')
    
    loai_dich_vu = fields.Selection([
        ('setup', 'Setup phòng'),
        ('catering', 'Catering/Tea-break'),
        ('it_support', 'IT Support'),
        ('housekeeping', 'Vệ sinh/Housekeeping'),
        ('equipment', 'Thiết bị mượn'),
        ('other', 'Khác')
    ], string='Loại dịch vụ', required=True)
    
    # Setup phòng
    layout_type = fields.Selection([
        ('u_shape', 'U-shape'),
        ('classroom', 'Classroom'),
        ('theater', 'Theater'),
        ('boardroom', 'Boardroom'),
        ('banquet', 'Banquet')
    ], string='Kiểu layout')
    so_ghe = fields.Integer(string='Số ghế')
    
    # Catering
    so_luong_nguoi = fields.Integer(string='Số lượng người')
    menu = fields.Text(string='Menu')
    thoi_diem_phuc_vu = fields.Datetime(string='Thời điểm phục vụ')
    
    # IT Support
    yeu_cau_hoi_online = fields.Boolean(string='Yêu cầu họp online', default=False)
    can_test_mic_cam = fields.Boolean(string='Cần test mic/camera', default=False)
    
    # Housekeeping
    don_truoc = fields.Boolean(string='Dọn trước', default=True)
    don_sau = fields.Boolean(string='Dọn sau', default=True)
    
    # Thiết bị mượn
    thiet_bi_muon_ids = fields.Many2many('tai_san', 'dich_vu_thiet_bi_rel', 'dich_vu_id', 'tai_san_id', 
                                         string='Thiết bị mượn',
                                         domain=[('is_shared_asset', '=', True)])
    
    # Chi phí
    chi_phi = fields.Float(string='Chi phí', default=0.0)
    
    # Mô tả
    mo_ta = fields.Text(string='Mô tả chi tiết')
    
    # Trạng thái
    state = fields.Selection([
        ('requested', 'Đã yêu cầu'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='requested')
