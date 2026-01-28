from odoo import models, fields, api
from datetime import datetime, time


class TangCa(models.Model):
    _name = 'tang_ca'
    _description = 'Tăng ca (OT)'
    _order = 'ngay_tang_ca desc, nhan_vien_id'
    _rec_name = 'display_name'

    cham_cong_id = fields.Many2one(
        "cham_cong",
        string="Bản ghi chấm công",
        required=True,
        ondelete='cascade'
    )
    
    nhan_vien_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên",
        related='cham_cong_id.nhan_vien_id',
        store=True,
        readonly=True
    )
    ngay_tang_ca = fields.Date(
        "Ngày tăng ca",
        related='cham_cong_id.ngay_cham_cong',
        store=True,
        readonly=True
    )
    
    so_gio_ot = fields.Float(
        "Số giờ OT",
        related='cham_cong_id.so_gio_ot',
        store=True,
        readonly=True
    )
    
    loai_ngay = fields.Selection(
        [
            ("ngay_thuong", "Ngày thường"),
            ("ngay_nghi", "Ngày nghỉ"),
            ("ngay_le", "Ngày lễ")
        ],
        string="Loại ngày",
        related='cham_cong_id.loai_ngay',
        store=True
    )
    
    # Hệ số OT
    he_so_ot = fields.Float(
        "Hệ số OT",
        compute="_compute_he_so_ot",
        store=True,
        readonly=True
    )
    
    # Lương OT
    luong_ot = fields.Float(
        "Lương OT",
        compute="_compute_luong_ot",
        store=True,
        readonly=True
    )
    
    gio_bat_dau_ot = fields.Datetime(
        "Giờ bắt đầu OT",
        compute="_compute_gio_ot",
        store=True,
        readonly=True
    )
    gio_ket_thuc_ot = fields.Datetime(
        "Giờ kết thúc OT",
        related='cham_cong_id.gio_ra',
        store=True,
        readonly=True
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    display_name = fields.Char(
        "Tên hiển thị",
        compute="_compute_display_name",
        store=True
    )
    
    @api.depends('nhan_vien_id', 'ngay_tang_ca', 'so_gio_ot')
    def _compute_display_name(self):
        for record in self:
            nhan_vien = record.nhan_vien_id.ho_va_ten if record.nhan_vien_id else ""
            record.display_name = f"{nhan_vien} - {record.ngay_tang_ca or ''} - {record.so_gio_ot:.2f}h OT"
    
    @api.depends('loai_ngay')
    def _compute_he_so_ot(self):
        for record in self:
            if record.loai_ngay == "ngay_thuong":
                record.he_so_ot = 1.5  # 150%
            elif record.loai_ngay == "ngay_nghi":
                record.he_so_ot = 2.0  # 200%
            elif record.loai_ngay == "ngay_le":
                record.he_so_ot = 3.0  # 300%
            else:
                record.he_so_ot = 1.5
    
    @api.depends('cham_cong_id.ngay_cham_cong')
    def _compute_gio_ot(self):
        for record in self:
            if record.cham_cong_id and record.cham_cong_id.ngay_cham_cong:
                ngay_cham = record.cham_cong_id.ngay_cham_cong
                if isinstance(ngay_cham, str):
                    ngay_cham = fields.Date.from_string(ngay_cham)
                elif hasattr(ngay_cham, 'date'):
                    ngay_cham = ngay_cham.date()
                # Giờ bắt đầu OT = 17:30
                record.gio_bat_dau_ot = datetime.combine(ngay_cham, time(17, 30))
    
    @api.depends('so_gio_ot', 'he_so_ot', 'nhan_vien_id')
    def _compute_luong_ot(self):
        for record in self:
            if record.so_gio_ot > 0 and record.nhan_vien_id:
                # Lấy lương giờ từ bảng lương (nếu có)
                # Tạm thời tính theo lương cơ bản / (26 * 8)
                # Sẽ được tính lại trong bảng lương
                record.luong_ot = 0  # Sẽ được tính trong bảng lương

