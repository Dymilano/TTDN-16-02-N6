from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class KyLuong(models.Model):
    _name = 'ky_luong'
    _description = 'Kỳ lương'
    _order = 'nam desc, thang desc'

    name = fields.Char(
        "Tên kỳ lương",
        compute="_compute_name",
        store=True
    )
    thang = fields.Selection(
        [
            ('01', 'Tháng 1'), ('02', 'Tháng 2'), ('03', 'Tháng 3'),
            ('04', 'Tháng 4'), ('05', 'Tháng 5'), ('06', 'Tháng 6'),
            ('07', 'Tháng 7'), ('08', 'Tháng 8'), ('09', 'Tháng 9'),
            ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
        ],
        string="Tháng",
        required=True
    )
    nam = fields.Integer(
        "Năm",
        required=True,
        default=lambda self: datetime.now().year
    )
    
    tu_ngay = fields.Date("Từ ngày", required=True)
    den_ngay = fields.Date("Đến ngày", required=True)
    
    trang_thai = fields.Selection(
        [
            ("draft", "Nháp"),
            ("approved", "Đã duyệt"),
            ("locked", "Đã khóa")
        ],
        string="Trạng thái",
        default="draft"
    )
    
    bang_luong_ids = fields.One2many(
        "bang_luong_thang",
        "ky_luong_id",
        string="Danh sách bảng lương"
    )
    
    _sql_constraints = [
        ('unique_thang_nam', 'unique(thang, nam)', 'Kỳ lương cho tháng/năm này đã tồn tại!')
    ]
    
    @api.depends('thang', 'nam')
    def _compute_name(self):
        for record in self:
            record.name = f"Kỳ lương {record.thang}/{record.nam}"
    
    @api.constrains('tu_ngay', 'den_ngay')
    def _check_ngay(self):
        for record in self:
            if record.tu_ngay and record.den_ngay:
                if record.den_ngay < record.tu_ngay:
                    raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    def action_approve(self):
        for rec in self:
            rec.trang_thai = 'approved'

    def action_lock(self):
        for rec in self:
            rec.trang_thai = 'locked'

    def action_generate_bang_luong(self):
        for rec in self:
            if rec.trang_thai != 'locked':
                raise ValidationError("Chỉ được tạo bảng lương khi kỳ lương đã khóa.")
            cham_cong = self.env['cham_cong'].search([
                ('ngay_cham_cong', '>=', rec.tu_ngay),
                ('ngay_cham_cong', '<=', rec.den_ngay),
            ])
            nhan_vien_ids = cham_cong.mapped('nhan_vien_id')
            for nv in nhan_vien_ids:
                if nv.trang_thai == 'nghi_viec' and nv.ngay_ket_thuc and nv.ngay_ket_thuc < rec.tu_ngay:
                    # bỏ qua nhân viên đã nghỉ trước kỳ
                    continue
                existing = self.env['bang_luong_thang'].search([
                    ('ky_luong_id', '=', rec.id),
                    ('nhan_vien_id', '=', nv.id),
                ], limit=1)
                vals = {
                    'ky_luong_id': rec.id,
                    'nhan_vien_id': nv.id,
                }
                if existing:
                    existing.write(vals)
                else:
                    self.env['bang_luong_thang'].create(vals)


