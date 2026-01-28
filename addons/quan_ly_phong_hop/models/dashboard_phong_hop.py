# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class DashboardPhongHop(models.TransientModel):
    _name = 'dashboard_phong_hop'
    _description = 'Dashboard phòng họp'
    
    # Thêm một field dummy để có thể tạo record
    name = fields.Char(string='Name', default='Dashboard', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Tự động tạo record khi mở dashboard"""
        res = super(DashboardPhongHop, self).default_get(fields_list)
        res['name'] = 'Dashboard'
        return res
    
    @api.model
    def _auto_init(self):
        """Xóa view cũ nếu có trước khi tạo table mới"""
        cr = self.env.cr
        # Kiểm tra và xóa view cũ nếu có
        cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_views 
                WHERE viewname = 'dashboard_phong_hop'
            )
        """)
        if cr.fetchone()[0]:
            cr.execute('DROP VIEW IF EXISTS dashboard_phong_hop CASCADE')
        # Kiểm tra và xóa table cũ nếu có (từ lần trước)
        cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'dashboard_phong_hop'
            )
        """)
        if cr.fetchone()[0]:
            cr.execute('DROP TABLE IF EXISTS dashboard_phong_hop CASCADE')
        return super(DashboardPhongHop, self)._auto_init()
    
    @api.model
    def name_get(self):
        return [(record.id, "Dashboard") for record in self]
    
    @api.model
    def get_filter_options(self):
        """Lấy danh sách các options cho bộ lọc"""
        try:
            # Lấy danh sách địa điểm
            locations = self.env['tai_san.location'].search([
                ('location_type', 'in', ['site', 'building', 'floor', 'room'])
            ])
            location_options = [{'id': loc.id, 'name': loc.name} for loc in locations]
            
            # Lấy danh sách phòng ban từ nhansu
            phong_ban_list = []
            try:
                phong_bans = self.env['phong_ban'].search([('trang_thai', '=', 'hoat_dong')])
                phong_ban_list = [{'id': pb.id, 'name': pb.ten_phong_ban or pb.ma_phong_ban} for pb in phong_bans]
            except Exception as e:
                _logger.warning("Error loading phong_ban: %s", str(e))
            
            # Lấy danh sách chức vụ từ nhansu
            chuc_vu_list = []
            try:
                chuc_vus = self.env['chuc_vu'].search([])
                chuc_vu_list = [{'id': cv.id, 'name': cv.ten_chuc_vu or cv.ma_chuc_vu} for cv in chuc_vus]
            except Exception as e:
                _logger.warning("Error loading chuc_vu: %s", str(e))
            
            return {
                'locations': location_options,
                'phong_bans': phong_ban_list,
                'chuc_vus': chuc_vu_list
            }
        except Exception as e:
            _logger.error("Error getting filter options: %s", str(e))
            return {
                'locations': [],
                'phong_bans': [],
                'chuc_vus': []
            }
    
    @api.model
    def _normalize_filters(self, filters):
        """Chuẩn hóa filter: chuyển string từ JS sang int"""
        if not filters:
            return {}
        out = dict(filters)
        for key in ('location_id', 'phong_ban_id', 'chuc_vu_id'):
            val = out.get(key)
            if val is None or val == '' or val is False:
                out[key] = None
            else:
                try:
                    out[key] = int(val) if not isinstance(val, int) else val
                except (TypeError, ValueError):
                    out[key] = None
        return out

    @api.model
    def get_dashboard_data(self, filters=None):
        """Lấy dữ liệu cho dashboard với các KPI và phân tích nâng cao"""
        filters = self._normalize_filters(filters or {})
        _logger.info("=== Dashboard get_dashboard_data called ===")
        _logger.info("Filters: %s", filters)
        try:
            now = fields.Datetime.now()
            today = fields.Date.today()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Áp dụng filters cho phòng họp
            domain = []
            if filters.get('location_id'):
                domain.append(('location_id', '=', filters['location_id']))
            
            # Áp dụng filters cho booking (phòng ban, chức vụ)
            booking_domain = []
            if filters.get('phong_ban_id'):
                # Lấy danh sách nhân viên thuộc phòng ban này
                nhan_vien_ids = self.env['nhan_vien'].search([
                    ('phong_ban_id', '=', filters['phong_ban_id']),
                    ('trang_thai', '=', 'dang_lam_viec')
                ]).ids
                if nhan_vien_ids:
                    booking_domain.append(('host_id', 'in', nhan_vien_ids))
                else:
                    # Nếu không có nhân viên nào, không có booking nào
                    booking_domain.append(('id', '=', False))
            
            if filters.get('chuc_vu_id'):
                # Lấy danh sách nhân viên có chức vụ này
                nhan_vien_ids = self.env['nhan_vien'].search([
                    ('chuc_vu_id', '=', filters['chuc_vu_id']),
                    ('trang_thai', '=', 'dang_lam_viec')
                ]).ids
                if nhan_vien_ids:
                    if filters.get('phong_ban_id'):
                        # Nếu đã có filter phòng ban, lấy giao của 2 danh sách
                        phong_ban_nv_ids = self.env['nhan_vien'].search([
                            ('phong_ban_id', '=', filters['phong_ban_id']),
                            ('trang_thai', '=', 'dang_lam_viec')
                        ]).ids
                        nhan_vien_ids = list(set(nhan_vien_ids) & set(phong_ban_nv_ids))
                    booking_domain.append(('host_id', 'in', nhan_vien_ids))
                else:
                    # Nếu không có nhân viên nào, không có booking nào
                    booking_domain.append(('id', '=', False))
            
            # ========== 1. KPI CHIẾN LƯỢC ==========
            # Khởi tạo tất cả các biến để tránh lỗi UnboundLocalError
            total_phong = 0
            meetings_today = 0
            meetings_week = 0
            total_hours = 0.0
            phong_dang_co_booking = 0
            ty_le_su_dung = 0
            ty_le_lang_phi = 0
            ty_le_huy = 0
            ty_le_no_show = 0
            phong_bao_tri = 0
            phong_trong = 0
            heatmap_data = []
            hours = []
            dept_performance = []
            quality_stats = {}
            asset_health = []
            recent_activities = []
            upcoming_data = []
            ending_data = []
            usage_by_day = []
            top_rooms_data = []
            phong_dang_hop_data = []
            cuoc_hop_sap_bat_dau_data = []
            warnings = []
            phong_trong_data = []
            
            _logger.info("Getting total_phong...")
            try:
                total_phong = self.env['phong_hop'].search_count(domain)
                _logger.info("total_phong: %s", total_phong)
            except Exception as e:
                _logger.error("Error getting total_phong: %s", str(e))
                total_phong = 0
            
            # Cuộc họp hôm nay (áp dụng filter)
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            meetings_today_domain = [
                ('start_datetime', '>=', today_start),
                ('start_datetime', '<=', today_end),
                ('state', '!=', 'cancelled')
            ] + booking_domain
            meetings_today = self.env['dat_phong_hop'].search_count(meetings_today_domain)
            
            # Cuộc họp tuần này (áp dụng filter)
            week_start_dt = datetime.combine(week_start, datetime.min.time())
            week_end_dt = week_start_dt + timedelta(days=7)
            meetings_week_domain = [
                ('start_datetime', '>=', week_start_dt),
                ('start_datetime', '<', week_end_dt),
                ('state', '!=', 'cancelled')
            ] + booking_domain
            meetings_week = self.env['dat_phong_hop'].search_count(meetings_week_domain)
            
            # Tổng giờ sử dụng phòng (tháng này) (áp dụng filter)
            month_start_dt = datetime.combine(month_start, datetime.min.time())
            bookings_month_domain = [
                ('start_datetime', '>=', month_start_dt),
                ('state', 'in', ['confirmed', 'checked_in', 'in_progress', 'done'])
            ] + booking_domain
            bookings_month = self.env['dat_phong_hop'].search(bookings_month_domain)
            total_hours = 0.0
            for b in bookings_month:
                try:
                    if b.start_datetime and b.end_datetime:
                        duration = (b.end_datetime - b.start_datetime).total_seconds() / 3600
                        total_hours += duration
                except:
                    continue
            
            # Tỷ lệ sử dụng phòng (%) (áp dụng filter)
            phong_dang_co_booking_domain = [
                ('state', 'in', ['confirmed', 'checked_in', 'in_progress']),
                ('start_datetime', '<=', now),
                ('end_datetime', '>=', now)
            ] + booking_domain
            phong_dang_co_booking_ids = self.env['dat_phong_hop'].search(phong_dang_co_booking_domain).mapped('phong_hop_id')
            phong_dang_co_booking = len(set(phong_dang_co_booking_ids.ids))
            ty_le_su_dung = (phong_dang_co_booking / total_phong * 100) if total_phong > 0 else 0
            
            # Tỷ lệ phòng bị lãng phí (<30% sử dụng)
            phong_lang_phi = 0
            for room in self.env['phong_hop'].search(domain):
                if room.ty_le_su_dung < 30:
                    phong_lang_phi += 1
            ty_le_lang_phi = (phong_lang_phi / total_phong * 100) if total_phong > 0 else 0
            
            # Tỷ lệ hủy phòng (áp dụng filter)
            cancelled_domain = [
                ('state', '=', 'cancelled'),
                ('start_datetime', '>=', month_start_dt)
            ] + booking_domain
            cancelled_count = self.env['dat_phong_hop'].search_count(cancelled_domain)
            total_bookings_domain = [
                ('start_datetime', '>=', month_start_dt)
            ] + booking_domain
            total_bookings_month = self.env['dat_phong_hop'].search_count(total_bookings_domain)
            ty_le_huy = (cancelled_count / total_bookings_month * 100) if total_bookings_month > 0 else 0
            
            # Tỷ lệ không check-in (no-show) (áp dụng filter)
            no_show_domain = [
                ('state', '=', 'no_show'),
                ('start_datetime', '>=', month_start_dt)
            ] + booking_domain
            no_show_count = self.env['dat_phong_hop'].search_count(no_show_domain)
            ty_le_no_show = (no_show_count / total_bookings_month * 100) if total_bookings_month > 0 else 0
            
            # ========== 2. HEATMAP SỬ DỤNG PHÒNG ==========
            # Heatmap: Giờ (X) x Phòng (Y)
            heatmap_data = []
            rooms = self.env['phong_hop'].search(domain)
            hours = list(range(8, 19))  # 8h-18h
            
            for room in rooms:
                room_data = {'room': room.ten_phong or room.ma_phong or 'Unknown', 'hours': {}}
                for hour in hours:
                    try:
                        # Đếm số booking trong giờ này (tháng này)
                        hour_start = datetime.combine(today, datetime.min.time().replace(hour=hour))
                        hour_end = hour_start + timedelta(hours=1)
                        heatmap_hour_domain = [
                            ('phong_hop_id', '=', room.id),
                            ('start_datetime', '>=', month_start_dt),
                            ('start_datetime', '<', hour_end),
                            ('end_datetime', '>', hour_start),
                            ('state', 'in', ['confirmed', 'checked_in', 'in_progress', 'done'])
                        ] + booking_domain
                        bookings_in_hour = self.env['dat_phong_hop'].search_count(heatmap_hour_domain)
                        # Tính tỷ lệ (số ngày trong tháng)
                        days_in_month = (today - month_start).days + 1
                        usage_rate = (bookings_in_hour / days_in_month * 100) if days_in_month > 0 else 0
                        room_data['hours'][hour] = min(usage_rate, 100)
                    except Exception as e:
                        room_data['hours'][hour] = 0
                heatmap_data.append(room_data)
            
            # ========== 3. HIỆU SUẤT THEO PHÒNG BAN ==========
            dept_stats = defaultdict(lambda: {'bookings': 0, 'cancelled': 0, 'no_show': 0})
            bookings_with_dept_domain = [
                ('start_datetime', '>=', month_start_dt),
                ('host_id.phong_ban_id', '!=', False)
            ] + booking_domain
            bookings_with_dept = self.env['dat_phong_hop'].search(bookings_with_dept_domain)
            
            for booking in bookings_with_dept:
                try:
                    if booking.host_id and booking.host_id.phong_ban_id:
                        dept_name = booking.host_id.phong_ban_id.ten_phong_ban or booking.host_id.phong_ban_id.ma_phong_ban or 'Unknown'
                        dept_stats[dept_name]['bookings'] += 1
                        if booking.state == 'cancelled':
                            dept_stats[dept_name]['cancelled'] += 1
                        if booking.state == 'no_show':
                            dept_stats[dept_name]['no_show'] += 1
                except:
                    continue
            
            dept_performance = []
            for dept_name, stats in dept_stats.items():
                dept_performance.append({
                    'name': dept_name,
                    'bookings': stats['bookings'],
                    'cancelled': stats['cancelled'],
                    'no_show': stats['no_show'],
                    'cancelled_rate': (stats['cancelled'] / stats['bookings'] * 100) if stats['bookings'] > 0 else 0
                })
            dept_performance.sort(key=lambda x: x['bookings'], reverse=True)
            
            # ========== 4. PHÂN TÍCH CHẤT LƯỢNG CUỘC HỌP ==========
            quality_stats = {
                'over_capacity': 0,  # Phòng quá lớn
                'under_capacity': 0,  # Phòng quá nhỏ
                'over_time': 0,  # Họp quá dài
                'on_time_end': 0  # Kết thúc đúng giờ
            }
            
            completed_bookings = self.env['dat_phong_hop'].search([
                ('state', '=', 'done'),
                ('start_datetime', '>=', month_start_dt)
            ])
            
            for booking in completed_bookings:
                try:
                    if booking.phong_hop_id and booking.so_nguoi_tham_du:
                        capacity = booking.phong_hop_id.suc_chua or 1
                        attendees = booking.so_nguoi_tham_du or 0
                        # Phòng quá lớn (>50% trống)
                        if attendees < capacity * 0.5:
                            quality_stats['over_capacity'] += 1
                        # Phòng quá nhỏ (>90% sức chứa)
                        elif attendees > capacity * 0.9:
                            quality_stats['under_capacity'] += 1
                        
                        # Kiểm tra thời lượng
                        if booking.start_datetime and booking.end_datetime:
                            duration = (booking.end_datetime - booking.start_datetime).total_seconds() / 3600
                            if duration > 3:  # Họp quá 3 giờ
                                quality_stats['over_time'] += 1
                            else:
                                quality_stats['on_time_end'] += 1
                except:
                    continue
            
            # ========== 5. TÌNH TRẠNG TÀI SẢN & PHÒNG ==========
            asset_health = []
            for room in rooms:
                try:
                    # Đếm số lần bảo trì
                    maintenance_count = self.env['bao_tri_phong_hop'].search_count([
                        ('phong_hop_id', '=', room.id),
                        ('ngay_bao_tri', '>=', month_start)
                    ])
                    
                    # Đếm tài sản có vấn đề
                    problematic_assets = self.env['tai_san_phong_hop'].search_count([
                        ('phong_hop_id', '=', room.id),
                        ('trang_thai', 'in', ['maintenance', 'damaged'])
                    ])
                    
                    asset_health.append({
                        'room': room.ten_phong or room.ma_phong or 'Unknown',
                        'maintenance_count': maintenance_count,
                        'problematic_assets': problematic_assets,
                        'total_assets': len(room.tai_san_trong_phong_ids) if room.tai_san_trong_phong_ids else 0
                    })
                except:
                    continue
            
            # ========== 6. HOẠT ĐỘNG GẦN ĐÂY ==========
            recent_activities = []
            
            # Bookings gần đây
            recent_bookings = self.env['dat_phong_hop'].search([
                ('create_date', '>=', now - timedelta(days=7))
            ], order='create_date desc', limit=20)
            
            for booking in recent_bookings:
                try:
                    recent_activities.append({
                        'type': 'booking',
                        'action': 'Đặt phòng' if booking.state != 'cancelled' else 'Hủy đặt phòng',
                        'room': booking.phong_hop_id.ten_phong if booking.phong_hop_id else '',
                        'user': booking.host_id.name if booking.host_id else '',
                        'time': booking.create_date.strftime('%d/%m/%Y %H:%M') if booking.create_date else '',
                        'details': booking.name or ''
                    })
                except:
                    continue
            
            # Bảo trì gần đây
            try:
                recent_maintenance = self.env['bao_tri_phong_hop'].search([
                    ('create_date', '>=', now - timedelta(days=7))
                ], order='create_date desc', limit=10)
                
                for maint in recent_maintenance:
                    try:
                        recent_activities.append({
                            'type': 'maintenance',
                            'action': 'Bảo trì phòng',
                            'room': maint.phong_hop_id.ten_phong if maint.phong_hop_id else '',
                            'user': maint.nguoi_thuc_hien_id.name if maint.nguoi_thuc_hien_id else '',
                            'time': maint.create_date.strftime('%d/%m/%Y %H:%M') if maint.create_date else '',
                            'details': maint.ghi_chu or ''
                        })
                    except:
                        continue
            except:
                pass
            
            recent_activities.sort(key=lambda x: x['time'], reverse=True)
            recent_activities = recent_activities[:20]
            
            # ========== 7. DỮ LIỆU CŨ (giữ lại để tương thích) ==========
            phong_bao_tri = self.env['phong_hop'].search_count(domain + [('state', '=', 'maintenance')])
            phong_trong = total_phong - phong_dang_co_booking - phong_bao_tri
            
            # Cuộc họp sắp diễn ra
            upcoming_meetings = self.env['dat_phong_hop'].search([
                ('state', 'in', ['approved', 'confirmed']),
                ('start_datetime', '>=', now),
                ('start_datetime', '<=', now + timedelta(hours=2))
            ], order='start_datetime asc', limit=10)
            
            upcoming_data = []
            for meeting in upcoming_meetings:
                try:
                    upcoming_data.append({
                        'id': meeting.id,
                        'name': meeting.name or '',
                        'phong': meeting.phong_hop_id.ten_phong if meeting.phong_hop_id else '',
                        'start_time': meeting.start_datetime.strftime('%H:%M') if meeting.start_datetime else '',
                        'host': meeting.host_id.name if meeting.host_id else '',
                    })
                except:
                    continue
            
            # Phòng sắp hết giờ
            ending_soon = self.env['dat_phong_hop'].search([
                ('state', 'in', ['in_progress', 'checked_in']),
                ('end_datetime', '>=', now),
                ('end_datetime', '<=', now + timedelta(minutes=30))
            ], order='end_datetime asc', limit=10)
            
            ending_data = []
            for meeting in ending_soon:
                try:
                    ending_data.append({
                        'id': meeting.id,
                        'name': meeting.name or '',
                        'phong': meeting.phong_hop_id.ten_phong if meeting.phong_hop_id else '',
                        'end_time': meeting.end_datetime.strftime('%H:%M') if meeting.end_datetime else '',
                    })
                except:
                    continue
            
            # Tỷ lệ sử dụng theo ngày (7 ngày gần nhất)
            usage_by_day = []
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                bookings = self.env['dat_phong_hop'].search([
                    ('start_datetime', '>=', datetime.combine(date, datetime.min.time())),
                    ('start_datetime', '<', datetime.combine(date + timedelta(days=1), datetime.min.time())),
                    ('state', 'in', ['confirmed', 'checked_in', 'in_progress', 'done'])
                ])
                total_minutes = 0
                for b in bookings:
                    try:
                        if b.start_datetime and b.end_datetime:
                            duration = int((b.end_datetime - b.start_datetime).total_seconds() / 60)
                            total_minutes += duration
                    except:
                        continue
                total_available = total_phong * 600 if total_phong > 0 else 1
                usage_rate = (total_minutes / total_available * 100) if total_available > 0 else 0
                usage_by_day.append({
                    'date': date.strftime('%d/%m'),
                    'usage': round(usage_rate, 1)
                })
            
            # Top phòng được dùng nhiều nhất
            top_rooms_data = []
            for room in rooms:
                try:
                    bookings_count = len(room.booking_ids.filtered(lambda b: b.state != 'cancelled'))
                    top_rooms_data.append({
                        'name': room.ten_phong or room.ma_phong or 'Unknown',
                        'count': bookings_count,
                        'usage_rate': room.ty_le_su_dung or 0
                    })
                except:
                    continue
            top_rooms_data.sort(key=lambda x: x['count'], reverse=True)
            top_rooms_data = top_rooms_data[:5]
            
            # ========== 8. REAL-TIME DATA ==========
            # Phòng đang họp ngay bây giờ (áp dụng filter)
            phong_dang_hop_domain = [
                ('state', 'in', ['checked_in', 'in_progress']),
                ('start_datetime', '<=', now),
                ('end_datetime', '>=', now)
            ] + booking_domain
            phong_dang_hop = self.env['dat_phong_hop'].search(phong_dang_hop_domain)
            phong_dang_hop_data = []
            for booking in phong_dang_hop:
                try:
                    phong_dang_hop_data.append({
                        'id': booking.id,
                        'name': booking.name or '',
                        'phong': booking.phong_hop_id.ten_phong if booking.phong_hop_id else '',
                        'host': booking.host_id.name if booking.host_id else '',
                        'start_time': booking.start_datetime.strftime('%H:%M') if booking.start_datetime else '',
                        'end_time': booking.end_datetime.strftime('%H:%M') if booking.end_datetime else '',
                        'so_nguoi': booking.so_nguoi_tham_du or 0
                    })
                except:
                    continue
            
            # Cuộc họp sắp bắt đầu (next 30-60 phút) (áp dụng filter)
            next_30min = now + timedelta(minutes=30)
            next_60min = now + timedelta(minutes=60)
            cuoc_hop_sap_bat_dau_domain = [
                ('state', 'in', ['approved', 'confirmed']),
                ('start_datetime', '>=', next_30min),
                ('start_datetime', '<=', next_60min)
            ] + booking_domain
            cuoc_hop_sap_bat_dau = self.env['dat_phong_hop'].search(cuoc_hop_sap_bat_dau_domain, order='start_datetime asc')
            cuoc_hop_sap_bat_dau_data = []
            for meeting in cuoc_hop_sap_bat_dau:
                try:
                    minutes_until = int((meeting.start_datetime - now).total_seconds() / 60)
                    cuoc_hop_sap_bat_dau_data.append({
                        'id': meeting.id,
                        'name': meeting.name or '',
                        'phong': meeting.phong_hop_id.ten_phong if meeting.phong_hop_id else '',
                        'host': meeting.host_id.name if meeting.host_id else '',
                        'start_time': meeting.start_datetime.strftime('%H:%M') if meeting.start_datetime else '',
                        'minutes_until': minutes_until
                    })
                except:
                    continue
            
            # ========== 9. CẢNH BÁO & RỦI RO ==========
            warnings = []
            
            # No-show risk: Cuộc họp đã đến giờ nhưng chưa check-in
            no_show_risk = self.env['dat_phong_hop'].search([
                ('state', 'in', ['approved', 'confirmed']),
                ('start_datetime', '<=', now),
                ('start_datetime', '>=', now - timedelta(minutes=30)),
                ('check_in_time', '=', False)
            ])
            for booking in no_show_risk:
                try:
                    warnings.append({
                        'type': 'no_show_risk',
                        'severity': 'warning',
                        'title': 'Nguy cơ No-show',
                        'message': f"Cuộc họp '{booking.name}' tại {booking.phong_hop_id.ten_phong if booking.phong_hop_id else ''} đã đến giờ nhưng chưa check-in",
                        'booking_id': booking.id,
                        'phong': booking.phong_hop_id.ten_phong if booking.phong_hop_id else ''
                    })
                except:
                    continue
            
            # Overbook attempt: Phòng có booking trùng lịch (nếu có lỗi)
            # Kiểm tra phòng có booking trong quá khứ chưa kết thúc
            for room in rooms:
                try:
                    active_bookings = self.env['dat_phong_hop'].search([
                        ('phong_hop_id', '=', room.id),
                        ('state', 'not in', ['cancelled', 'rejected', 'no_show', 'done']),
                        ('start_datetime', '<=', now),
                        ('end_datetime', '>=', now)
                    ])
                    if len(active_bookings) > 1:
                        warnings.append({
                            'type': 'overbook',
                            'severity': 'danger',
                            'title': 'Phòng bị đặt trùng',
                            'message': f"Phòng {room.ten_phong or room.ma_phong} có {len(active_bookings)} booking đang diễn ra cùng lúc",
                            'phong': room.ten_phong or room.ma_phong,
                            'room_id': room.id
                        })
                except:
                    continue
            
            # Thiếu thiết bị: Booking yêu cầu thiết bị nhưng phòng không có
            bookings_with_equipment_req = self.env['dat_phong_hop'].search([
                ('state', 'in', ['approved', 'confirmed', 'checked_in']),
                ('start_datetime', '>=', now),
                ('start_datetime', '<=', now + timedelta(days=1))
            ])
            for booking in bookings_with_equipment_req:
                try:
                    if booking.dich_vu_ids:
                        missing_equipment = []
                        room = booking.phong_hop_id
                        if room:
                            for dv in booking.dich_vu_ids:
                                if dv.loai_dich_vu == 'it_support' and dv.yeu_cau_hoi_online:
                                    if not room.co_vc_device:
                                        missing_equipment.append('VC device')
                                    if not room.co_camera:
                                        missing_equipment.append('Camera')
                                    if not room.co_micro:
                                        missing_equipment.append('Micro')
                                elif dv.loai_dich_vu == 'equipment':
                                    # Kiểm tra thiết bị mượn
                                    if dv.ten_thiet_bi and not room.tai_san_trong_phong_ids.filtered(lambda t: dv.ten_thiet_bi.lower() in (t.ten_tai_san or '').lower()):
                                        missing_equipment.append(dv.ten_thiet_bi)
                        
                        if missing_equipment:
                            warnings.append({
                                'type': 'missing_equipment',
                                'severity': 'warning',
                                'title': 'Thiếu thiết bị',
                                'message': f"Cuộc họp '{booking.name}' tại {room.ten_phong if room else ''} thiếu: {', '.join(missing_equipment)}",
                                'booking_id': booking.id,
                                'phong': room.ten_phong if room else ''
                            })
                except:
                    continue
            
            # Phòng hỏng nhưng vẫn có booking tương lai
            phong_hong_co_booking = self.env['phong_hop'].search([
                ('state', 'in', ['maintenance', 'out_of_service'])
            ])
            for room in phong_hong_co_booking:
                try:
                    future_bookings = self.env['dat_phong_hop'].search([
                        ('phong_hop_id', '=', room.id),
                        ('state', 'in', ['approved', 'confirmed']),
                        ('start_datetime', '>', now)
                    ], limit=5)
                    if future_bookings:
                        warnings.append({
                            'type': 'room_maintenance_with_booking',
                            'severity': 'danger',
                            'title': 'Phòng bảo trì có booking',
                            'message': f"Phòng {room.ten_phong or room.ma_phong} đang bảo trì nhưng có {len(future_bookings)} booking tương lai",
                            'phong': room.ten_phong or room.ma_phong,
                            'room_id': room.id,
                            'booking_count': len(future_bookings)
                        })
                except:
                    continue
            
            # ========== 10. PHÒNG TRỐNG SẴN SÀNG (cho quick booking) ==========
            phong_trong_san_sang = self.env['phong_hop'].search([
                ('state', '=', 'available')
            ])
            phong_trong_data = []
            for room in phong_trong_san_sang:
                try:
                    # Kiểm tra phòng có đang được sử dụng không
                    current_booking = self.env['dat_phong_hop'].search([
                        ('phong_hop_id', '=', room.id),
                        ('state', 'in', ['checked_in', 'in_progress']),
                        ('start_datetime', '<=', now),
                        ('end_datetime', '>=', now)
                    ], limit=1)
                    if not current_booking:
                        phong_trong_data.append({
                            'id': room.id,
                            'name': room.ten_phong or room.ma_phong or '',
                            'suc_chua': room.suc_chua or 0,
                            'location': room.location_id.name if room.location_id else ''
                        })
                except:
                    continue
            
            result = {
                # KPI cơ bản
                'total_phong': total_phong,
                'phong_dang_su_dung': phong_dang_co_booking,
                'phong_trong': phong_trong,
                'phong_bao_tri': phong_bao_tri,
                
                # KPI chiến lược
                'meetings_today': meetings_today,
                'meetings_week': meetings_week,
                'total_hours': round(total_hours, 1),
                'ty_le_su_dung': round(ty_le_su_dung, 1),
                'ty_le_lang_phi': round(ty_le_lang_phi, 1),
                'ty_le_huy': round(ty_le_huy, 1),
                'ty_le_no_show': round(ty_le_no_show, 1),
                
                # Heatmap
                'heatmap_data': heatmap_data,
                'heatmap_hours': hours,
                
                # Hiệu suất phòng ban
                'dept_performance': dept_performance[:10] if dept_performance else [],
                
                # Chất lượng cuộc họp
                'quality_stats': quality_stats,
                
                # Tình trạng tài sản
                'asset_health': asset_health[:10] if asset_health else [],
                
                # Hoạt động gần đây
                'recent_activities': recent_activities,
                
                # Dữ liệu cũ (tương thích)
                'upcoming_meetings': upcoming_data,
                'ending_soon': ending_data,
                'usage_by_day': usage_by_day,
                'top_rooms': top_rooms_data,
                
                # Real-time data
                'phong_dang_hop': phong_dang_hop_data,
                'cuoc_hop_sap_bat_dau': cuoc_hop_sap_bat_dau_data,
                
                # Cảnh báo & rủi ro
                'warnings': warnings,
                
                # Phòng trống sẵn sàng (quick booking)
                'phong_trong_san_sang': phong_trong_data[:10] if phong_trong_data else [],  # Top 10 phòng trống
            }
            _logger.info("=== Dashboard data prepared successfully ===")
            _logger.info("total_phong: %s, meetings_today: %s", total_phong, meetings_today)
            return result
        except Exception as e:
            import traceback
            _logger.error("=== Dashboard get_dashboard_data ERROR ===")
            _logger.error("Error: %s", str(e))
            _logger.error("Traceback: %s", traceback.format_exc())
            return {
                'total_phong': 0,
                'phong_dang_su_dung': 0,
                'phong_trong': 0,
                'phong_bao_tri': 0,
                'meetings_today': 0,
                'meetings_week': 0,
                'total_hours': 0,
                'ty_le_su_dung': 0,
                'ty_le_lang_phi': 0,
                'ty_le_huy': 0,
                'ty_le_no_show': 0,
                'heatmap_data': [],
                'heatmap_hours': [],
                'dept_performance': [],
                'quality_stats': {},
                'asset_health': [],
                'recent_activities': [],
                'upcoming_meetings': [],
                'ending_soon': [],
                'usage_by_day': [],
                'top_rooms': [],
                'error': str(e),
                'traceback': traceback.format_exc(),
                'warnings': [],
                'phong_dang_hop': [],
                'cuoc_hop_sap_bat_dau': [],
                'phong_trong_san_sang': []
            }
    
    @api.model
    def quick_checkin(self, booking_id):
        """Quick action: Check-in hộ (admin)"""
        try:
            booking = self.env['dat_phong_hop'].browse(booking_id)
            if booking.exists():
                if booking.state in ['approved', 'confirmed']:
                    booking.action_check_in()
                    return {'success': True, 'message': f'Đã check-in cho cuộc họp "{booking.name}"'}
                return {'success': False, 'message': 'Trạng thái booking không hợp lệ'}
            return {'success': False, 'message': 'Không tìm thấy booking'}
        except Exception as e:
            import traceback
            return {'success': False, 'message': f'Lỗi: {str(e)}'}
    
    @api.model
    def quick_end_early(self, booking_id):
        """Quick action: Kết thúc sớm cuộc họp"""
        try:
            booking = self.env['dat_phong_hop'].browse(booking_id)
            if booking.exists():
                if booking.state in ['checked_in', 'in_progress']:
                    booking.action_check_out()
                    return {'success': True, 'message': f'Đã kết thúc cuộc họp "{booking.name}"'}
                return {'success': False, 'message': 'Cuộc họp chưa bắt đầu'}
            return {'success': False, 'message': 'Không tìm thấy booking'}
        except Exception as e:
            return {'success': False, 'message': f'Lỗi: {str(e)}'}
    
    @api.model
    def quick_unlock_room(self, room_id):
        """Quick action: Mở khóa phòng sau bảo trì"""
        try:
            room = self.env['phong_hop'].browse(room_id)
            if room.exists():
                if room.state in ['maintenance', 'out_of_service']:
                    room.write({'state': 'available'})
                    return {'success': True, 'message': f'Đã mở khóa phòng "{room.ten_phong or room.ma_phong}"'}
                return {'success': False, 'message': 'Phòng không ở trạng thái bảo trì'}
            return {'success': False, 'message': 'Không tìm thấy phòng'}
        except Exception as e:
            return {'success': False, 'message': f'Lỗi: {str(e)}'}
    
    @api.model
    def quick_book_room(self, room_id, start_time, end_time, name, host_id):
        """Quick action: Đặt nhanh phòng trống"""
        try:
            room = self.env['phong_hop'].browse(room_id)
            if not room.exists():
                return {'success': False, 'message': 'Không tìm thấy phòng'}
            
            # Kiểm tra phòng có trống không
            overlapping = self.env['dat_phong_hop'].search([
                ('phong_hop_id', '=', room_id),
                ('state', 'not in', ['cancelled', 'rejected', 'no_show', 'done']),
                ('start_datetime', '<', end_time),
                ('end_datetime', '>', start_time)
            ])
            if overlapping:
                return {'success': False, 'message': 'Phòng đã được đặt trong khoảng thời gian này'}
            
            # Tạo booking
            booking = self.env['dat_phong_hop'].create({
                'name': name or 'Đặt nhanh từ Dashboard',
                'phong_hop_id': room_id,
                'start_datetime': start_time,
                'end_datetime': end_time,
                'host_id': host_id,
                'muc_dich': 'Đặt nhanh từ Dashboard',
                'state': 'confirmed'  # Tự động confirm cho quick booking
            })
            
            return {
                'success': True,
                'message': f'Đã đặt phòng "{room.ten_phong or room.ma_phong}" thành công',
                'booking_id': booking.id
            }
        except Exception as e:
            import traceback
            return {'success': False, 'message': f'Lỗi: {str(e)}'}
