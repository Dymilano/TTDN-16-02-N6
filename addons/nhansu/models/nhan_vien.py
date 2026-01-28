from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    
    # Thông tin công việc hiện tại
    phong_ban_id = fields.Many2one(
        "phong_ban",
        string="Phòng ban hiện tại"
    )
    chuc_vu_id = fields.Many2one(
        "chuc_vu",
        string="Chức vụ hiện tại"
    )
    ngay_vao_lam = fields.Date("Ngày vào làm")
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    trang_thai = fields.Selection(
        [
            ("dang_lam_viec", "Đang làm việc"),
            ("nghi_viec", "Nghỉ việc"),
            ("nghi_phep", "Nghỉ phép"),
            ("thu_viec", "Thử việc")
        ],
        string="Trạng thái",
        default="dang_lam_viec"
    )
    
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True, readonly=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", 
                                        compute="_compute_so_nguoi_bang_tuoi",
                                        store=True,
                                        readonly=True
                                        )
    
    # Tracking
    nguoi_tao = fields.Char("Người tạo", compute="_compute_nguoi_tao", store=True, readonly=True)
    nguoi_sua_cuoi = fields.Char("Người sửa cuối", compute="_compute_nguoi_sua_cuoi", store=True, readonly=True)
    
    @api.depends("create_uid")
    def _compute_nguoi_tao(self):
        for record in self:
            record.nguoi_tao = record.create_uid.name if record.create_uid else False
    
    @api.depends("write_uid", "create_uid", "write_date", "create_date")
    def _compute_nguoi_sua_cuoi(self):
        for record in self:
            if record.id:
                if record.write_date and record.create_date:
                    if record.write_date != record.create_date and record.write_uid:
                        record.nguoi_sua_cuoi = record.write_uid.name
                    elif record.create_uid:
                        record.nguoi_sua_cuoi = record.create_uid.name
                    else:
                        record.nguoi_sua_cuoi = False
                elif record.create_uid:
                    record.nguoi_sua_cuoi = record.create_uid.name
                else:
                    record.nguoi_sua_cuoi = False
            else:
                if record.create_uid:
                    record.nguoi_sua_cuoi = record.create_uid.name
                else:
                    record.nguoi_sua_cuoi = self.env.user.name if self.env.user else False
    
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                domain = [('tuoi', '=', record.tuoi)]
                if record.id:
                    domain.append(('ma_dinh_danh', '!=', record.ma_dinh_danh))
                records = self.env['nhan_vien'].search(domain)
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0
    
    _sql_constrains = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
            else:
                record.ho_va_ten = False
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split()])
                record.ma_dinh_danh = record.ten.lower() + chu_cai_dau
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year
            else:
                record.tuoi = 0

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi and record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")
