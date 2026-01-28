# -*- coding: utf-8 -*-
{
    'name': "Quản lý phòng họp",

    'summary': """
        Module quản lý phòng họp với đầy đủ tính năng đặt phòng, dịch vụ, bảo trì và dashboard
    """,

    'description': """
        Module Quản lý phòng họp bao gồm:
        - Danh mục phòng họp với đầy đủ thông tin
        - Đặt phòng và điều phối với calendar view
        - Dịch vụ kèm theo (catering, IT support, setup)
        - Bảo trì phòng họp
        - Tài sản phòng họp
        - Dashboard và báo cáo
        - Tích hợp với module quản lý tài sản và nhân sự
    """,

    'author': "Nguyễn Ngọc Đan Trường - 1504",
    'website': "http://www.yourcompany.com",

    'category': 'Human Resources',
    'version': '15.0.1.0.10',

    'depends': ['base', 'web', 'nhansu', 'mail', 'quan_ly_tai_san'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'data/cleanup_ai_chatbot.xml',
        'views/phong_hop.xml',
        'views/dat_phong_hop.xml',
        'views/dich_vu_phong_hop.xml',
        'views/bao_tri_phong_hop.xml',
        'views/tai_san_phong_hop.xml',
        'views/dashboard_phong_hop.xml',
        'views/wizard_reject_booking.xml',
        'views/wizard_cancel_booking.xml',
        'views/wizard_add_assets.xml',
        'views/wizard_multi_room_booking.xml',
        'views/wizard_extend_booking.xml',
        'views/menu.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js',
            'quan_ly_phong_hop/static/src/css/dashboard.css',
            'quan_ly_phong_hop/static/src/js/dashboard_phong_hop.js',
        ],
    },
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
