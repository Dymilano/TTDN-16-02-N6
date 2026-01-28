from odoo import models, fields, api


class ViPhamChamCong(models.Model):
    _name = 'vi_pham_cham_cong'
    _description = 'Vi phạm chấm công'
    _order = 'ngay_vi_pham desc'

    cham_cong_id = fields.Many2one(
        "cham_cong",
        string="Bản ghi chấm công",
        required=True,
        ondelete='cascade'
    )
    
    # Related fields
    nhan_vien_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên",
        related='cham_cong_id.nhan_vien_id',
        store=True,
        readonly=True
    )
    ngay_vi_pham = fields.Date(
        "Ngày vi phạm",
        related='cham_cong_id.ngay_cham_cong',
        store=True,
        readonly=True
    )
    
    loai_vi_pham = fields.Selection(
        [
            ("muon_gio", "Muộn giờ"),
            ("som_ve", "Về sớm"),
            ("quen_cham_cong", "Quên chấm công"),
            ("thieu_gio", "Thiếu giờ"),
            ("khac", "Khác")
        ],
        string="Loại vi phạm",
        required=True
    )
    
    muc_do = fields.Selection(
        [
            ("nhe", "Nhẹ"),
            ("vua", "Vừa"),
            ("nang", "Nặng")
        ],
        string="Mức độ",
        required=True,
        default="nhe"
    )
    
    so_phut = fields.Integer("Số phút")
    so_tien_phat = fields.Float("Số tiền phạt")
    
    mo_ta = fields.Text("Mô tả")
    
    _rec_name = 'display_name'
    display_name = fields.Char(
        "Tên hiển thị",
        compute="_compute_display_name",
        store=True
    )
    
    @api.depends('nhan_vien_id', 'ngay_vi_pham', 'loai_vi_pham')
    def _compute_display_name(self):
        for record in self:
            nhan_vien = record.nhan_vien_id.ho_va_ten if record.nhan_vien_id else ""
            loai = dict(record._fields['loai_vi_pham'].selection).get(record.loai_vi_pham, "")
            record.display_name = f"{nhan_vien} - {loai} - {record.ngay_vi_pham or ''}"

