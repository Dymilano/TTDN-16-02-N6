from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Email address for automatic notifications
ADMIN_EMAIL = 'nguyenduymilano@gmail.com'

class BaoTriTaiSan(models.Model):
    _name = 'bao_tri_tai_san'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Bảo trì tài sản'
    _order = 'ngay_bao_tri desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    tai_san_id = fields.Many2one('tai_san', string='Tài sản', required=True)
    loai_bao_tri = fields.Selection([
        ('bao_tri', 'Bảo trì định kỳ'),
        ('sua_chua', 'Sửa chữa'),
        ('bao_hanh', 'Bảo hành'),
        ('nang_cap', 'Nâng cấp')
    ], string='Loại bảo trì', required=True, default='bao_tri')
    
    ngay_bao_tri = fields.Date(string='Ngày thực hiện', default=fields.Date.context_today, required=True)
    ngay_hoan_thanh = fields.Date(string='Ngày hoàn thành')
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    
    nha_cung_cap_id = fields.Many2one('res.partner', string='Nhà cung cấp/Sửa chữa')
    mo_ta = fields.Text(string="Mô tả")
    ket_qua = fields.Text(string="Kết quả")

    # Costs
    chi_phi_nhan_cong = fields.Float(string='Chi phí nhân công')
    chi_phi_vat_tu = fields.Float(string='Chi phí vật tư')
    chi_phi_thue_ngoai = fields.Float(string='Chi phí thuê ngoài')
    tong_chi_phi = fields.Float(string='Tổng chi phí', compute='_compute_tong_chi_phi', store=True)
    
    # Downtime & Details
    thoi_gian_dung_may = fields.Float(string='Thời gian dừng máy (giờ)')
    nguyen_nhan = fields.Text(string='Nguyên nhân hư hỏng')
    linh_kien_thay_the = fields.Text(string='Linh kiện thay thế')
    
    @api.depends('chi_phi_nhan_cong', 'chi_phi_vat_tu', 'chi_phi_thue_ngoai')
    def _compute_tong_chi_phi(self):
        for rec in self:
            rec.tong_chi_phi = rec.chi_phi_nhan_cong + rec.chi_phi_vat_tu + rec.chi_phi_thue_ngoai

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('bao.tri.tai.san') or _('New')
        record = super(BaoTriTaiSan, self).create(vals)
        record._send_maintenance_email('created')
        return record
    
    def write(self, vals):
        old_states = {r.id: r.state for r in self}
        result = super(BaoTriTaiSan, self).write(vals)
        for rec in self:
            if 'state' in vals and old_states.get(rec.id) != rec.state:
                if rec.state == 'in_progress':
                    rec._send_maintenance_email('started')
                elif rec.state == 'done':
                    rec._send_maintenance_email('completed')
                elif rec.state == 'cancelled':
                    rec._send_maintenance_email('cancelled')
        return result
    
    def _send_maintenance_email(self, email_type):
        """Gửi email thông báo về bảo trì tài sản"""
        self.ensure_one()
        try:
            template_xmlid_map = {
                'created': 'quan_ly_tai_san.email_template_maintenance_created',
                'started': 'quan_ly_tai_san.email_template_maintenance_started',
                'completed': 'quan_ly_tai_san.email_template_maintenance_completed',
                'cancelled': 'quan_ly_tai_san.email_template_maintenance_cancelled',
            }
            template_xmlid = template_xmlid_map.get(email_type)
            if not template_xmlid:
                _logger.warning("Unknown email type: %s", email_type)
                return
            
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.with_context(email_to=ADMIN_EMAIL).send_mail(self.id, force_send=True)
                if self.tai_san_id.custodian_id and self.tai_san_id.custodian_id.email:
                    template.send_mail(self.id, force_send=True)
                _logger.info("Sent %s email for maintenance %s", email_type, self.name)
        except Exception as e:
            _logger.error("Error sending maintenance email (%s): %s", email_type, str(e))

    def action_start(self):
        self.ensure_one()
        self.state = 'in_progress'
        # Update asset state
        if self.tai_san_id:
            self.tai_san_id.write({'state': 'maintenance'})

    def action_done(self):
        self.ensure_one()
        self.write({'state': 'done', 'ngay_hoan_thanh': fields.Date.today()})
        
        # Restore asset state (default to in_use, or configurable)
        if self.tai_san_id:
             self.tai_san_id.write({'state': 'in_use'})
             
             # Create technical history log
             self.env['lich_su_ky_thuat'].create({
                'tai_san_id': self.tai_san_id.id,
                'noi_dung': f"{dict(self._fields['loai_bao_tri'].selection).get(self.loai_bao_tri)}: {self.mo_ta}. Nguyen nhan: {self.nguyen_nhan}",
                'ngay': self.ngay_bao_tri,
                'ghi_chu': f"Ket qua: {self.ket_qua}. Chi phi: {self.tong_chi_phi}"
             })

    def action_cancel(self):
        self.state = 'cancelled'
        if self.tai_san_id and self.tai_san_id.state == 'maintenance':
             self.tai_san_id.write({'state': 'in_use'}) # Revert if cancelled logic needed