class BangLuongThang(models.Model):
    _name = 'bang_luong_thang'
    _description = 'Bảng lương tháng'
    _order = 'nhan_vien_id, ky_luong_id'
    _rec_name = 'display_name'

    ky_luong_id = fields.Many2one(
        "ky_luong",
        string="Kỳ lương",
        required=True,
        ondelete='cascade'
    )
    nhan_vien_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên",
        required=True
    )
    
    # Lương cơ bản (mặc định 10,400,000)
    luong_co_ban_thang = fields.Float(
        "Lương cơ bản tháng",
        required=True,
        default=10400000,
        help="Lương cơ bản theo hợp đồng (mặc định 10,400,000)"
    )
    
    # Công chuẩn (mặc định 26 ngày, bỏ chủ nhật)
    cong_chuan_thang = fields.Float(
        "Công chuẩn tháng",
        default=26.0,
        readonly=True,
        help="Số ngày công chuẩn trong tháng (26 ngày, bỏ chủ nhật)"
    )
    
    # Tổng hợp từ chấm công
    tong_gio_lam = fields.Float(
        "Tổng giờ làm",
        compute="_compute_tong_hop_cham_cong",
        store=True,
        readonly=True
    )
    tong_ngay_cong = fields.Float(
        "Tổng ngày công",
        compute="_compute_tong_hop_cham_cong",
        store=True,
        readonly=True
    )
    
    # Đơn giá
    don_gia_ngay = fields.Float(
        "Đơn giá ngày",
        compute="_compute_don_gia",
        store=True,
        readonly=True,
        help="Lương cơ bản / Công chuẩn"
    )
    don_gia_gio = fields.Float(
        "Đơn giá giờ",
        compute="_compute_don_gia",
        store=True,
        readonly=True,
        help="Lương tháng / (26 × 8)"
    )
    
    # Tính lương theo công thức: Lương tháng = Lương cơ bản / 26 × Số công thực tế
    luong_theo_cong = fields.Float(
        "Lương theo công",
        compute="_compute_luong",
        store=True,
        readonly=True,
        help="Lương cơ bản / Công chuẩn × Số công thực tế"
    )
    
    # Tổng hợp OT
    tong_gio_ot = fields.Float(
        "Tổng giờ OT",
        compute="_compute_tong_ot",
        store=True,
        readonly=True
    )
    luong_ot = fields.Float(
        "Lương OT",
        compute="_compute_luong_ot",
        store=True,
        readonly=True,
        help="Tính theo hệ số: ngày thường 150%, ngày nghỉ 200%, ngày lễ 300%"
    )
    
    # Tổng hợp vi phạm
    tong_phat_vi_pham = fields.Float(
        "Tổng phạt vi phạm",
        compute="_compute_tong_phat",
        store=True,
        readonly=True
    )
    
    # Lương thực nhận
    luong_thuc_nhan = fields.Float(
        "Lương thực nhận",
        compute="_compute_luong",
        store=True,
        readonly=True,
        help="Lương theo công + Lương OT - Phạt vi phạm"
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    display_name = fields.Char(
        "Tên hiển thị",
        compute="_compute_display_name",
        store=True
    )
    
    _sql_constraints = [
        ('unique_nhan_vien_ky', 'unique(nhan_vien_id, ky_luong_id)', 
         'Bảng lương cho nhân viên trong kỳ này đã tồn tại!')
    ]

    @api.model
    def create(self, vals):
        ky = self.env['ky_luong'].browse(vals.get('ky_luong_id'))
        if ky and ky.trang_thai != 'locked':
            raise ValidationError("Chỉ tạo bảng lương khi kỳ lương đã khóa.")
        nv = self.env['nhan_vien'].browse(vals.get('nhan_vien_id'))
        if nv and nv.trang_thai == 'nghi_viec' and nv.ngay_ket_thuc and ky and nv.ngay_ket_thuc < ky.tu_ngay:
            raise ValidationError("Nhân viên đã nghỉ trước kỳ lương, không tạo bảng lương.")
        return super(BangLuongThang, self).create(vals)

    def write(self, vals):
        if 'ky_luong_id' in vals:
            ky = self.env['ky_luong'].browse(vals['ky_luong_id'])
            if ky and ky.trang_thai != 'locked':
                raise ValidationError("Chỉ chỉnh sửa khi kỳ lương đã khóa.")
        return super(BangLuongThang, self).write(vals)
    
    @api.depends('nhan_vien_id', 'ky_luong_id')
    def _compute_display_name(self):
        for record in self:
            nhan_vien = record.nhan_vien_id.ho_va_ten if record.nhan_vien_id else ""
            ky = record.ky_luong_id.name if record.ky_luong_id else ""
            record.display_name = f"{nhan_vien} - {ky}"
    
    @api.depends('luong_co_ban_thang', 'cong_chuan_thang')
    def _compute_don_gia(self):
        for record in self:
            if record.cong_chuan_thang > 0:
                # Đơn giá ngày = Lương cơ bản / Công chuẩn
                record.don_gia_ngay = record.luong_co_ban_thang / record.cong_chuan_thang
                # Đơn giá giờ = Lương tháng / (26 × 8)
                gio_chuan = record.cong_chuan_thang * 8
                record.don_gia_gio = record.luong_co_ban_thang / gio_chuan if gio_chuan > 0 else 0
            else:
                record.don_gia_ngay = 0
                record.don_gia_gio = 0
    
    @api.depends('nhan_vien_id', 'ky_luong_id.tu_ngay', 'ky_luong_id.den_ngay')
    def _compute_tong_hop_cham_cong(self):
        for record in self:
            if record.nhan_vien_id and record.ky_luong_id:
                cham_cong = self.env['cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_cham_cong', '>=', record.ky_luong_id.tu_ngay),
                    ('ngay_cham_cong', '<=', record.ky_luong_id.den_ngay)
                ])
                
                record.tong_gio_lam = sum(cham_cong.mapped('so_gio_lam') or [0])
                record.tong_ngay_cong = sum(cham_cong.mapped('ngay_cong') or [0])
            else:
                record.tong_gio_lam = 0
                record.tong_ngay_cong = 0
    
    @api.depends('nhan_vien_id', 'ky_luong_id')
    def _compute_tong_ot(self):
        for record in self:
            if record.nhan_vien_id and record.ky_luong_id:
                cham_cong = self.env['cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_cham_cong', '>=', record.ky_luong_id.tu_ngay),
                    ('ngay_cham_cong', '<=', record.ky_luong_id.den_ngay)
                ])
                record.tong_gio_ot = sum(cham_cong.mapped('so_gio_ot') or [0])
            else:
                record.tong_gio_ot = 0
    
    @api.depends('tong_gio_ot', 'don_gia_gio', 'nhan_vien_id', 'ky_luong_id')
    def _compute_luong_ot(self):
        for record in self:
            if record.tong_gio_ot > 0 and record.don_gia_gio > 0 and record.nhan_vien_id and record.ky_luong_id:
                # Tính lương OT theo từng ngày với hệ số khác nhau
                cham_cong = self.env['cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_cham_cong', '>=', record.ky_luong_id.tu_ngay),
                    ('ngay_cham_cong', '<=', record.ky_luong_id.den_ngay),
                    ('so_gio_ot', '>', 0)
                ])
                
                total_ot = 0
                for cc in cham_cong:
                    # Xác định hệ số theo loại ngày
                    if cc.loai_ngay == "ngay_thuong":
                        he_so = 1.5  # 150%
                    elif cc.loai_ngay == "ngay_nghi":
                        he_so = 2.0  # 200%
                    elif cc.loai_ngay == "ngay_le":
                        he_so = 3.0  # 300%
                    else:
                        he_so = 1.5
                    
                    total_ot += record.don_gia_gio * cc.so_gio_ot * he_so
                
                record.luong_ot = total_ot
            else:
                record.luong_ot = 0
    
    @api.depends('nhan_vien_id', 'ky_luong_id')
    def _compute_tong_phat(self):
        for record in self:
            if record.nhan_vien_id and record.ky_luong_id:
                vi_pham = self.env['vi_pham_cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_vi_pham', '>=', record.ky_luong_id.tu_ngay),
                    ('ngay_vi_pham', '<=', record.ky_luong_id.den_ngay)
                ])
                record.tong_phat_vi_pham = sum(vi_pham.mapped('so_tien_phat') or [0])
            else:
                record.tong_phat_vi_pham = 0
    
    @api.depends('luong_co_ban_thang', 'tong_ngay_cong', 'don_gia_ngay', 
                 'luong_ot', 'tong_phat_vi_pham')
    def _compute_luong(self):
        for record in self:
            # Công thức: Lương tháng = Lương cơ bản / Công chuẩn × Số công thực tế
            record.luong_theo_cong = record.don_gia_ngay * record.tong_ngay_cong
            
            # Lương thực nhận = Lương theo công + Lương OT - Phạt vi phạm
            record.luong_thuc_nhan = record.luong_theo_cong + record.luong_ot - record.tong_phat_vi_pham
