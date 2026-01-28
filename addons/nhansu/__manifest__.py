# -*- coding: utf-8 -*-
{
    'name': "Quản lý nhân sự",

    'summary': """
        Module quản lý nhân sự doanh nghiệp, quản lý nhân viên, phòng ban, 
        chức vụ, chứng chỉ và lịch sử công tác""",

    'description': """
        Module quản lý nhân sự bao gồm:
        - Quản lý thông tin nhân viên
        - Quản lý phòng ban với cấu trúc phân cấp
        - Quản lý chức vụ và cấp bậc
        - Quản lý chứng chỉ, bằng cấp
        - Lịch sử công tác của nhân viên
        - Chấm công: giờ vào/ra, tính số giờ làm, trạng thái
        - Vi phạm chấm công: muộn giờ, về sớm, thiếu giờ, quên chấm công
        - Bảng lương tháng: tính lương theo ngày công hoặc theo giờ
        - Tracking người tạo và người sửa
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/phong_ban.xml',
        'views/chuc_vu.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/cham_cong.xml',
        'views/vi_pham_cham_cong.xml',
        'views/tang_ca.xml',
        'views/ky_luong.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
