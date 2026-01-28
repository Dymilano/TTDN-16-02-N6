from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PhongBan(models.Model):
    _name = 'phong_ban'
    _description = 'Bảng chứa thông tin phòng ban'
    _rec_name = 'ten_phong_ban'
    _order = 'ma_phong_ban asc'

    ma_phong_ban = fields.Char("Mã phòng ban", required=True)
    ten_phong_ban = fields.Char("Tên phòng ban", required=True)
    mo_ta = fields.Text("Mô tả")
    
    # Cấu trúc phân cấp
    parent_id = fields.Many2one(
        "phong_ban", 
        string="Phòng ban cha",
        ondelete='restrict'
    )
    child_ids = fields.One2many(
        "phong_ban",
        "parent_id",
        string="Phòng ban con"
    )
    
    # Trưởng phòng
    truong_phong_id = fields.Many2one(
        "nhan_vien",
        string="Trưởng phòng"
    )
    
    # Thông tin liên hệ
    dia_chi = fields.Char("Địa chỉ")
    so_dien_thoai = fields.Char("Số điện thoại")
    email = fields.Char("Email")
    
    # Số lượng nhân viên
    so_nhan_vien = fields.Integer(
        "Số nhân viên",
        compute="_compute_so_nhan_vien",
        store=True
    )
    
    # Trạng thái
    trang_thai = fields.Selection(
        [
            ("hoat_dong", "Hoạt động"),
            ("tam_dung", "Tạm dừng"),
            ("dong_cua", "Đóng cửa")
        ],
        string="Trạng thái",
        default="hoat_dong"
    )
    
    _sql_constraints = [
        ('ma_phong_ban_unique', 'unique(ma_phong_ban)', 'Mã phòng ban phải là duy nhất')
    ]
    
    @api.depends('truong_phong_id')
    def _compute_so_nhan_vien(self):
        for record in self:
            # Đếm số nhân viên thuộc phòng ban này
            nhan_vien_count = self.env['nhan_vien'].search_count([
                ('phong_ban_id', '=', record.id)
            ])
            record.so_nhan_vien = nhan_vien_count
    
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for record in self:
            if record.parent_id:
                if record.parent_id.id == record.id:
                    raise ValidationError("Phòng ban không thể là phòng ban cha của chính nó!")
                # Kiểm tra vòng lặp
                parent = record.parent_id
                while parent:
                    if parent.id == record.id:
                        raise ValidationError("Không thể tạo vòng lặp trong cấu trúc phòng ban!")
                    parent = parent.parent_id

