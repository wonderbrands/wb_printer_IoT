from odoo import models, fields, api
from odoo.exceptions import UserError
from markupsafe import Markup


class PrintReasonWizard(models.TransientModel):
    _name = 'sale.order.print.reason.wizard'
    _description = 'Motivo de Reimpresión'

    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', required=True)
    print_reason = fields.Text(string='Motivo de Impresión')
    report_type = fields.Selection([
        ('attachment_4x8', 'Guía Adjunta 4x8'),
        ('etiqueta_ei', 'Etiqueta EI'),
    ], string='Tipo de Reporte', required=True)

    def action_print(self):
        self.ensure_one()
        order = self.sale_order_id

        # Registrar en el chatter
        report_label = dict(self._fields['report_type'].selection).get(self.report_type, '')
        body_html = Markup(
            "<b>Reimpresión:</b> %s<br/>"
            "<b>Motivo:</b> %s<br/>"
            "<b>Usuario:</b> %s"
        ) % (report_label, self.print_reason, self.env.user.name)

        order.message_post(
            body=body_html,
            subject="Reimpresión solicitada",
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        # Disparar el reporte correspondiente
        if self.report_type == 'attachment_4x8':
            return self.env.ref('wb_printer_IoT.action_report_print_attachment_4x8').report_action(order)
        else:
            return self.env.ref('wb_printer_IoT.action_report_zpl_backup').report_action(order)