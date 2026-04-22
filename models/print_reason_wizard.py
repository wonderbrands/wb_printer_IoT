from odoo import models, fields, api
from odoo.exceptions import UserError
from markupsafe import Markup


class PrintReasonWizard(models.TransientModel):
    _name = 'sale.order.print.reason.wizard'
    _description = 'Motivo de Reimpresión'

    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', required=True)
    print_reason_selection = fields.Selection([
        ('etiqueta_danada', 'Etiqueta dañada'),
        ('etiqueta_ilegible', 'Etiqueta ilegible / borrosa'),
        ('error_datos', 'Error en datos de la etiqueta'),
        ('extravio_paquete', 'Extravío de paquete'),
        ('cambio_carrier', 'Cambio de carrier / paquetería'),
        ('devolucion', 'Devolución o cambio'),
        ('auditoria', 'Auditoría / verificación'),
        ('otro', 'Otro (especificar)'),
    ], string='Motivo de Impresión')
    
    print_reason_text = fields.Text(string='Detalle del motivo')
    report_type = fields.Selection([
        ('attachment_4x8', 'Guía Adjunta 4x8'),
        ('etiqueta_ei', 'Etiqueta EI'),
    ], string='Tipo de Reporte', required=True)

    @api.onchange('print_reason_selection')
    def _onchange_print_reason_selection(self):
        """Limpiar el texto libre cuando se cambia a una opción predefinida."""
        if self.print_reason_selection != 'otro':
            self.print_reason_text = False

    def action_print(self):
        self.ensure_one()

        # --- Validar permisos del grupo de seguridad ---
        if not self.env.user.has_group('wb_printer_IoT.group_print_labels'):
            raise UserError(
                "No tienes permiso para realizar esta acción, solicita a mesa de control."
            )

        # --- Validar que se haya seleccionado un motivo ---
        if not self.print_reason_selection:
            raise UserError("Debes seleccionar un motivo de impresión.")

        # --- Si eligió "Otro", validar que el texto libre tenga contenido real ---
        if self.print_reason_selection == 'otro':
            texto = (self.print_reason_text or '').strip()
            if not texto:
                raise UserError(
                    "Seleccionaste 'Otro (especificar)' como motivo. "
                    "Debes escribir el detalle del motivo."
                )
            if len(texto) < 10:
                raise UserError(
                    "El detalle del motivo es demasiado corto (mínimo 10 caracteres). "
                    "Por favor describe brevemente la razón de la reimpresión."
                )

        order = self.sale_order_id

        # --- Construir el motivo para el chatter ---
        reason_label = dict(
            self._fields['print_reason_selection'].selection
        ).get(self.print_reason_selection, '')

        if self.print_reason_selection == 'otro':
            reason_display = f"{reason_label}: {self.print_reason_text.strip()}"
        else:
            reason_display = reason_label

        report_label = dict(
            self._fields['report_type'].selection
        ).get(self.report_type, '')

        body_html = Markup(
            "<b>Reimpresión:</b> %s<br/>"
            "<b>Motivo:</b> %s<br/>"
            "<b>Usuario:</b> %s"
        ) % (report_label, reason_display, self.env.user.name)

        order.message_post(
            body=body_html,
            subject="Reimpresión solicitada",
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        # --- Disparar el reporte correspondiente ---
        if self.report_type == 'attachment_4x8':
            action = self.env.ref(
                'wb_printer_IoT.action_report_print_attachment_4x8'
            ).report_action(order)
        else:
            action = self.env.ref(
                'wb_printer_IoT.action_report_zpl_backup'
            ).report_action(order)

        action['close_on_report_download'] = True
        return action