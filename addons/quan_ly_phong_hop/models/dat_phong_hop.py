# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

# Email address for automatic notifications
ADMIN_EMAIL = 'nguyenduymilano@gmail.com'

class DatPhongHop(models.Model):
    _name = 'dat_phong_hop'
    _description = 'Đặt phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'
    
    ma_booking = fields.Char(string='Mã booking', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string='Tên cuộc họp', required=True)
    phong_hop_id = fields.Many2one('phong_hop', string='Phòng họp', required=True, tracking=True)
    location_id = fields.Many2one('tai_san.location', string='Địa điểm', related='phong_hop_id.location_id', store=True, readonly=True)
    
    # Thời gian
    start_datetime = fields.Datetime(string='Thời gian bắt đầu', required=True, tracking=True)
    end_datetime = fields.Datetime(string='Thời gian kết thúc', required=True, tracking=True)
    duration_minutes = fields.Integer(string='Thời lượng (phút)', compute='_compute_duration', store=True)
    auto_release_time = fields.Datetime(string='Thời gian tự động giải phóng', compute='_compute_auto_release_time')
    
    # Người chủ trì
    host_id = fields.Many2one('nhan_vien', string='Người chủ trì', required=True, tracking=True)
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban', related='host_id.phong_ban_id', store=True, readonly=True)
    
    # Người tham dự
    chuc_vu_tham_du_ids = fields.Many2many('chuc_vu', 'dat_phong_chuc_vu_rel', 'booking_id', 'chuc_vu_id', string='Chức vụ tham dự')
    phong_ban_tham_du_ids = fields.Many2many('phong_ban', 'dat_phong_phong_ban_rel', 'booking_id', 'phong_ban_id', string='Phòng ban tham dự')
    attendee_ids = fields.Many2many('nhan_vien', 'dat_phong_attendee_rel', 'booking_id', 'nhan_vien_id', string='Người tham dự', compute='_compute_attendee_ids', store=True)
    so_nguoi_tham_du = fields.Integer(string='Số người tham dự', compute='_compute_so_nguoi_tham_du', store=True)
    
    # Thông tin cuộc họp
    muc_dich = fields.Text(string='Mục đích cuộc họp')
    ghi_chu = fields.Text(string='Ghi chú')
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending_approval', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('confirmed', 'Đã xác nhận'),
        ('checked_in', 'Đã check-in'),
        ('in_progress', 'Đang diễn ra'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
        ('no_show', 'Không đến')
    ], string='Trạng thái', default='draft', required=True, tracking=True)
    
    # Check-in/Check-out
    check_in_time = fields.Datetime(string='Thời gian check-in', readonly=True)
    check_out_time = fields.Datetime(string='Thời gian check-out', readonly=True)
    qr_code = fields.Char(string='QR Code', compute='_compute_qr_code')
    
    # Phê duyệt
    can_approval = fields.Boolean(string='Cần phê duyệt', compute='_compute_can_approval')
    approver_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    approval_date = fields.Datetime(string='Ngày duyệt', readonly=True)
    ly_do_tu_choi = fields.Text(string='Lý do từ chối', readonly=True)
    
    # Hủy
    ly_do_huy = fields.Text(string='Lý do hủy', readonly=True)
    
    # Dịch vụ
    dich_vu_ids = fields.One2many('dich_vu_phong_hop', 'booking_id', string='Dịch vụ kèm theo')
    co_catering = fields.Boolean(string='Có catering', compute='_compute_co_catering', store=True)
    tong_chi_phi = fields.Float(string='Tổng chi phí', compute='_compute_tong_chi_phi', store=True)
    
    # Đặt phòng định kỳ
    is_recurring = fields.Boolean(string='Đặt phòng định kỳ', default=False)
    recurring_type = fields.Selection([
        ('daily', 'Hàng ngày'),
        ('weekly', 'Hàng tuần'),
        ('monthly', 'Hàng tháng')
    ], string='Loại định kỳ')
    recurring_end_date = fields.Date(string='Ngày kết thúc định kỳ')
    recurring_count = fields.Integer(string='Số lần lặp lại', default=0)
    recurring_booking_ids = fields.One2many('dat_phong_hop', 'parent_booking_id', string='Các booking định kỳ')
    parent_booking_id = fields.Many2one('dat_phong_hop', string='Booking gốc', readonly=True)
    
    # Đặt nhiều phòng
    is_multi_room = fields.Boolean(string='Đặt nhiều phòng', default=False)
    related_booking_ids = fields.Many2many('dat_phong_hop', 'dat_phong_multi_rel', 'booking_id', 'related_booking_id', string='Các booking liên quan')
    
    # Đặt thay người khác
    is_assistant_booking = fields.Boolean(string='Đặt thay người khác', default=False)
    assistant_id = fields.Many2one('res.users', string='Người đặt thay')
    
    # Thông tin khác
    is_outside_hours = fields.Boolean(string='Ngoài giờ làm việc', compute='_compute_is_outside_hours', store=True)
    reminder_sent = fields.Boolean(string='Đã gửi nhắc nhở', default=False)
    
    _sql_constraints = [
        ('check_time', 'CHECK(end_datetime > start_datetime)', 'Thời gian kết thúc phải sau thời gian bắt đầu!'),
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_booking', _('New')) == _('New'):
            vals['ma_booking'] = self.env['ir.sequence'].next_by_code('dat.phong.hop') or _('New')
        record = super(DatPhongHop, self).create(vals)
        
        # Gửi email thông báo tạo booking
        record._send_booking_email('created')
        
        # Gửi bus notification
        record._notify_dashboard_update()
        
        return record
    
    def write(self, vals):
        # Track changes for email notifications
        old_states = {r.id: r.state for r in self}
        old_check_in = {r.id: r.check_in_time for r in self}
        old_check_out = {r.id: r.check_out_time for r in self}
        old_start = {r.id: r.start_datetime for r in self}
        old_end = {r.id: r.end_datetime for r in self}
        old_phong = {r.id: r.phong_hop_id.id for r in self}
        
        result = super(DatPhongHop, self).write(vals)
        
        # Send email notifications based on changes
        for record in self:
            if 'state' in vals and old_states.get(record.id) != record.state:
                if record.state == 'approved':
                    record._send_booking_email('created')
                elif record.state == 'cancelled':
                    record._send_booking_email('cancelled')
                elif record.state == 'checked_in':
                    record._send_booking_email('checkin')
            
            if 'check_in_time' in vals and not old_check_in.get(record.id) and record.check_in_time:
                record._send_booking_email('checkin')
            
            if 'start_datetime' in vals or 'end_datetime' in vals:
                if old_start.get(record.id) != record.start_datetime or old_end.get(record.id) != record.end_datetime:
                    record._send_booking_email('time_changed')
            
            if 'phong_hop_id' in vals and old_phong.get(record.id) != record.phong_hop_id.id:
                record._send_booking_email('room_changed')
        
        # Gửi bus notification
        self._notify_dashboard_update()
        
        return result
    
    def _notify_dashboard_update(self):
        """Gửi bus notification để dashboard cập nhật real-time"""
        try:
            self.env['bus.bus']._sendone(
                'dashboard_phong_hop',
                'dashboard_phong_hop/update',
                {
                    'message': 'Dashboard update required',
                    'timestamp': fields.Datetime.now().isoformat()
                }
            )
        except Exception as e:
            _logger.warning("Error sending dashboard update notification: %s", str(e))
    
    def _send_booking_email(self, email_type):
        """Gửi email thông báo về booking"""
        self.ensure_one()
        try:
            template_xmlid_map = {
                'created': 'quan_ly_phong_hop.email_template_booking_created',
                'checkin': 'quan_ly_phong_hop.email_template_booking_checkin',
                'cancelled': 'quan_ly_phong_hop.email_template_booking_cancelled',
                'reminder': 'quan_ly_phong_hop.email_template_booking_reminder',
                'time_changed': 'quan_ly_phong_hop.email_template_booking_time_changed',
                'room_changed': 'quan_ly_phong_hop.email_template_booking_room_changed',
            }
            template_xmlid = template_xmlid_map.get(email_type)
            if not template_xmlid:
                _logger.warning("Unknown email type: %s", email_type)
                return
            
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                # Gửi email đến admin
                template.with_context(email_to=ADMIN_EMAIL).send_mail(self.id, force_send=True)
                
                # Gửi email đến host nếu có email
                if self.host_id and self.host_id.email:
                    template.send_mail(self.id, force_send=True)
                
                _logger.info("Sent %s email for booking %s", email_type, self.ma_booking)
            else:
                _logger.warning("Email template %s not found", template_xmlid)
        except Exception as e:
            _logger.error("Error sending booking email (%s): %s", email_type, str(e))
    
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                rec.duration_minutes = int(delta.total_seconds() / 60)
            else:
                rec.duration_minutes = 0
    
    @api.depends('end_datetime', 'phong_hop_id')
    def _compute_auto_release_time(self):
        for rec in self:
            if rec.end_datetime and rec.phong_hop_id:
                buffer_minutes = rec.phong_hop_id.buffer_time_after or 15
                rec.auto_release_time = rec.end_datetime + timedelta(minutes=buffer_minutes)
            else:
                rec.auto_release_time = False
    
    @api.depends('chuc_vu_tham_du_ids', 'phong_ban_tham_du_ids')
    def _compute_attendee_ids(self):
        for rec in self:
            attendee_ids = []
            # Thêm host
            if rec.host_id:
                attendee_ids.append(rec.host_id.id)
            
            # Thêm nhân viên theo chức vụ
            if rec.chuc_vu_tham_du_ids:
                nhan_viens = self.env['nhan_vien'].search([('chuc_vu_id', 'in', rec.chuc_vu_tham_du_ids.ids)])
                attendee_ids.extend(nhan_viens.ids)
            
            # Thêm nhân viên theo phòng ban
            if rec.phong_ban_tham_du_ids:
                nhan_viens = self.env['nhan_vien'].search([('phong_ban_id', 'in', rec.phong_ban_tham_du_ids.ids)])
                attendee_ids.extend(nhan_viens.ids)
            
            rec.attendee_ids = [(6, 0, list(set(attendee_ids)))]
    
    @api.depends('attendee_ids')
    def _compute_so_nguoi_tham_du(self):
        for rec in self:
            rec.so_nguoi_tham_du = len(rec.attendee_ids)
    
    @api.depends('dich_vu_ids', 'dich_vu_ids.loai_dich_vu')
    def _compute_co_catering(self):
        for rec in self:
            rec.co_catering = any(dv.loai_dich_vu == 'catering' for dv in rec.dich_vu_ids)
    
    @api.depends('dich_vu_ids', 'dich_vu_ids.chi_phi')
    def _compute_tong_chi_phi(self):
        for rec in self:
            rec.tong_chi_phi = sum(rec.dich_vu_ids.mapped('chi_phi'))
    
    @api.depends('start_datetime', 'phong_hop_id')
    def _compute_is_outside_hours(self):
        for rec in self:
            if rec.start_datetime and rec.phong_hop_id and not rec.phong_hop_id.hoat_dong_ca_ngay:
                hour = rec.start_datetime.hour + rec.start_datetime.minute / 60.0
                rec.is_outside_hours = hour < rec.phong_hop_id.gio_bat_dau or hour >= rec.phong_hop_id.gio_ket_thuc
            else:
                rec.is_outside_hours = False
    
    @api.depends('phong_hop_id', 'start_datetime', 'end_datetime', 'state')
    def _compute_can_approval(self):
        for rec in self:
            rec.can_approval = rec.is_outside_hours or rec.state == 'pending_approval'
    
    @api.depends('ma_booking', 'name')
    def _compute_qr_code(self):
        for rec in self:
            rec.qr_code = f"BOOKING-{rec.ma_booking}"
    
    @api.constrains('start_datetime', 'end_datetime', 'phong_hop_id')
    def _check_booking_conflict(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime and rec.phong_hop_id:
                conflicts = self.search([
                    ('phong_hop_id', '=', rec.phong_hop_id.id),
                    ('id', '!=', rec.id),
                    ('state', 'not in', ['cancelled', 'no_show', 'done']),
                    ('start_datetime', '<', rec.end_datetime),
                    ('end_datetime', '>', rec.start_datetime)
                ])
                if conflicts:
                    raise ValidationError(_('Phòng đã được đặt trong khoảng thời gian này!'))
    
    def action_submit(self):
        """Gửi yêu cầu đặt phòng"""
        for rec in self:
            if rec.can_approval:
                rec.state = 'pending_approval'
            else:
                rec.state = 'approved'
                rec._send_booking_email('created')
    
    def action_approve(self):
        """Duyệt booking"""
        for rec in self:
            rec.state = 'approved'
            rec.approver_id = self.env.user
            rec.approval_date = fields.Datetime.now()
            rec._send_booking_email('created')
    
    def action_reject(self):
        """Từ chối booking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lý do từ chối',
            'res_model': 'wizard.reject.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id}
        }
    
    def action_check_in(self):
        """Check-in"""
        for rec in self:
            if rec.state in ['approved', 'confirmed']:
                rec.state = 'checked_in'
                rec.check_in_time = fields.Datetime.now()
                rec._send_booking_email('checkin')
    
    def action_start(self):
        """Bắt đầu cuộc họp"""
        for rec in self:
            if rec.state == 'checked_in':
                rec.state = 'in_progress'
    
    def action_check_out(self):
        """Check-out"""
        for rec in self:
            if rec.state == 'in_progress':
                rec.state = 'done'
                rec.check_out_time = fields.Datetime.now()

    def action_create_multi_room_booking(self):
        """Đặt nhiều phòng cho cùng một cuộc họp.

        Hiện tại chỉ là hàm placeholder để hợp lệ hóa button trong view.
        TODO: triển khai logic tạo các booking phòng họp liên quan.
        """
        self.ensure_one()
        # Tạm thời chưa làm gì, chỉ trả về True để tránh lỗi view
        return True

    def action_extend_booking(self):
        """Gia hạn thời gian booking hiện tại.

        Hiện tại chỉ là hàm placeholder để hợp lệ hóa button trong view.
        TODO: triển khai logic kiểm tra xung đột và cập nhật end_datetime.
        """
        self.ensure_one()
        # Tạm thời chưa làm gì, chỉ trả về True để tránh lỗi view
        return True

    def action_suggest_rooms(self):
        """Gợi ý phòng phù hợp dựa trên thời gian, số người và thiết bị.

        Hiện tại chỉ là hàm placeholder để hợp lệ hóa button trong view.
        TODO: triển khai logic tìm phòng trống, đủ sức chứa và tiện ích.
        """
        self.ensure_one()
        return True

    def action_cancel(self):
        """Hủy booking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hủy booking',
            'res_model': 'wizard.cancel.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id}
        }
    
    @api.model
    def cron_send_booking_reminders(self):
        """Cron job gửi nhắc nhở booking"""
        try:
            now = fields.Datetime.now()
            reminder_start = now + timedelta(minutes=30)
            reminder_end = now + timedelta(minutes=60)
            
            bookings_to_remind = self.search([
                ('state', 'in', ['approved', 'confirmed']),
                ('start_datetime', '>=', reminder_start),
                ('start_datetime', '<=', reminder_end),
                ('reminder_sent', '=', False),
            ])
            
            for booking in bookings_to_remind:
                try:
                    booking._send_booking_email('reminder')
                    booking.write({'reminder_sent': True})
                except Exception as e:
                    _logger.error("Error sending reminder for booking %s: %s", booking.ma_booking, str(e))
            
            _logger.info("Sent reminders for %d bookings", len(bookings_to_remind))
        except Exception as e:
            _logger.error("Error in cron_send_booking_reminders: %s", str(e))
    
    @api.model
    def cron_check_no_show(self):
        """Cron job kiểm tra no-show"""
        try:
            now = fields.Datetime.now()
            # Kiểm tra các booking đã quá thời gian bắt đầu nhưng chưa check-in
            no_show_bookings = self.search([
                ('state', 'in', ['approved', 'confirmed']),
                ('start_datetime', '<', now - timedelta(minutes=15)),
                ('check_in_time', '=', False),
            ])
            
            for booking in no_show_bookings:
                booking.write({'state': 'no_show'})
                booking._send_booking_email('cancelled')
            
            _logger.info("Marked %d bookings as no-show", len(no_show_bookings))
        except Exception as e:
            _logger.error("Error in cron_check_no_show: %s", str(e))
