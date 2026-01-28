from odoo import models, fields, api
from datetime import datetime, time, timedelta
from odoo.exceptions import ValidationError


class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bảng chấm công nhân viên'
    _order = 'ngay_cham_cong desc, nhan_vien_id'
    _rec_name = 'display_name'

    nhan_vien_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên",
        required=True
    )
    ngay_cham_cong = fields.Date(
        "Ngày chấm công",
        required=True,
        default=fields.Date.today
    )
    
    # Giờ vào/ra
    gio_vao = fields.Datetime("Giờ vào")
    gio_ra = fields.Datetime("Giờ ra")
    
    # Giờ nghỉ cố định: 12:30-13:30 (1 giờ)
    gio_nghi = fields.Float(
        "Số giờ nghỉ",
        default=1.0,
        readonly=True,
        help="Nghỉ trưa từ 12:30-13:30 (1 giờ)"
    )
    
    # Tính toán số giờ làm (sáng 4h + chiều 4h = 8h)
    so_gio_lam = fields.Float(
        "Số giờ làm",
        compute="_compute_so_gio_lam",
        store=True,
        readonly=True,
        help="Sáng 4 tiếng (08:30-12:30) + Chiều 4 tiếng (13:30-17:30) = 8 tiếng"
    )
    
    # Giờ OT (sau 17:30)
    so_gio_ot = fields.Float(
        "Số giờ OT",
        compute="_compute_so_gio_ot",
        store=True,
        readonly=True,
        help="Giờ làm sau 17:30 (tăng ca)"
    )
    
    # Trạng thái
    trang_thai = fields.Selection(
        [
            ("vang", "Vắng"),
            ("dung_gio", "Đúng giờ"),
            ("muon_gio", "Muộn giờ"),
            ("som_ve", "Về sớm")
        ],
        string="Trạng thái",
        compute="_compute_trang_thai",
        store=True,
        readonly=True
    )
    
    # Tình trạng chấm công
    tinh_trang_cham_cong = fields.Selection(
        [
            ("du_vao_ra", "Đủ vào/ra"),
            ("thieu_vao", "Thiếu vào"),
            ("thieu_ra", "Thiếu ra"),
            ("thieu_ca_hai", "Thiếu cả hai")
        ],
        string="Tình trạng chấm công",
        compute="_compute_tinh_trang_cham_cong",
        store=True,
        readonly=True
    )
    
    # Phút muộn/sớm (tính từ 00:00)
    phut_muon = fields.Integer(
        "Phút muộn",
        compute="_compute_phut_muon_som",
        store=True,
        readonly=True,
        help="Tính từ 00:00, sau 08:30 là muộn"
    )
    phut_som = fields.Integer(
        "Phút về sớm",
        compute="_compute_phut_muon_som",
        store=True,
        readonly=True,
        help="Chấm công trước 17:30 là về sớm"
    )
    
    # Vi phạm
    vi_pham_ids = fields.One2many(
        "vi_pham_cham_cong",
        "cham_cong_id",
        string="Danh sách vi phạm"
    )
    
    # Quy đổi ngày công
    ngay_cong = fields.Float(
        "Ngày công",
        compute="_compute_ngay_cong",
        store=True,
        readonly=True,
        help="Quy đổi: đủ 8h = 1 công, 4-8h = 0.5 công, <4h = 0 công"
    )
    
    # Loại ngày (để tính OT)
    loai_ngay = fields.Selection(
        [
            ("ngay_thuong", "Ngày thường"),
            ("ngay_nghi", "Ngày nghỉ"),
            ("ngay_le", "Ngày lễ")
        ],
        string="Loại ngày",
        default="ngay_thuong",
        help="Phân loại để tính hệ số OT"
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    # Giờ chuẩn cố định
    GIO_BAT_DAU_CHUAN = 8.5  # 08:30
    GIO_KET_THUC_CHUAN = 17.5  # 17:30
    GIO_NGHI_TRUA_BAT_DAU = 12.5  # 12:30
    GIO_NGHI_TRUA_KET_THUC = 13.5  # 13:30
    
    _sql_constraints = [
        ('unique_nhan_vien_ngay', 'unique(nhan_vien_id, ngay_cham_cong)', 
         'Mỗi nhân viên chỉ được chấm công 1 lần mỗi ngày!')
    ]
    khoa_ky_luong = fields.Boolean(
        "Đã khóa theo kỳ lương",
        compute="_compute_khoa_ky_luong",
        store=False,
        help="Không thể sửa khi ngày chấm công thuộc kỳ lương đã khóa"
    )
    
    def _ensure_not_locked_period(self, vals=None):
        """Ngăn sửa/xóa khi ngày nằm trong kỳ lương đã khóa."""
        vals = vals or {}
        records = self
        if not records and vals.get('ngay_cham_cong'):
            # create path, check date from vals
            target_dates = [vals.get('ngay_cham_cong')]
        else:
            target_dates = [rec.ngay_cham_cong for rec in records]
        for target_date in target_dates:
            if not target_date:
                continue
            locked_period = self.env['ky_luong'].search([
                ('trang_thai', '=', 'locked'),
                ('tu_ngay', '<=', target_date),
                ('den_ngay', '>=', target_date),
            ], limit=1)
            if locked_period:
                raise ValidationError(
                    f"Không thể sửa/chấm công cho ngày {target_date} vì kỳ lương {locked_period.name} đã khóa."
                )
    
    @api.depends('ngay_cham_cong')
    def _compute_khoa_ky_luong(self):
        for record in self:
            locked = False
            if record.ngay_cham_cong:
                locked = bool(self.env['ky_luong'].search_count([
                    ('trang_thai', '=', 'locked'),
                    ('tu_ngay', '<=', record.ngay_cham_cong),
                    ('den_ngay', '>=', record.ngay_cham_cong),
                ]))
            record.khoa_ky_luong = locked
    
    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham_cong:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {record.ngay_cham_cong}"
            else:
                record.display_name = "Chấm công"
    
    @api.depends('gio_vao', 'gio_ra')
    def _compute_tinh_trang_cham_cong(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                record.tinh_trang_cham_cong = "du_vao_ra"
            elif record.gio_vao and not record.gio_ra:
                record.tinh_trang_cham_cong = "thieu_ra"
            elif not record.gio_vao and record.gio_ra:
                record.tinh_trang_cham_cong = "thieu_vao"
            else:
                record.tinh_trang_cham_cong = "thieu_ca_hai"
    
    @api.depends('gio_vao', 'gio_ra', 'gio_nghi')
    def _compute_so_gio_lam(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                # Tính số giờ hiện diện
                delta = record.gio_ra - record.gio_vao
                present_hours = delta.total_seconds() / 3600.0
                
                # Trừ giờ nghỉ trưa (1 giờ)
                total_hours = max(0, present_hours - (record.gio_nghi or 1.0))
                
                # Tính giờ ra chuẩn để xác định OT
                ngay_cham = record.ngay_cham_cong
                if isinstance(ngay_cham, str):
                    ngay_cham = fields.Date.from_string(ngay_cham)
                elif hasattr(ngay_cham, 'date'):
                    ngay_cham = ngay_cham.date()
                
                gio_ra_chuan = datetime.combine(ngay_cham, time(17, 30))
                gio_ra_actual = record.gio_ra
                if isinstance(gio_ra_actual, str):
                    gio_ra_actual = fields.Datetime.from_string(gio_ra_actual)
                
                # Nếu có OT (ra sau 17:30), số giờ làm = 8h, phần còn lại là OT
                if gio_ra_actual and gio_ra_actual > gio_ra_chuan:
                    record.so_gio_lam = 8.0  # Giờ làm chuẩn là 8h
                else:
                    # Không có OT, số giờ làm = tổng giờ - nghỉ
                    record.so_gio_lam = min(8.0, total_hours)  # Tối đa 8h
            else:
                record.so_gio_lam = 0
    
    @api.depends('gio_ra', 'ngay_cham_cong')
    def _compute_so_gio_ot(self):
        for record in self:
            if record.gio_ra and record.ngay_cham_cong:
                # Tính giờ ra chuẩn (17:30)
                ngay_cham = record.ngay_cham_cong
                if isinstance(ngay_cham, str):
                    ngay_cham = fields.Date.from_string(ngay_cham)
                elif hasattr(ngay_cham, 'date'):
                    ngay_cham = ngay_cham.date()
                
                gio_ra_chuan = datetime.combine(ngay_cham, time(17, 30))
                gio_ra_actual = record.gio_ra
                if isinstance(gio_ra_actual, str):
                    gio_ra_actual = fields.Datetime.from_string(gio_ra_actual)
                
                if gio_ra_actual and gio_ra_actual > gio_ra_chuan:
                    # Tính số giờ OT (sau 17:30)
                    delta = gio_ra_actual - gio_ra_chuan
                    record.so_gio_ot = delta.total_seconds() / 3600.0
                else:
                    record.so_gio_ot = 0.0
            else:
                record.so_gio_ot = 0.0
    
    @api.depends('gio_vao', 'gio_ra', 'ngay_cham_cong')
    def _compute_phut_muon_som(self):
        for record in self:
            record.phut_muon = 0
            record.phut_som = 0
            
            if record.gio_vao and record.ngay_cham_cong:
                # Tính giờ vào chuẩn (08:30)
                ngay_cham = record.ngay_cham_cong
                if isinstance(ngay_cham, str):
                    ngay_cham = fields.Date.from_string(ngay_cham)
                elif hasattr(ngay_cham, 'date'):
                    ngay_cham = ngay_cham.date()
                
                gio_vao_chuan = datetime.combine(ngay_cham, time(8, 30))
                gio_vao_actual = record.gio_vao
                if isinstance(gio_vao_actual, str):
                    gio_vao_actual = fields.Datetime.from_string(gio_vao_actual)
                
                if gio_vao_actual:
                    # Tính từ 00:00 (ngày chấm công)
                    ngay_00_00 = datetime.combine(ngay_cham, time(0, 0))
                    diff_from_midnight = (gio_vao_actual - ngay_00_00).total_seconds() / 60.0
                    diff_from_standard = (gio_vao_actual - gio_vao_chuan).total_seconds() / 60.0
                    
                    # Sau 08:30 là muộn (tính từ 00:00)
                    if diff_from_midnight > (8 * 60 + 30):  # 08:30 = 510 phút
                        record.phut_muon = int(diff_from_standard) if diff_from_standard > 0 else 0
            
            if record.gio_ra and record.ngay_cham_cong:
                # Tính giờ ra chuẩn (17:30)
                ngay_cham = record.ngay_cham_cong
                if isinstance(ngay_cham, str):
                    ngay_cham = fields.Date.from_string(ngay_cham)
                elif hasattr(ngay_cham, 'date'):
                    ngay_cham = ngay_cham.date()
                
                gio_ra_chuan = datetime.combine(ngay_cham, time(17, 30))
                gio_ra_actual = record.gio_ra
                if isinstance(gio_ra_actual, str):
                    gio_ra_actual = fields.Datetime.from_string(gio_ra_actual)
                
                if gio_ra_actual:
                    diff = (gio_ra_chuan - gio_ra_actual).total_seconds() / 60.0
                    # Trước 17:30 là về sớm
                    if diff > 0:
                        record.phut_som = int(diff)
    
    @api.depends('gio_vao', 'gio_ra', 'phut_muon', 'phut_som', 'so_gio_lam')
    def _compute_trang_thai(self):
        for record in self:
            if not record.gio_vao or not record.gio_ra:
                record.trang_thai = "vang"
            elif record.phut_muon > 0:
                record.trang_thai = "muon_gio"
            elif record.phut_som > 0:
                record.trang_thai = "som_ve"
            else:
                record.trang_thai = "dung_gio"
    
    @api.depends('so_gio_lam')
    def _compute_ngay_cong(self):
        for record in self:
            if record.so_gio_lam >= 8:
                record.ngay_cong = 1.0
            elif record.so_gio_lam >= 4:
                record.ngay_cong = 0.5
            else:
                record.ngay_cong = 0.0
    
    @api.model
    def create(self, vals):
        self._ensure_not_locked_period(vals)
        record = super(ChamCong, self).create(vals)
        record._auto_create_violations()
        return record
    
    def write(self, vals):
        self._ensure_not_locked_period(vals)
        result = super(ChamCong, self).write(vals)
        if any(field in vals for field in ['gio_vao', 'gio_ra', 'phut_muon', 'phut_som', 'so_gio_lam']):
            self._auto_create_violations()
        return result

    def unlink(self):
        self._ensure_not_locked_period()
        return super(ChamCong, self).unlink()
    
    def _auto_create_violations(self):
        """Tự động tạo vi phạm dựa trên dữ liệu chấm công"""
        for record in self:
            # Xóa vi phạm cũ
            record.vi_pham_ids.unlink()
            
            violations = []
            
            # Vi phạm muộn giờ
            if record.phut_muon > 0:
                violations.append({
                    'cham_cong_id': record.id,
                    'loai_vi_pham': 'muon_gio',
                    'so_phut': record.phut_muon,
                    'muc_do': 'nhe' if record.phut_muon <= 15 else 'vua' if record.phut_muon <= 30 else 'nang',
                    'mo_ta': f'Đi muộn {record.phut_muon} phút (sau 08:30)'
                })
            
            # Vi phạm về sớm
            if record.phut_som > 0:
                violations.append({
                    'cham_cong_id': record.id,
                    'loai_vi_pham': 'som_ve',
                    'so_phut': record.phut_som,
                    'muc_do': 'nhe' if record.phut_som <= 15 else 'vua' if record.phut_som <= 30 else 'nang',
                    'mo_ta': f'Về sớm {record.phut_som} phút (trước 17:30)'
                })
            
            # Vi phạm thiếu giờ
            if record.so_gio_lam < 8:
                violations.append({
                    'cham_cong_id': record.id,
                    'loai_vi_pham': 'thieu_gio',
                    'so_phut': int((8 - record.so_gio_lam) * 60),
                    'muc_do': 'nhe' if record.so_gio_lam >= 6 else 'vua' if record.so_gio_lam >= 4 else 'nang',
                    'mo_ta': f'Thiếu giờ: chỉ làm {record.so_gio_lam:.2f} giờ (yêu cầu 8 giờ)'
                })
            
            # Vi phạm quên chấm công
            if not record.gio_vao or not record.gio_ra:
                violations.append({
                    'cham_cong_id': record.id,
                    'loai_vi_pham': 'quen_cham_cong',
                    'muc_do': 'nang',
                    'mo_ta': 'Quên chấm công vào/ra'
                })
            
            # Tạo vi phạm
            if violations:
                self.env['vi_pham_cham_cong'].create(violations)
