from odoo import api, fields, models
 
class ZefaSchedule(models.Model):
    _name = 'zefa.schedule'
    _description = 'Zefa Schedule'
     
    name = fields.Char(string='Nama', required=True)
    description = fields.Text(string='Deskripsi')
    description_2 = fields.Text(string='Deskripsi_2')
    frequency = fields.Selection(selection=[
        ('harian', 'Harian'), 
        ('mingguan', 'Mingguan'), 
        ('bulanan', 'Bulanan')],
        string='Jenis')