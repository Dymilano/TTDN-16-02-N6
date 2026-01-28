# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WizardAddAssets(models.TransientModel):
    _name = 'wizard.add.assets.to.room'
    _description = 'Wizard thêm tài sản vào phòng'

    phong_hop_id = fields.Many2one('phong_hop', string='Phòng họp', required=True)
    tai_san_ids = fields.Many2many('tai_san', 'wizard_add_assets_tai_san_rel', 'wizard_id', 'tai_san_id',
                                   string='Tài sản cần thêm',
                                   domain=[('is_shared_asset', '=', True)])
    
    def action_add_assets(self):
        """Thêm tài sản vào phòng"""
        self.ensure_one()
        if not self.tai_san_ids:
            raise ValidationError(_('Vui lòng chọn ít nhất một tài sản!'))
        
        # Tạo các bản ghi tai_san_phong_hop
        for tai_san in self.tai_san_ids:
            # Kiểm tra xem đã tồn tại chưa
            existing = self.env['tai_san_phong_hop'].search([
                ('phong_hop_id', '=', self.phong_hop_id.id),
                ('tai_san_id', '=', tai_san.id)
            ])
            if not existing:
                self.env['tai_san_phong_hop'].create({
                    'phong_hop_id': self.phong_hop_id.id,
                    'tai_san_id': tai_san.id,
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã thêm %s tài sản vào phòng %s') % (len(self.tai_san_ids), self.phong_hop_id.ten_phong),
                'type': 'success',
                'sticky': False,
            }
        }
