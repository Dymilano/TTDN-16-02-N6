from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LichSuCongTac(models.Model):
    _name = 'lich_su_cong_tac'
    _description = 'Bảng chứa thông tin lịch sử công tác'
    _order = 'ngay_bat_dau desc'

    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban", required=True)
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ", required=True)
    
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    
    loai_chuc_vu = fields.Selection(
        [
            ("chinh", "Chính"), 
            ("kiem_nhiem", "Kiêm nhiệm")
        ], 
        string="Loại chức vụ", 
        default="chinh"
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau:
                if record.ngay_ket_thuc < record.ngay_bat_dau:
                    raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")
    
    
