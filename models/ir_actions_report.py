import base64
from odoo import models, api
from odoo.exceptions import UserError

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        
        #4x6 dummy
        if report.report_name == 'wb_printer_IoT.report_attachment_dummy':
            if not res_ids:
                raise UserError("No se ha seleccionado ningún traslado.")
            
            picking_id = res_ids[0]
            
            #buscamos el stock.picking
            picking = self.env['stock.picking'].browse(picking_id)
            
            if not picking.exists():
                raise UserError("No se encontró el traslado.")
            
            #buscar los adjuntos del stock picking
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', picking.id),
                ('mimetype', '=', 'application/pdf')
                # 'mimetype', 'in', ['application/pdf', 'text/plain', 'application/zpl']) #pdf y zpl
            ], limit=1, order='create_date desc')
            
            if not attachment:
                raise UserError(f"No hay ninguna guía PDF de 4x6 adjunta en el traslado {picking.name}.")
            
            '''
            
            raw_content = base64.b64decode(attachment.datas)
            
            if attachment.mimetype in ['text/plain', 'application/zpl'] or attachment.name.endswith(('.txt', '.zpl')):
                # Lo enviamos como texto crudo para que el IoT lo inyecte directo a la térmica
                return raw_content, 'text'
            else:
                # Lo enviamos como PDF para que el IoT lo rasterice
                return raw_content, 'pdf'
            '''
            
            
            #data raw
            pdf_content = base64.b64decode(attachment.datas)
            return pdf_content, 'pdf'
            
        #si no es el dummy, return proceso original
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)