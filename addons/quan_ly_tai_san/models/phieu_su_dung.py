from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PhieuSuDung(models.Model):
    _name = 'phieu_su_dung'
    _description = 'Phiếu sử dụng tài sản'
    _order = 'ngay_su_dung desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    bo_phan_id = fields.Many2one('phong_ban', string='Bộ phận', related='nhan_vien_id.phong_ban_id', store=True)
    ngay_su_dung = fields.Date(string='Ngày sử dụng', default=fields.Date.context_today, required=True)
    line_ids = fields.One2many('phieu_su_dung.line', 'phieu_su_dung_id', string='Chi tiết')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft')
    ghi_chu = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('phieu.su.dung') or _('New')
        return super(PhieuSuDung, self).create(vals)

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_('Vui lòng thêm tài sản vào phiếu sử dụng.'))
            for line in rec.line_ids:
                if line.tai_san_id.trang_thai_thanh_ly == 'da_thanh_ly':
                     raise ValidationError(_('Tài sản %s đã thanh lý, không thể sử dụng.') % line.tai_san_id.ten_tai_san)
                
                # Check current allocation
                current_allocation = self.env['phan_bo_tai_san'].search([
                    ('tai_san_id', '=', line.tai_san_id.id),
                    ('trang_thai', '=', 'in-use')
                ], limit=1)

                if current_allocation:
                    # Update existing allocation to not-in-use or change logic?
                    # Plan says: "Updates or creates this assignment".
                    # Let's release the old one to keep history clean
                    current_allocation.trang_thai = 'not-in-use'

                # Create new allocation
                self.env['phan_bo_tai_san'].create({
                    'tai_san_id': line.tai_san_id.id,
                    'phong_ban_id': rec.bo_phan_id.id,
                    'nhan_vien_su_dung_id': rec.nhan_vien_id.id,
                    'ngay_phat': rec.ngay_su_dung,
                    'vi_tri_tai_san_id': rec.bo_phan_id.id, # Default to department loc
                    'trang_thai': 'in-use',
                    'ghi_chu': rec.ghi_chu or f"Phân bổ từ phiếu {rec.name}"
                })
            rec.state = 'confirmed'

    def action_cancel(self):
        self.mapped('line_ids.tai_san_id').write({'trang_thai_thanh_ly': 'chua_phan_bo'}) # Revert logic might be complex if we want to restore previous state. 
        # For simple reverting, we just set state to cancelled. User might need to manually fix allocations if they made a mistake.
        self.write({'state': 'cancelled'})


class PhieuSuDungLine(models.Model):
    _name = 'phieu_su_dung.line'
    _description = 'Chi tiết phiếu sử dụng'

    phieu_su_dung_id = fields.Many2one('phieu_su_dung', string='Phiếu sử dụng', ondelete='cascade')
    tai_san_id = fields.Many2one('tai_san', string='Tài sản', required=True, domain=[('trang_thai_thanh_ly', '!=', 'da_thanh_ly')])
    ghi_chu = fields.Char(string='Ghi chú')

    @api.constrains('tai_san_id')
    def _check_tai_san_unique(self):
        for line in self:
            # Check duplicate in same slip
            domain = [
                ('phieu_su_dung_id', '=', line.phieu_su_dung_id.id),
                ('tai_san_id', '=', line.tai_san_id.id),
                ('id', '!=', line.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('Tài sản %s đã có trong phiếu này.') % line.tai_san_id.ten_tai_san)
