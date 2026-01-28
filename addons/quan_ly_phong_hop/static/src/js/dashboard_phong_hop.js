odoo.define('quan_ly_phong_hop.dashboard_phong_hop', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');
    var core = require('web.core');

    var DashboardPhongHopController = FormController.extend({
        start: function () {
            const self = this;
            return this._super.apply(this, arguments).then(function() {
                self.$el.addClass('o_dashboard_view');
                // Setup filters
                self._setupFilters();
                // Đợi Chart.js và DOM sẵn sàng, đồng thời đảm bảo data đã được load
                Promise.all([
                    self._waitForChartJS(),
                    self._ensureDataLoaded()
                ]).then(function() {
                    // Render dashboard sau khi DOM, Chart.js và data sẵn sàng
                    self._updateDashboard();
                    // Setup real-time updates (auto-refresh + bus)
                    self._setupRealTimeUpdates();
                });
            });
        },
        
        _setupRealTimeUpdates: function() {
            const self = this;
            
            // Auto-refresh mỗi 30 giây
            self.autoRefreshInterval = setInterval(function() {
                if (!document.hidden) {
                    self._refreshDashboard();
                }
            }, 30000);
            
            // Refresh khi user quay lại tab
            self.visibilityChangeHandler = function() {
                if (!document.hidden) {
                    self._refreshDashboard();
                }
            };
            document.addEventListener('visibilitychange', self.visibilityChangeHandler);
            
            self._addRefreshIndicator();
            self._addManualRefreshButton();
        },
        
        _refreshDashboard: function() {
            const self = this;
            if (self._isRefreshing) {
                console.log('Dashboard refresh already in progress, skipping...');
                return;
            }
            
            self._isRefreshing = true;
            self._showRefreshIndicator(true);
            
            this._loadDashboardData().then(function() {
                self._updateDashboard();
                self._isRefreshing = false;
                self._showRefreshIndicator(false);
                console.log('Dashboard refreshed successfully');
            }).catch(function(error) {
                console.error('Error refreshing dashboard:', error);
                self._isRefreshing = false;
                self._showRefreshIndicator(false);
            });
        },
        
        _addRefreshIndicator: function() {
            const self = this;
            // Thêm indicator vào header của dashboard
            const $header = this.$('.o_form_view .o_form_sheet .oe_title');
            if ($header.length) {
                self.$refreshIndicator = $('<span class="dashboard-refresh-indicator" style="margin-left: 10px; font-size: 12px; color: #666;"><i class="fa fa-refresh fa-spin" style="display: none;"></i> <span class="refresh-text"></span></span>');
                $header.append(self.$refreshIndicator);
            } else {
                // Fallback: thêm vào đầu form
                self.$refreshIndicator = $('<div class="dashboard-refresh-indicator" style="text-align: right; padding: 5px; font-size: 12px; color: #666;"><i class="fa fa-refresh fa-spin" style="display: none;"></i> <span class="refresh-text"></span></div>');
                this.$('.o_form_view').prepend(self.$refreshIndicator);
            }
        },
        
        _addManualRefreshButton: function() {
            const self = this;
            // Thêm button refresh vào filter area
            const $filterArea = this.$('.dashboard-filters');
            if ($filterArea.length) {
                const $refreshBtn = $('<a href="#" class="btn btn-sm btn-secondary" role="button" id="btn_manual_refresh" style="margin-left: 10px;"><i class="fa fa-refresh"></i> Làm mới</a>');
                $filterArea.append($refreshBtn);
                $refreshBtn.on('click', function(e) {
                    e.preventDefault();
                    self._refreshDashboard();
                });
            }
        },
        
        _showRefreshIndicator: function(show) {
            const self = this;
            if (!self.$refreshIndicator) return;
            
            if (show) {
                self.$refreshIndicator.find('.fa-refresh').show();
                self.$refreshIndicator.find('.refresh-text').text('Đang cập nhật...');
            } else {
                self.$refreshIndicator.find('.fa-refresh').hide();
                const now = new Date();
                const timeStr = now.toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
                self.$refreshIndicator.find('.refresh-text').text('Cập nhật lúc ' + timeStr);
                // Ẩn text sau 5 giây
                setTimeout(function() {
                    if (self.$refreshIndicator) {
                        self.$refreshIndicator.find('.refresh-text').text('');
                    }
                }, 5000);
            }
        },
        
        destroy: function() {
            const self = this;
            // Cleanup auto-refresh interval
            if (self.autoRefreshInterval) {
                clearInterval(self.autoRefreshInterval);
                self.autoRefreshInterval = null;
            }
            
            // Remove visibility change listener
            if (self.visibilityChangeHandler) {
                document.removeEventListener('visibilitychange', self.visibilityChangeHandler);
            }
            
            return this._super.apply(this, arguments);
        },
        
        _ensureDataLoaded: function() {
            const self = this;
            return new Promise(function(resolve) {
                // Nếu data đã có, resolve ngay
                if (self.dashboardData && !self.dashboardData.error) {
                    console.log('Dashboard data already loaded');
                    resolve();
                    return;
                }
                
                // Nếu chưa có, đợi và retry
                let attempts = 0;
                const maxAttempts = 20; // 2 giây
                const checkInterval = setInterval(function() {
                    attempts++;
                    if (self.dashboardData && !self.dashboardData.error) {
                        console.log('Dashboard data loaded after', attempts * 100, 'ms');
                        clearInterval(checkInterval);
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        console.warn('Dashboard data not loaded after', maxAttempts * 100, 'ms');
                        clearInterval(checkInterval);
                        // Vẫn resolve để không block, nhưng sẽ hiển thị warning
                        if (!self.dashboardData) {
                            self.dashboardData = {
                                total_phong: 0,
                                phong_dang_su_dung: 0,
                                phong_trong: 0,
                                phong_bao_tri: 0,
                                meetings_today: 0,
                                meetings_week: 0,
                                total_hours: 0,
                                ty_le_su_dung: 0,
                                ty_le_lang_phi: 0,
                                ty_le_huy: 0,
                                ty_le_no_show: 0,
                                error: 'Data loading timeout'
                            };
                        }
                        resolve();
                    }
                }, 100);
            });
        },
        
        _waitForChartJS: function() {
            const self = this;
            return new Promise(function(resolve) {
                // Kiểm tra xem Chart.js đã load chưa
                if (typeof Chart !== 'undefined') {
                    console.log('Chart.js is ready');
                    resolve();
                } else {
                    console.log('Waiting for Chart.js...');
                    let attempts = 0;
                    const checkInterval = setInterval(function() {
                        attempts++;
                        if (typeof Chart !== 'undefined') {
                            console.log('Chart.js loaded after', attempts, 'attempts');
                            clearInterval(checkInterval);
                            resolve();
                        } else if (attempts > 50) { // Timeout sau 5 giây
                            console.error('Chart.js failed to load');
                            clearInterval(checkInterval);
                            resolve(); // Vẫn resolve để không block
                        }
                    }, 100);
                }
            });
        },
        
        init: function () {
            this._super.apply(this, arguments);
            this.usageChart = null;
            this.topRoomsChart = null;
            this.heatmapChart = null;
            this.deptPerformanceChart = null;
            this.qualityChart = null;
            this.filters = {};
            this.dashboardData = null;
        },

        willStart: function () {
            const self = this;
            // Load dashboard data song song với super
            return Promise.all([
                this._super.apply(this, arguments),
                this._loadDashboardData()
            ]).then(function() {
                // Đảm bảo data được load trước khi render
                console.log('willStart completed, dashboardData:', self.dashboardData);
                return Promise.resolve();
            });
        },

        _loadDashboardData: function () {
            const self = this;
            var filters = this.filters || {};
            // Đảm bảo args luôn là object (backend mong đợi dict)
            var args = [
                { location_id: filters.location_id || null, phong_ban_id: filters.phong_ban_id || null, chuc_vu_id: filters.chuc_vu_id || null, period: filters.period || 'month' }
            ];
            
            return this._rpc({
                model: 'dashboard_phong_hop',
                method: 'get_dashboard_data',
                args: args,
            }).then(function (data) {
                console.log('=== RPC call completed ===');
                console.log('Data received:', data);
                console.log('Data type:', typeof data);
                console.log('Data keys:', data ? Object.keys(data) : 'null/undefined');
                console.log('Total phong:', data ? data.total_phong : 'N/A');
                console.log('Meetings today:', data ? data.meetings_today : 'N/A');
                
                if (!data) {
                    console.error('Dashboard data is null or undefined!');
                    data = {
                        total_phong: 0,
                        error: 'No data returned from server'
                    };
                }
                
                self.dashboardData = data;
                console.log('Dashboard data assigned to self.dashboardData');
                
                // Nếu có lỗi trong data, log ra
                if (data.error) {
                    console.error('Dashboard data error:', data.error);
                    if (data.traceback) {
                        console.error('Traceback:', data.traceback);
                    }
                } else {
                    console.log('Dashboard data loaded successfully!');
                    console.log('Total phong:', data.total_phong);
                    console.log('Meetings today:', data.meetings_today);
                }
                
                return data;
            }).catch(function (error) {
                console.error('=== RPC call ERROR ===');
                console.error('Error loading dashboard data:', error);
                console.error('Error type:', typeof error);
                console.error('Error message:', error.message || error);
                console.error('Error details:', JSON.stringify(error));
                
                self.dashboardData = {
                    total_phong: 0,
                    phong_dang_su_dung: 0,
                    phong_trong: 0,
                    phong_bao_tri: 0,
                    meetings_today: 0,
                    meetings_week: 0,
                    total_hours: 0,
                    ty_le_su_dung: 0,
                    ty_le_lang_phi: 0,
                    ty_le_huy: 0,
                    ty_le_no_show: 0,
                    heatmap_data: [],
                    heatmap_hours: [],
                    dept_performance: [],
                    quality_stats: {},
                    asset_health: [],
                    recent_activities: [],
                    upcoming_meetings: [],
                    ending_soon: [],
                    usage_by_day: [],
                    top_rooms: [],
                    error: error.message || 'Unknown error'
                };
                console.log('Error data assigned to self.dashboardData');
                return self.dashboardData;
            });
        },

        renderButtons: function () {
            // Hide default buttons
            this.$buttons = $();
            return this.$buttons;
        },

        _update: function () {
            const self = this;
            return this._loadDashboardData().then(function () {
                self._updateDashboard();
            });
        },

        _setupFilters: function () {
            const self = this;
            
            // Load filter options khi khởi tạo
            self._loadFilterOptions();
            
            this.$('#btn_apply_filter').on('click', function() {
                var loc = self.$('#filter_location').val();
                var pb = self.$('#filter_department').val();
                var cv = self.$('#filter_chuc_vu').val();
                self.filters = {
                    location_id: loc ? parseInt(loc, 10) || false : false,
                    phong_ban_id: pb ? parseInt(pb, 10) || false : false,
                    chuc_vu_id: cv ? parseInt(cv, 10) || false : false,
                    period: (self.$('#filter_period').val() || 'month')
                };
                self._loadDashboardData().then(function() {
                    self._updateDashboard();
                });
            });
            
            this.$('#btn_reset_filter').on('click', function() {
                self.$('#filter_location').val('');
                self.$('#filter_department').val('');
                self.$('#filter_chuc_vu').val('');
                self.$('#filter_period').val('month');
                self.filters = {};
                self._loadDashboardData().then(function() {
                    self._updateDashboard();
                });
            });
        },
        
        _loadFilterOptions: function() {
            const self = this;
            return this._rpc({
                model: 'dashboard_phong_hop',
                method: 'get_filter_options',
                args: []
            }).then(function(options) {
                console.log('Filter options loaded:', options);
                
                // Populate location dropdown
                const $locationSelect = self.$('#filter_location');
                $locationSelect.empty();
                $locationSelect.append('<option value="">Tất cả</option>');
                if (options.locations && options.locations.length > 0) {
                    options.locations.forEach(function(loc) {
                        $locationSelect.append('<option value="' + loc.id + '">' + loc.name + '</option>');
                    });
                }
                
                // Populate phong ban dropdown
                const $phongBanSelect = self.$('#filter_department');
                $phongBanSelect.empty();
                $phongBanSelect.append('<option value="">Tất cả</option>');
                if (options.phong_bans && options.phong_bans.length > 0) {
                    options.phong_bans.forEach(function(pb) {
                        $phongBanSelect.append('<option value="' + pb.id + '">' + pb.name + '</option>');
                    });
                }
                
                // Populate chuc vu dropdown
                const $chucVuSelect = self.$('#filter_chuc_vu');
                $chucVuSelect.empty();
                $chucVuSelect.append('<option value="">Tất cả</option>');
                if (options.chuc_vus && options.chuc_vus.length > 0) {
                    options.chuc_vus.forEach(function(cv) {
                        $chucVuSelect.append('<option value="' + cv.id + '">' + cv.name + '</option>');
                    });
                }
            }).catch(function(error) {
                console.error('Error loading filter options:', error);
            });
        },

        _updateDashboard: function () {
            console.log('=== _updateDashboard called ===');
            console.log('dashboardData exists:', !!this.dashboardData);
            console.log('dashboardData:', this.dashboardData);
            
            if (!this.dashboardData) {
                console.warn('No dashboard data available, trying to load...');
                const self = this;
                return this._loadDashboardData().then(function() {
                    console.log('Data loaded, calling _updateDashboard again');
                    self._updateDashboard();
                });
            }
            
            const data = this.dashboardData;
            console.log('=== Updating dashboard with data ===');
            console.log('Total phong:', data.total_phong);
            console.log('Meetings today:', data.meetings_today);
            console.log('Full data:', data);
            
            // Update KPI cards
            console.log('Updating KPI cards...');
            const totalPhongEl = this.$('#total_phong');
            console.log('total_phong element found:', totalPhongEl.length > 0);
            if (totalPhongEl.length) {
                totalPhongEl.text(data.total_phong || 0);
                console.log('Set total_phong to:', data.total_phong || 0);
            } else {
                console.warn('Element #total_phong not found!');
            }
            
            if (this.$('#meetings_today').length) {
                this.$('#meetings_today').text(data.meetings_today || 0);
                console.log('Set meetings_today to:', data.meetings_today || 0);
            }
            if (this.$('#meetings_week').length) {
                this.$('#meetings_week').text(data.meetings_week || 0);
                console.log('Set meetings_week to:', data.meetings_week || 0);
            }
            if (this.$('#total_hours').length) {
                this.$('#total_hours').text(data.total_hours || 0);
                console.log('Set total_hours to:', data.total_hours || 0);
            }
            if (this.$('#ty_le_su_dung').length) {
                this.$('#ty_le_su_dung').text((data.ty_le_su_dung || 0) + '%');
                console.log('Set ty_le_su_dung to:', (data.ty_le_su_dung || 0) + '%');
            }
            if (this.$('#ty_le_lang_phi').length) {
                this.$('#ty_le_lang_phi').text((data.ty_le_lang_phi || 0) + '%');
                console.log('Set ty_le_lang_phi to:', (data.ty_le_lang_phi || 0) + '%');
            }
            if (this.$('#ty_le_huy').length) {
                this.$('#ty_le_huy').text((data.ty_le_huy || 0) + '%');
                console.log('Set ty_le_huy to:', (data.ty_le_huy || 0) + '%');
            }
            if (this.$('#ty_le_no_show').length) {
                this.$('#ty_le_no_show').text((data.ty_le_no_show || 0) + '%');
                console.log('Set ty_le_no_show to:', (data.ty_le_no_show || 0) + '%');
            }
            if (this.$('#phong_dang_su_dung').length) {
                this.$('#phong_dang_su_dung').text(data.phong_dang_su_dung || 0);
                console.log('Set phong_dang_su_dung to:', data.phong_dang_su_dung || 0);
            }
            if (this.$('#phong_bao_tri').length) {
                this.$('#phong_bao_tri').text(data.phong_bao_tri || 0);
                console.log('Set phong_bao_tri to:', data.phong_bao_tri || 0);
            }
            console.log('KPI cards updated');

            // Render heatmap
            this._renderHeatmap(data.heatmap_data || [], data.heatmap_hours || []);

            // Render usage chart
            this._renderUsageChart(data.usage_by_day || []);

            // Render top rooms chart
            this._renderTopRoomsChart(data.top_rooms || []);

            // Render department performance chart
            this._renderDeptPerformanceChart(data.dept_performance || []);

            // Render quality chart
            this._renderQualityChart(data.quality_stats || {});

            // Render asset health table
            this._renderAssetHealthTable(data.asset_health || []);

            // Render recent activities table
            this._renderRecentActivitiesTable(data.recent_activities || []);

            // Render upcoming meetings table
            this._renderUpcomingMeetings(data.upcoming_meetings || []);

            // Render ending soon table
            this._renderEndingSoon(data.ending_soon || []);
            
            // Render real-time data & warnings
            this._renderWarnings(data.warnings || []);
            this._renderPhongDangHop(data.phong_dang_hop || []);
            this._renderCuocHopSapBatDau(data.cuoc_hop_sap_bat_dau || []);
            
            // Setup quick actions
            this._setupQuickActions();
        },
        
        _setupQuickActions: function() {
            const self = this;
            // Quick book
            this.$('#btn_quick_book').off('click').on('click', function() {
                self._showQuickBookDialog();
            });
            // Quick check-in
            this.$('#btn_quick_checkin').off('click').on('click', function() {
                self._showQuickCheckinDialog();
            });
            // Quick end
            this.$('#btn_quick_end').off('click').on('click', function() {
                self._showQuickEndDialog();
            });
            // Quick unlock
            this.$('#btn_quick_unlock').off('click').on('click', function() {
                self._showQuickUnlockDialog();
            });
        },
        
        _renderWarnings: function(warnings) {
            const $container = this.$('#warningsContainer');
            if (!$container.length) return;
            
            $container.empty();
            
            if (warnings.length === 0) {
                $container.append('<div class="alert alert-success"><i class="fa fa-check-circle"></i> Không có cảnh báo nào</div>');
                return;
            }
            
            warnings.forEach(function(warning) {
                const severityClass = warning.severity === 'danger' ? 'alert-danger' : 
                                      warning.severity === 'warning' ? 'alert-warning' : 'alert-info';
                const icon = warning.severity === 'danger' ? 'fa-exclamation-circle' : 
                            warning.severity === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
                
                let actionBtn = '';
                if (warning.booking_id) {
                    actionBtn = `<button class="btn btn-sm btn-primary ml-2" data-booking-id="${warning.booking_id}">Xem chi tiết</button>`;
                } else if (warning.room_id) {
                    actionBtn = `<button class="btn btn-sm btn-primary ml-2" data-room-id="${warning.room_id}">Xem phòng</button>`;
                }
                
                $container.append(`
                    <div class="alert ${severityClass} alert-dismissible fade show" role="alert">
                        <i class="fa ${icon}"></i> <strong>${warning.title}:</strong> ${warning.message}
                        ${actionBtn}
                        <button type="button" class="close" data-dismiss="alert">
                            <span>&times;</span>
                        </button>
                    </div>
                `);
            });
        },
        
        _renderPhongDangHop: function(phongDangHop) {
            const $tbody = this.$('#phongDangHopTable');
            if (!$tbody.length) return;
            
            $tbody.empty();
            
            if (phongDangHop.length === 0) {
                $tbody.append('<tr><td colspan="5" class="text-center text-muted">Không có phòng nào đang họp</td></tr>');
                return;
            }
            
            const self = this;
            phongDangHop.forEach(function(item) {
                $tbody.append(`
                    <tr>
                        <td>${item.phong || ''}</td>
                        <td>${item.name || ''}</td>
                        <td>${item.host || ''}</td>
                        <td>${item.start_time || ''} - ${item.end_time || ''}</td>
                        <td>
                            <button class="btn btn-sm btn-warning btn-quick-end" data-booking-id="${item.id}">
                                <i class="fa fa-stop"></i> Kết thúc
                            </button>
                        </td>
                    </tr>
                `);
            });
            
            // Bind quick end buttons
            $tbody.find('.btn-quick-end').on('click', function() {
                const bookingId = $(this).data('booking-id');
                self._quickEnd(bookingId);
            });
        },
        
        _renderCuocHopSapBatDau: function(cuocHopSapBatDau) {
            const $tbody = this.$('#cuocHopSapBatDauTable');
            if (!$tbody.length) return;
            
            $tbody.empty();
            
            if (cuocHopSapBatDau.length === 0) {
                $tbody.append('<tr><td colspan="5" class="text-center text-muted">Không có cuộc họp sắp bắt đầu</td></tr>');
                return;
            }
            
            const self = this;
            cuocHopSapBatDau.forEach(function(item) {
                $tbody.append(`
                    <tr>
                        <td>${item.phong || ''}</td>
                        <td>${item.name || ''}</td>
                        <td>${item.host || ''}</td>
                        <td><span class="badge badge-info">${item.minutes_until || 0} phút</span></td>
                        <td>
                            <button class="btn btn-sm btn-success btn-quick-checkin" data-booking-id="${item.id}">
                                <i class="fa fa-check"></i> Check-in
                            </button>
                        </td>
                    </tr>
                `);
            });
            
            // Bind quick check-in buttons
            $tbody.find('.btn-quick-checkin').on('click', function() {
                const bookingId = $(this).data('booking-id');
                self._quickCheckin(bookingId);
            });
        },
        
        _quickCheckin: function(bookingId) {
            const self = this;
            this._rpc({
                model: 'dashboard_phong_hop',
                method: 'quick_checkin',
                args: [bookingId]
            }).then(function(result) {
                if (result.success) {
                    self.displayNotification({
                        title: 'Thành công',
                        message: result.message,
                        type: 'success'
                    });
                    self._update();
                } else {
                    self.displayNotification({
                        title: 'Lỗi',
                        message: result.message,
                        type: 'danger'
                    });
                }
            });
        },
        
        _quickEnd: function(bookingId) {
            const self = this;
            this._rpc({
                model: 'dashboard_phong_hop',
                method: 'quick_end_early',
                args: [bookingId]
            }).then(function(result) {
                if (result.success) {
                    self.displayNotification({
                        title: 'Thành công',
                        message: result.message,
                        type: 'success'
                    });
                    self._update();
                } else {
                    self.displayNotification({
                        title: 'Lỗi',
                        message: result.message,
                        type: 'danger'
                    });
                }
            });
        },
        
        _showQuickBookDialog: function() {
            // TODO: Implement quick book dialog
            this.displayNotification({
                title: 'Thông báo',
                message: 'Tính năng đặt nhanh phòng đang được phát triển',
                type: 'info'
            });
        },
        
        _showQuickCheckinDialog: function() {
            // TODO: Implement quick check-in dialog
            this.displayNotification({
                title: 'Thông báo',
                message: 'Vui lòng chọn booking từ bảng "Cuộc họp sắp bắt đầu"',
                type: 'info'
            });
        },
        
        _showQuickEndDialog: function() {
            // TODO: Implement quick end dialog
            this.displayNotification({
                title: 'Thông báo',
                message: 'Vui lòng chọn booking từ bảng "Phòng đang họp"',
                type: 'info'
            });
        },
        
        _showQuickUnlockDialog: function() {
            // TODO: Implement quick unlock dialog
            this.displayNotification({
                title: 'Thông báo',
                message: 'Tính năng mở khóa phòng đang được phát triển',
                type: 'info'
            });
        },

        _renderHeatmap: function (heatmapData, hours) {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded');
                return;
            }
            
            if (this.heatmapChart) {
                this.heatmapChart.destroy();
            }

            const canvas = this.$('#heatmapChart');
            if (!canvas.length || !heatmapData || heatmapData.length === 0) {
                console.warn('Heatmap canvas not found or no data', {
                    canvas: canvas.length,
                    heatmapData: heatmapData ? heatmapData.length : 0
                });
                return;
            }

            const ctx = canvas[0].getContext('2d');
            
            // Chuẩn bị dữ liệu cho heatmap
            const roomNames = heatmapData.map(r => r.room);
            const datasets = [];
            
            hours.forEach((hour, hourIdx) => {
                const data = heatmapData.map(room => room.hours[hour] || 0);
                datasets.push({
                    label: hour + 'h',
                    data: data,
                    backgroundColor: this._getHeatmapColor(data, hourIdx),
                    borderWidth: 1
                });
            });

            this.heatmapChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: roomNames,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            stacked: true,
                            ticks: {
                                maxRotation: 45,
                                minRotation: 45
                            }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                }
                            }
                        }
                    }
                }
            });
        },

        _getHeatmapColor: function (values, hourIdx) {
            // Màu sắc dựa trên giá trị sử dụng
            return values.map(val => {
                if (val < 20) return 'rgba(220, 53, 69, 0.3)'; // Đỏ nhạt - ít sử dụng
                if (val < 50) return 'rgba(255, 193, 7, 0.5)'; // Vàng - trung bình
                if (val < 80) return 'rgba(40, 167, 69, 0.6)'; // Xanh lá - tốt
                return 'rgba(0, 123, 255, 0.7)'; // Xanh dương - cao
            });
        },

        _renderUsageChart: function (usageData) {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded');
                return;
            }
            
            if (this.usageChart) {
                this.usageChart.destroy();
            }

            const canvas = this.$('#usageChart');
            if (!canvas.length || !usageData || usageData.length === 0) {
                console.warn('Usage chart canvas not found or no data', {
                    canvas: canvas.length,
                    usageData: usageData ? usageData.length : 0
                });
                return;
            }

            const ctx = canvas[0].getContext('2d');
            const labels = usageData.map(d => d.date);
            const data = usageData.map(d => d.usage);

            this.usageChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tỷ lệ sử dụng (%)',
                        data: data,
                        borderColor: '#6640b2',
                        backgroundColor: 'rgba(102, 64, 178, 0.1)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        },

        _renderTopRoomsChart: function (roomsData) {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded');
                return;
            }
            
            if (this.topRoomsChart) {
                this.topRoomsChart.destroy();
            }

            const canvas = this.$('#topRoomsChart');
            if (!canvas.length || !roomsData || roomsData.length === 0) {
                console.warn('Top rooms chart canvas not found or no data', {
                    canvas: canvas.length,
                    roomsData: roomsData ? roomsData.length : 0
                });
                return;
            }

            const ctx = canvas[0].getContext('2d');
            const labels = roomsData.map(r => r.name);
            const data = roomsData.map(r => r.count);

            this.topRoomsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số lần đặt',
                        data: data,
                        backgroundColor: '#1faf47',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        },

        _renderDeptPerformanceChart: function (deptData) {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded');
                return;
            }
            
            if (this.deptPerformanceChart) {
                this.deptPerformanceChart.destroy();
            }

            const canvas = this.$('#deptPerformanceChart');
            if (!canvas.length || !deptData || deptData.length === 0) {
                console.warn('Dept performance chart canvas not found or no data', {
                    canvas: canvas.length,
                    deptData: deptData ? deptData.length : 0
                });
                return;
            }

            const ctx = canvas[0].getContext('2d');
            const labels = deptData.map(d => d.name);
            const bookings = deptData.map(d => d.bookings);
            const cancelled = deptData.map(d => d.cancelled);

            this.deptPerformanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số lần đặt',
                        data: bookings,
                        backgroundColor: '#6640b2'
                    }, {
                        label: 'Số lần hủy',
                        data: cancelled,
                        backgroundColor: '#ff4c5b'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        _renderQualityChart: function (qualityStats) {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded');
                return;
            }
            
            if (this.qualityChart) {
                this.qualityChart.destroy();
            }

            const canvas = this.$('#qualityChart');
            if (!canvas.length || !qualityStats || Object.keys(qualityStats).length === 0) {
                console.warn('Quality chart canvas not found or no data', {
                    canvas: canvas.length,
                    qualityStats: qualityStats ? Object.keys(qualityStats).length : 0
                });
                return;
            }

            const ctx = canvas[0].getContext('2d');

            this.qualityChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Phòng quá lớn', 'Phòng quá nhỏ', 'Họp quá dài', 'Kết thúc đúng giờ'],
                    datasets: [{
                        data: [
                            qualityStats.over_capacity || 0,
                            qualityStats.under_capacity || 0,
                            qualityStats.over_time || 0,
                            qualityStats.on_time_end || 0
                        ],
                        backgroundColor: [
                            '#ff4c5b',
                            '#ff9800',
                            '#fd7e14',
                            '#1faf47'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        _renderAssetHealthTable: function (assetData) {
            const $tbody = this.$('#assetHealthTable');
            if (!$tbody.length) {
                console.warn('Asset health table not found');
                return;
            }
            $tbody.empty();

            if (assetData.length === 0) {
                $tbody.append('<tr><td colspan="4" class="text-center text-muted">Không có dữ liệu</td></tr>');
                return;
            }

            assetData.forEach(function (item) {
                const $row = $('<tr>');
                $row.append($('<td>').text(item.room));
                $row.append($('<td>').text(item.maintenance_count));
                const problematicClass = item.problematic_assets > 0 ? 'text-danger' : 'text-success';
                $row.append($('<td>').addClass(problematicClass).text(item.problematic_assets));
                $row.append($('<td>').text(item.total_assets));
                $tbody.append($row);
            });
        },

        _renderRecentActivitiesTable: function (activities) {
            const $tbody = this.$('#recentActivitiesTable');
            if (!$tbody.length) {
                console.warn('Recent activities table not found');
                return;
            }
            $tbody.empty();

            if (activities.length === 0) {
                $tbody.append('<tr><td colspan="4" class="text-center text-muted">Không có hoạt động gần đây</td></tr>');
                return;
            }

            activities.forEach(function (activity) {
                const $row = $('<tr>');
                $row.append($('<td>').text(activity.time));
                $row.append($('<td>').text(activity.action));
                $row.append($('<td>').text(activity.room));
                $row.append($('<td>').text(activity.user));
                $tbody.append($row);
            });
        },

        _renderUpcomingMeetings: function (meetings) {
            const $tbody = this.$('#upcomingMeetingsTable');
            if (!$tbody.length) {
                console.warn('Upcoming meetings table not found');
                return;
            }
            $tbody.empty();

            if (meetings.length === 0) {
                $tbody.append('<tr><td colspan="4" class="text-center text-muted">Không có cuộc họp sắp diễn ra</td></tr>');
                return;
            }

            meetings.forEach(function (meeting) {
                const $row = $('<tr>');
                $row.append($('<td>').text(meeting.start_time));
                $row.append($('<td>').text(meeting.phong));
                $row.append($('<td>').text(meeting.name));
                $row.append($('<td>').text(meeting.host));
                $tbody.append($row);
            });
        },

        _renderEndingSoon: function (meetings) {
            const $tbody = this.$('#endingSoonTable');
            if (!$tbody.length) {
                console.warn('Ending soon table not found');
                return;
            }
            $tbody.empty();

            if (meetings.length === 0) {
                $tbody.append('<tr><td colspan="3" class="text-center text-muted">Không có phòng sắp hết giờ</td></tr>');
                return;
            }

            meetings.forEach(function (meeting) {
                const $row = $('<tr>');
                $row.append($('<td>').text(meeting.end_time));
                $row.append($('<td>').text(meeting.phong));
                $row.append($('<td>').text(meeting.name));
                $tbody.append($row);
            });
        },
    });

    var DashboardPhongHopView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: DashboardPhongHopController
        })
    });

    viewRegistry.add('dashboard_phong_hop_view', DashboardPhongHopView);

    return {
        DashboardPhongHopController: DashboardPhongHopController,
        DashboardPhongHopView: DashboardPhongHopView,
    };
});
