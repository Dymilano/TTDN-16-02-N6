# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class BaoTriPhongHop(models.Model):
    _name = 'bao_tri_phong_hop'
    _description = 'Bảo trì phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ngay_bao_tri desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    phong_hop_id = fields.Many2one('phong_hop', string='Phòng họp', required=True, ondelete='restrict')
    
    loai_bao_tri = fields.Selection([
        ('bao_tri_dinh_ky', 'Bảo trì định kỳ'),
        ('sua_chua', 'Sửa chữa'),
        ('nang_cap', 'Nâng cấp'),
        ('ve_sinh', 'Vệ sinh sâu'),
        ('kiem_tra', 'Kiểm tra thiết bị')
    ], string='Loại bảo trì', required=True, default='bao_tri_dinh_ky')
    
    ngay_bao_tri = fields.Date(string='Ngày thực hiện', default=fields.Date.context_today, required=True)
    ngay_hoan_thanh = fields.Date(string='Ngày hoàn thành')
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('scheduled', 'Đã lên lịch'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    
    # Liên kết với tài sản trong phòng
    tai_san_bao_tri_ids = fields.Many2many('tai_san', 'bao_tri_phong_tai_san_rel', 'bao_tri_id', 'tai_san_id',
                                           string='Tài sản cần bảo trì')
    
    nha_cung_cap_id = fields.Many2one('res.partner', string='Nhà cung cấp/Sửa chữa')
    mo_ta = fields.Text(string="Mô tả")
    ket_qua = fields.Text(string="Kết quả")
    
    # Chi phí
    chi_phi_nhan_cong = fields.Float(string='Chi phí nhân công')
    chi_phi_vat_tu = fields.Float(string='Chi phí vật tư')
    chi_phi_thue_ngoai = fields.Float(string='Chi phí thuê ngoài')
    tong_chi_phi = fields.Float(string='Tổng chi phí', compute='_compute_tong_chi_phi', store=True)
    
    ghi_chu = fields.Text(string='Ghi chú')
    
    # Computed field để hiển thị trạng thái phòng (cho decoration)
    phong_hop_state = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('maintenance', 'Bảo trì'),
        ('out_of_service', 'Ngừng hoạt động')
    ], string='Trạng thái phòng', compute='_compute_phong_hop_state', store=False)
    
    # Lịch sử bảo trì phòng (tất cả các phiếu bảo trì của phòng này)
    lich_su_bao_tri_phong_ids = fields.One2many('bao_tri_phong_hop', 'phong_hop_id', 
                                                 string='Lịch sử bảo trì phòng',
                                                 compute='_compute_lich_su_bao_tri_phong', store=False)
    
    @api.depends('phong_hop_id', 'phong_hop_id.state')
    def _compute_phong_hop_state(self):
        """Tính toán trạng thái phòng để hiển thị decoration"""
        for rec in self:
            rec.phong_hop_state = rec.phong_hop_id.state if rec.phong_hop_id else False
    
    @api.depends('phong_hop_id')
    def _compute_lich_su_bao_tri_phong(self):
        """Tính toán lịch sử bảo trì của phòng"""
        for rec in self:
            try:
                if rec.phong_hop_id:
                    rec.lich_su_bao_tri_phong_ids = self.env['bao_tri_phong_hop'].search([
                        ('phong_hop_id', '=', rec.phong_hop_id.id),
                        ('id', '!=', rec.id)  # Loại trừ phiếu hiện tại
                    ], order='ngay_bao_tri desc')
                else:
                    rec.lich_su_bao_tri_phong_ids = self.env['bao_tri_phong_hop']
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning("Error computing lich_su_bao_tri_phong for bao_tri_phong_hop %s: %s", rec.id, str(e))
                rec.lich_su_bao_tri_phong_ids = self.env['bao_tri_phong_hop']
    
    @api.onchange('phong_hop_id')
    def _onchange_phong_hop_id(self):
        """Force compute khi thay đổi phòng"""
        self._compute_lich_su_bao_tri_phong()
    
    @api.depends('chi_phi_nhan_cong', 'chi_phi_vat_tu', 'chi_phi_thue_ngoai')
    def _compute_tong_chi_phi(self):
        for rec in self:
            rec.tong_chi_phi = rec.chi_phi_nhan_cong + rec.chi_phi_vat_tu + rec.chi_phi_thue_ngoai
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('bao.tri.phong.hop') or _('New')
        record = super(BaoTriPhongHop, self).create(vals)
        # Gửi bus notification để dashboard cập nhật real-time
        self._notify_dashboard_update()
        return record
    
    def write(self, vals):
        result = super(BaoTriPhongHop, self).write(vals)
        # Gửi bus notification khi có thay đổi quan trọng
        if any(key in vals for key in ['state', 'phong_hop_id', 'ngay_bao_tri', 'ngay_hoan_thanh']):
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
    
    def action_schedule(self):
        """Lên lịch bảo trì"""
        for rec in self:
            rec.write({'state': 'scheduled'})
            # Tự động chuyển phòng sang trạng thái bảo trì
            if rec.phong_hop_id:
                rec.phong_hop_id.write({'state': 'maintenance'})
                # Hủy các booking trong thời gian bảo trì
                bookings = self.env['dat_phong_hop'].search([
                    ('phong_hop_id', '=', rec.phong_hop_id.id),
                    ('start_datetime', '>=', fields.Datetime.combine(rec.ngay_bao_tri, datetime.min.time())),
                    ('state', 'in', ['draft', 'pending_approval', 'approved', 'confirmed'])
                ])
                for booking in bookings:
                    booking.write({
                        'state': 'cancelled',
                        'ly_do_huy': f'Phòng bảo trì từ {rec.ngay_bao_tri}'
                    })
    
    def action_start(self):
        """Bắt đầu bảo trì"""
        for rec in self:
            rec.write({'state': 'in_progress'})
    
    def action_done(self):
        """Hoàn thành bảo trì"""
        for rec in self:
            rec.write({
                'state': 'done',
                'ngay_hoan_thanh': fields.Date.today()
            })
            # Khôi phục phòng về trạng thái sẵn sàng
            if rec.phong_hop_id:
                rec.phong_hop_id.write({'state': 'available'})
    
    def action_cancel(self):
        """Hủy bảo trì"""
        for rec in self:
            rec.write({'state': 'cancelled'})
            # Khôi phục phòng nếu đang bảo trì
            if rec.phong_hop_id.state == 'maintenance':
                rec.phong_hop_id.write({'state': 'available'})
