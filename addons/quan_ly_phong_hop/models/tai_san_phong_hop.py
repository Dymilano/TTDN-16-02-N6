# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TaiSanPhongHop(models.Model):
    _name = 'tai_san_phong_hop'
    _description = 'Tài sản phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    phong_hop_id = fields.Many2one('phong_hop', string='Phòng họp', required=True, ondelete='cascade')
    tai_san_id = fields.Many2one('tai_san', string='Tài sản', required=True, ondelete='restrict')
    
    # Thông tin kỹ thuật
    nha_san_xuat = fields.Char(string='Nhà sản xuất', related='tai_san_id.manufacturer', store=True)
    model = fields.Char(string='Model', related='tai_san_id.model_number', store=True)
    serial_number = fields.Char(string='Số serial', related='tai_san_id.serial_number', store=True)
    
    # Người chịu trách nhiệm
    nguoi_chiu_trach_nhiem_id = fields.Many2one('nhan_vien', string='Người chịu trách nhiệm', related='tai_san_id.custodian_id', store=True)
    phong_ban_quan_ly_id = fields.Many2one('phong_ban', string='Phòng ban quản lý', related='tai_san_id.department_id', store=True)
    
    # Giấy tờ và ghi chú
    giay_to = fields.Binary(string='Giấy tờ', related='tai_san_id.giay_to_tai_san')
    ghi_chu = fields.Char(string='Ghi chú', related='tai_san_id.ghi_chu')
    
    # Trạng thái - đồng bộ với tài sản nhưng có thể override
    trang_thai_tai_san = fields.Selection([
        ('new', 'Mới'),
        ('in_use', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì'),
        ('damaged', 'Hư hỏng'),
        ('lost', 'Mất'),
        ('liquidation', 'Thanh lý'),
        ('sold', 'Đã bán'),
        ('disposed', 'Đã hủy')
    ], string='Trạng thái tài sản', related='tai_san_id.state', store=True, readonly=True)
    
    trang_thai = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('in_use', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì'),
        ('damaged', 'Hư hỏng')
    ], string='Trạng thái trong phòng', default='available', 
       compute='_compute_trang_thai', store=True)
    
    @api.depends('trang_thai_tai_san')
    def _compute_trang_thai(self):
        """Đồng bộ trạng thái từ tài sản"""
        for rec in self:
            mapping = {
                'new': 'available',
                'in_use': 'in_use',
                'maintenance': 'maintenance',
                'damaged': 'damaged',
                'lost': 'damaged',
                'liquidation': 'damaged',
                'sold': 'damaged',
                'disposed': 'damaged'
            }
            rec.trang_thai = mapping.get(rec.trang_thai_tai_san, 'available')
    
    # Lịch sử - các quan hệ với module quan_ly_tai_san
    lich_su_bao_tri_ids = fields.One2many('bao_tri_tai_san', 'tai_san_id', string='Lịch sử bảo trì', 
                                          compute='_compute_lich_su', store=False)
    phieu_bao_tri_ids = fields.One2many('bao_tri_tai_san', 'tai_san_id', string='Phiếu bảo trì',
                                         compute='_compute_lich_su', store=False)
    lich_su_su_dung_ids = fields.One2many('phieu_su_dung.line', 'tai_san_id', string='Lịch sử sử dụng',
                                          compute='_compute_lich_su', store=False)
    phieu_mua_sam_ids = fields.Many2many('mua_sam_tai_san', string='Phiếu mua sắm',
                                         compute='_compute_lich_su', store=False)
    
    @api.depends('tai_san_id')
    def _compute_lich_su(self):
        """Tính toán các lịch sử liên quan đến tài sản"""
        for rec in self:
            try:
                if rec.tai_san_id:
                    # Lịch sử bảo trì (tất cả)
                    rec.lich_su_bao_tri_ids = self.env['bao_tri_tai_san'].search([
                        ('tai_san_id', '=', rec.tai_san_id.id)
                    ])
                    # Phiếu bảo trì (chỉ các phiếu)
                    rec.phieu_bao_tri_ids = rec.lich_su_bao_tri_ids
                    # Lịch sử sử dụng
                    rec.lich_su_su_dung_ids = self.env['phieu_su_dung.line'].search([
                        ('tai_san_id', '=', rec.tai_san_id.id)
                    ])
                    # Phiếu mua sắm (tìm qua ten_tai_san và ngay_mua_ts)
                    # Vì mua_sam_tai_san.line không có tai_san_id, ta tìm qua tên và ngày mua
                    phieu_mua_sam_records = self.env['mua_sam_tai_san']
                    if rec.tai_san_id.ten_tai_san and rec.tai_san_id.ngay_mua_ts:
                        mua_sam_lines = self.env['mua_sam_tai_san.line'].search([
                            ('ten_tai_san', '=', rec.tai_san_id.ten_tai_san)
                        ])
                        # Lọc thêm theo ngày mua nếu có
                        for line in mua_sam_lines:
                            if line.mua_sam_id.ngay_mua == rec.tai_san_id.ngay_mua_ts:
                                phieu_mua_sam_records |= line.mua_sam_id
                    rec.phieu_mua_sam_ids = phieu_mua_sam_records
                else:
                    rec.lich_su_bao_tri_ids = self.env['bao_tri_tai_san']
                    rec.phieu_bao_tri_ids = self.env['bao_tri_tai_san']
                    rec.lich_su_su_dung_ids = self.env['phieu_su_dung.line']
                    rec.phieu_mua_sam_ids = self.env['mua_sam_tai_san']
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning("Error computing lich_su for tai_san_phong_hop %s: %s", rec.id, str(e))
                rec.lich_su_bao_tri_ids = self.env['bao_tri_tai_san']
                rec.phieu_bao_tri_ids = self.env['bao_tri_tai_san']
                rec.lich_su_su_dung_ids = self.env['phieu_su_dung.line']
                rec.phieu_mua_sam_ids = self.env['mua_sam_tai_san']
    
    @api.onchange('tai_san_id')
    def _onchange_tai_san_id(self):
        """Force compute khi thay đổi tài sản"""
        self._compute_lich_su()
    
    _sql_constraints = [
        ('phong_tai_san_unique', 'unique(phong_hop_id, tai_san_id)', 'Tài sản này đã được gán cho phòng này!'),
    ]
    
    def action_add_asset_from_list(self):
        """Mở wizard để thêm tài sản từ danh sách tài sản"""
        self.ensure_one()
        # Lấy danh sách tài sản đã có trong phòng
        existing_asset_ids = self.phong_hop_id.tai_san_phong_hop_ids.mapped('tai_san_id').ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thêm tài sản vào phòng',
            'res_model': 'wizard.add.assets.to.room',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.phong_hop_id.id,
                'default_tai_san_ids': [(6, 0, [])],
            }
        }
    
    def action_view_asset(self):
        """Mở form view của tài sản trong module quản lý tài sản"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chi tiết tài sản',
            'res_model': 'tai_san',
            'res_id': self.tai_san_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_maintenance(self):
        """Xem lịch sử bảo trì của tài sản"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lịch sử bảo trì',
            'res_model': 'bao_tri_tai_san',
            'view_mode': 'tree,form',
            'domain': [('tai_san_id', '=', self.tai_san_id.id)],
            'target': 'current',
        }
    
    def action_create_maintenance(self):
        """Tạo phiếu bảo trì mới cho tài sản"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo phiếu bảo trì',
            'res_model': 'bao_tri_tai_san',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_tai_san_id': self.tai_san_id.id,
            }
        }
    
    def action_view_purchase(self):
        """Xem phiếu mua sắm liên quan đến tài sản"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Phiếu mua sắm',
            'res_model': 'mua_sam_tai_san',
            'view_mode': 'tree,form',
            'domain': [('tai_san_ids', 'in', [self.tai_san_id.id])],
            'target': 'current',
        }
    
    def action_view_usage(self):
        """Xem lịch sử sử dụng tài sản"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lịch sử sử dụng',
            'res_model': 'phieu_su_dung',
            'view_mode': 'tree,form',
            'domain': [('tai_san_id', '=', self.tai_san_id.id)],
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """Khi tạo tài sản phòng họp, tự động cập nhật location của tài sản"""
        record = super(TaiSanPhongHop, self).create(vals)
        if record.tai_san_id and record.phong_hop_id:
            # Cập nhật location của tài sản về phòng họp
            if record.phong_hop_id.location_id:
                record.tai_san_id.write({
                    'location_id': record.phong_hop_id.location_id.id
                })
            # Thêm vào danh sách tài sản trong phòng (many2many)
            record.phong_hop_id.write({
                'tai_san_trong_phong_ids': [(4, record.tai_san_id.id)]
            })
        # Gửi bus notification để dashboard cập nhật real-time
        self._notify_dashboard_update()
        return record
    
    def write(self, vals):
        """Khi cập nhật, đồng bộ location"""
        result = super(TaiSanPhongHop, self).write(vals)
        for rec in self:
            if rec.tai_san_id and rec.phong_hop_id and rec.phong_hop_id.location_id:
                rec.tai_san_id.write({
                    'location_id': rec.phong_hop_id.location_id.id
                })
        # Gửi bus notification khi có thay đổi quan trọng
        if any(key in vals for key in ['trang_thai', 'phong_hop_id', 'tai_san_id']):
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
        return result
    
    def unlink(self):
        """Khi xóa, cập nhật lại danh sách tài sản trong phòng"""
        phong_hop_ids = self.mapped('phong_hop_id')
        tai_san_ids = self.mapped('tai_san_id')
        result = super(TaiSanPhongHop, self).unlink()
        # Cập nhật lại danh sách tài sản trong phòng
        for phong in phong_hop_ids:
            phong.write({
                'tai_san_trong_phong_ids': [(3, tai_san_id) for tai_san_id in tai_san_ids.ids]
            })
        return result
