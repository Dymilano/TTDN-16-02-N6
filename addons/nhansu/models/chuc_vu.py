from odoo import models, fields, api


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'
    _order = 'ma_chuc_vu asc'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    mo_ta = fields.Text("Mô tả")
    
    # Phân cấp chức vụ
    cap_bac = fields.Selection(
        [
            ("nhan_vien", "Nhân viên"),
            ("chuyen_vien", "Chuyên viên"),
            ("truong_phong", "Trưởng phòng"),
            ("pho_giam_doc", "Phó giám đốc"),
            ("giam_doc", "Giám đốc"),
            ("tong_giam_doc", "Tổng giám đốc")
        ],
        string="Cấp bậc",
        default="nhan_vien"
    )
    
    # Mức lương tối thiểu và tối đa (tham khảo)
    luong_toi_thieu = fields.Float("Lương tối thiểu (tham khảo)")
    luong_toi_da = fields.Float("Lương tối đa (tham khảo)")
    
    # Số lượng nhân viên
    so_nhan_vien = fields.Integer(
        "Số nhân viên",
        compute="_compute_so_nhan_vien",
        store=True
    )
    
    _sql_constraints = [
        ('ma_chuc_vu_unique', 'unique(ma_chuc_vu)', 'Mã chức vụ phải là duy nhất')
    ]
    
    @api.depends('ten_chuc_vu')
    def _compute_so_nhan_vien(self):
        for record in self:
            nhan_vien_count = self.env['nhan_vien'].search_count([
                ('chuc_vu_id', '=', record.id)
            ])
            record.so_nhan_vien = nhan_vien_count
