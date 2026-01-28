from odoo import models, fields, api
from datetime import date


class DanhSachChungChiBangCap(models.Model):
    _name = 'danh_sach_chung_chi_bang_cap'
    _description = 'Bảng danh sách chứng chỉ bằng cấp'
    _order = 'ngay_cap desc'

    chung_chi_bang_cap_id = fields.Many2one("chung_chi_bang_cap", string="Chứng chỉ bằng cấp", required=True)
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    
    ngay_cap = fields.Date("Ngày cấp", default=fields.Date.today)
    ngay_het_han = fields.Date("Ngày hết hạn")
    so_seri = fields.Char("Số seri")
    co_quan_cap = fields.Char("Cơ quan cấp")
    
    trang_thai = fields.Selection(
        [
            ("con_han", "Còn hạn"),
            ("sap_het_han", "Sắp hết hạn"),
            ("het_han", "Hết hạn")
        ],
        string="Trạng thái",
        compute="_compute_trang_thai",
        store=True
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    # Related fields
    ma_dinh_danh = fields.Char("Mã định danh", related='nhan_vien_id.ma_dinh_danh', store=True)
    ho_va_ten = fields.Char("Họ và tên", related='nhan_vien_id.ho_va_ten', store=True)
    tuoi = fields.Integer("Tuổi", related='nhan_vien_id.tuoi', store=True)
    
    @api.depends('ngay_het_han')
    def _compute_trang_thai(self):
        today = date.today()
        for record in self:
            if not record.ngay_het_han:
                record.trang_thai = "con_han"
            else:
                days_until_expiry = (record.ngay_het_han - today).days
                if days_until_expiry < 0:
                    record.trang_thai = "het_han"
                elif days_until_expiry <= 30:
                    record.trang_thai = "sap_het_han"
                else:
                    record.trang_thai = "con_han"
    
