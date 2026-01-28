from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Email address for automatic notifications
ADMIN_EMAIL = 'nguyenduymilano@gmail.com'

class MuaSamTaiSan(models.Model):
    _name = 'mua_sam_tai_san'
    _description = 'Mua sắm tài sản'
    _order = 'ngay_mua desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    nha_cung_cap_id = fields.Many2one('res.partner', string='Nhà cung cấp', required=True)
    ngay_mua = fields.Date(string='Ngày mua', default=fields.Date.context_today, required=True)
    nguoi_mua_id = fields.Many2one('res.users', string='Người mua', default=lambda self: self.env.user)
    
    line_ids = fields.One2many('mua_sam_tai_san.line', 'mua_sam_id', string='Chi tiết')
    total_amount = fields.Float(string='Tổng tiền', compute='_compute_total', store=True)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã duyệt'),
        ('received', 'Đã nhận hàng'),
        ('cancelled', 'Hủy')
    ], string='Trạng thái', default='draft')
    
    ghi_chu = fields.Text(string='Ghi chú')

    @api.depends('line_ids.thanh_tien')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('thanh_tien'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('mua.sam.tai.san') or _('New')
        return super(MuaSamTaiSan, self).create(vals)

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec._send_purchase_email('approved')

    def action_receive(self):
        # Create Assets
        TaiSan = self.env['tai_san']
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_('Không có tài sản nào để nhận.'))
            
            for line in rec.line_ids:
                for i in range(int(line.so_luong)):
                    # Generate asset code? Or let user set it manually later?
                    # For now, auto-generate temporary code
                    asset_code = f"{rec.name}-{line.id}-{i+1}"
                    
                    TaiSan.create({
                        'ma_tai_san': asset_code,
                        'ten_tai_san': line.ten_tai_san,
                        'ngay_mua_ts': rec.ngay_mua,
                        'gia_tri_ban_dau': line.don_gia,
                        'gia_tri_hien_tai': line.don_gia,
                        'danh_muc_ts_id': line.danh_muc_id.id,
                        'don_vi_tinh': line.don_vi_tinh,
                        'ghi_chu': f"Mua từ phiếu {rec.name}",
                        'nha_cung_cap_id': rec.nha_cung_cap_id.id if rec.nha_cung_cap_id else False,
                        # Default depreciation settings could be fetched from category if implemented
                        'pp_khau_hao': 'none',
                        'trang_thai_thanh_ly': 'chua_phan_bo'
                    })
            rec.state = 'received'
            rec._send_purchase_email('received')

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec._send_purchase_email('cancelled')
    
    def _send_purchase_email(self, email_type):
        """Gửi email thông báo về mua sắm tài sản"""
        self.ensure_one()
        try:
            template_xmlid_map = {
                'approved': 'quan_ly_tai_san.email_template_purchase_approved',
                'received': 'quan_ly_tai_san.email_template_purchase_received',
                'cancelled': 'quan_ly_tai_san.email_template_purchase_cancelled',
            }
            template_xmlid = template_xmlid_map.get(email_type)
            if not template_xmlid:
                _logger.warning("Unknown email type: %s", email_type)
                return
            
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.with_context(email_to=ADMIN_EMAIL).send_mail(self.id, force_send=True)
                if self.nguoi_mua_id and self.nguoi_mua_id.email:
                    template.send_mail(self.id, force_send=True)
                _logger.info("Sent %s email for purchase %s", email_type, self.name)
        except Exception as e:
            _logger.error("Error sending purchase email (%s): %s", email_type, str(e))

class MuaSamTaiSanLine(models.Model):
    _name = 'mua_sam_tai_san.line'
    _description = 'Chi tiết mua sắm'

    mua_sam_id = fields.Many2one('mua_sam_tai_san', string='Phiếu mua sắm', ondelete='cascade')
    ten_tai_san = fields.Char(string='Tên tài sản/Thiết bị', required=True)
    danh_muc_id = fields.Many2one('danh_muc_tai_san', string='Loại tài sản', required=True)
    don_vi_tinh = fields.Char(string='ĐVT', default='Cái')
    so_luong = fields.Float(string='Số lượng', default=1.0, required=True)
    don_gia = fields.Float(string='Đơn giá', required=True)
    thanh_tien = fields.Float(string='Thành tiền', compute='_compute_thanh_tien', store=True)

    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for line in self:
            line.thanh_tien = line.so_luong * line.don_gia
