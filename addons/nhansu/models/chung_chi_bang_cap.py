from odoo import models, fields, api


class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Bảng chứa thông tin chứng chỉ bằng cấp'
    _rec_name = 'ten_chung_chi_bang_cap'
    _order = 'ma_chung_chi_bang_cap asc'

    ma_chung_chi_bang_cap = fields.Char("Mã chứng chỉ, bằng cấp", required=True)
    ten_chung_chi_bang_cap = fields.Char("Tên chứng chỉ, bằng cấp", required=True)
    mo_ta = fields.Text("Mô tả")
    
    # Loại chứng chỉ
    loai = fields.Selection(
        [
            ("bang_cap", "Bằng cấp"),
            ("chung_chi", "Chứng chỉ"),
            ("giay_chung_nhan", "Giấy chứng nhận"),
            ("chung_chi_quoc_te", "Chứng chỉ quốc tế")
        ],
        string="Loại",
        default="chung_chi"
    )
    
    # Cơ quan cấp
    co_quan_cap = fields.Char("Cơ quan cấp")
    
    # Thời hạn hiệu lực
    thoi_han = fields.Integer("Thời hạn (tháng)", help="Số tháng hiệu lực của chứng chỉ")
    
    # Số lượng người có chứng chỉ này
    so_nguoi_co = fields.Integer(
        "Số người có",
        compute="_compute_so_nguoi_co",
        store=True
    )
    
    _sql_constraints = [
        ('ma_chung_chi_bang_cap_unique', 'unique(ma_chung_chi_bang_cap)', 'Mã chứng chỉ bằng cấp phải là duy nhất')
    ]
    
    @api.depends('ten_chung_chi_bang_cap')
    def _compute_so_nguoi_co(self):
        for record in self:
            count = self.env['danh_sach_chung_chi_bang_cap'].search_count([
                ('chung_chi_bang_cap_id', '=', record.id)
            ])
            record.so_nguoi_co = count
