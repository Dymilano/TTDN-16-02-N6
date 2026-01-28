# -*- coding: utf-8 -*-
"""
Post-migration script để thêm các columns mới vào database
Chạy sau khi upgrade module
"""
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """Thêm các columns mới vào bảng dat_phong_hop"""
    _logger.info("Starting migration for quan_ly_phong_hop")
    
    # Kiểm tra và thêm column assistant_id nếu chưa có
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dat_phong_hop' AND column_name='assistant_id'
    """)
    if not cr.fetchone():
        _logger.info("Adding column assistant_id to dat_phong_hop")
        cr.execute("""
            ALTER TABLE dat_phong_hop 
            ADD COLUMN assistant_id INTEGER REFERENCES res_users(id) ON DELETE SET NULL
        """)
    
    # Kiểm tra và thêm các columns khác nếu cần
    columns_to_add = [
        ('is_recurring', 'BOOLEAN DEFAULT FALSE'),
        ('recurring_type', 'VARCHAR'),
        ('recurring_end_date', 'DATE'),
        ('recurring_count', 'INTEGER DEFAULT 1'),
        ('parent_booking_id', 'INTEGER REFERENCES dat_phong_hop(id) ON DELETE SET NULL'),
        ('is_multi_room', 'BOOLEAN DEFAULT FALSE'),
        ('is_assistant_booking', 'BOOLEAN DEFAULT FALSE'),
        ('is_outside_hours', 'BOOLEAN DEFAULT FALSE'),
    ]
    
    for column_name, column_type in columns_to_add:
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='dat_phong_hop' AND column_name=%s
        """, (column_name,))
        if not cr.fetchone():
            _logger.info("Adding column %s to dat_phong_hop", column_name)
            try:
                cr.execute("ALTER TABLE dat_phong_hop ADD COLUMN %s %s" % (column_name, column_type))
            except Exception as e:
                _logger.warning("Error adding column %s: %s", column_name, str(e))
    
    # Tạo bảng quan hệ many2many cho related_booking_ids nếu chưa có
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'dat_phong_hop_multi_rel'
        )
    """)
    if not cr.fetchone()[0]:
        _logger.info("Creating table dat_phong_hop_multi_rel")
        cr.execute("""
            CREATE TABLE dat_phong_hop_multi_rel (
                booking1_id INTEGER REFERENCES dat_phong_hop(id) ON DELETE CASCADE,
                booking2_id INTEGER REFERENCES dat_phong_hop(id) ON DELETE CASCADE,
                PRIMARY KEY (booking1_id, booking2_id)
            )
        """)
    
    _logger.info("Migration completed for quan_ly_phong_hop")
