# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetLocation(models.Model):
    _name = 'tai_san.location'
    _description = 'Địa điểm tài sản'
    _parent_store = True
    _rec_name = 'display_name'
    _order = 'parent_path'

    name = fields.Char(string="Tên địa điểm", required=True)
    parent_id = fields.Many2one('tai_san.location', string="Địa điểm cha", index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('tai_san.location', 'parent_id', string="Địa điểm con")
    
    location_type = fields.Selection([
        ('view', 'View'),
        ('site', 'Site/Cơ sở'),
        ('building', 'Tòa nhà'),
        ('floor', 'Tầng'),
        ('zone', 'Vùng/Khu'),
        ('room', 'Phòng'),
        ('other', 'Khác')
    ], string="Loại địa điểm", default='other')

    description = fields.Text(string="Mô tả")
    
    display_name = fields.Char(string="Tên hiển thị", compute='_compute_display_name', store=True)

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for rec in self:
            names = []
            current = rec
            while current:
                names.append(current.name)
                current = current.parent_id
            rec.display_name = " / ".join(reversed(names))
