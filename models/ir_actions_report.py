import base64
from odoo import models, api, fields
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        
        # ---------------------------------------------------------
        # 1. REPORTE DUMMY 4x8 (El que imprime los PDFs fusionados)
        # ---------------------------------------------------------
        if report.report_name == 'wb_printer_IoT.report_attachment_dummy':
            # ... (Tu código actual para el PDF múltiple se queda exactamente igual) ...
            if not res_ids:
                raise UserError("No se ha seleccionado ninguna Orden de Venta.")
            
            order_id = res_ids[0]
            order = self.env['sale.order'].browse(order_id)
            if not order.exists():
                raise UserError("No se encontró la Orden de Venta.")
            
            so_attachments = self.env['sale.order.attachment'].search([
                ('so_id', '=', order.id)
            ], order='sequence_number asc') 
            
            if not so_attachments:
                raise UserError(f"No hay ninguna guía adjunta en la orden {order.name}.")
            
            pdf_list = []
            zpl_list = []
            
            for attach in so_attachments:
                if not attach.attachment:
                    continue
                raw_content = base64.b64decode(attach.attachment)
                file_name = attach.file_name or ''
                if file_name.lower().endswith(('.txt', '.zpl')):
                    zpl_list.append(raw_content)
                else:
                    pdf_list.append(raw_content)
            
            if pdf_list:
                if len(pdf_list) > 1:
                    merged_pdf = merge_pdf(pdf_list)
                else:
                    merged_pdf = pdf_list[0]
                return merged_pdf, 'pdf'
            elif zpl_list:
                merged_zpl = b''.join(zpl_list)
                return merged_zpl, 'text'
            raise UserError("Los archivos adjuntos no contienen formatos válidos (PDF/ZPL).")

        # ---------------------------------------------------------
        # 2. NUEVO REPORTE ZPL DE RESPALDO (Etiqueta de Secuencia 4x6)
        # ---------------------------------------------------------
        elif report.report_name == 'wb_printer_IoT.report_zpl_backup':
            if not res_ids:
                raise UserError("No se ha seleccionado ninguna Orden de Venta.")
            
            order_id = res_ids[0]
            order = self.env['sale.order'].browse(order_id)
            if not order.exists():
                raise UserError("No se encontró la Orden de Venta.")

            # Buscamos cuántas guías tiene para generar ese mismo número de etiquetas
            so_attachments = self.env['sale.order.attachment'].search([
                ('so_id', '=', order.id)
            ], order='sequence_number asc')
            
            total_labels = len(so_attachments)
            if total_labels == 0:
                raise UserError(f"La orden {order.name} aún no tiene guías adjuntas.")

            # Variables para llenar la plantilla
            so_name = order.name or ''
            create_date = order.date_order.strftime('%Y-%m-%d') if order.date_order else ''
            team = order.team_id.name if order.team_id else 'Sin Equipo'
            
            # Buscamos el primer traslado asociado para sacar el nombre del OUT
            picking = self.env['stock.picking'].search([('sale_id', '=', order.id)], limit=1)
            out_name = picking.name if picking else 'Sin Traslado'
            almacen = picking.picking_type_id.warehouse_id.name if picking and picking.picking_type_id else 'Almacén Principal'
            carrier = order.carrier_id.name if order.carrier_id else 'Sin Transportista'
            
            full_zpl_code = ""

            # Generamos un bloque ZPL por cada anexo encontrado
            for attach in so_attachments:
                # Extraemos S00030/1, S00030/2, etc.
                display_name = attach.display_name_custom or f"{so_name}/{attach.sequence_number}"
                
                # Inyectamos las variables en tu plantilla ZPL
                zpl_code = f"""
                ^XA
                ^CI28
                ^FO350,50^GFA,2940,2940,49,,:::::::::::gU03CV03CgO078,gT07FCU07FCgN0FF8,gS01FFCT01FFCgM03FF8,003FFE01IF003IFV01FFCT01FFCgM03FF8,I07FF803FFC00FFEW0FFCU0FFCgN0FF8,I03FFC01FFE007FEW07FCU07FCgN07F8,I03FFC00IF003FCW03FCU03FCgN07F8,I01FFE00IF003FCW03FCU03FCgN07F8,I01IF007FF801F8W03FCU03FCgN07F8,J0IF007FF801F8W03FCU03FCgN07F8,J0IF807FFC01FX07FCU03FCgN0FF8,J07FF807FFC00F00FFR07IFC001FCP03FF3FJ0607800FF8Q0JF800FF,J07FFC03FFE00E03FFCI0383F8001JFC007FF8001C1FI03JFC003E1FC07FFEI0383F8003JF807FFE,J03FFC03FFE00E0JF001F8FFC007JFC01IFC00FC7F8003JFE01FE3FE0JFI0F8FFE007JF80JF,J03FFE03IF00C1JF80FFDFFE00KFC03F07E07FCFFC003KF07FE7FE1F87F80FFDIF01KF81F83F,J01FFE03IF00C3FC3FC1LF00FF8FFC07F07F0FFCFFC003FF1FF8FFE7FE3F03F81LF01FF1FF83F01F,J01FFE03IF8187F81FE3LF01FF07FC0FE03F1KFC003FC0FFC7JFE3F03FC3LF03FE0FF83F01F,K0IF03IF818FF01FE1IF9FF83FE03FC1FE03F8IF9F8003FC07FC1FFCFC7F03FC0IF9FF87FC07F87F00F,K0IF07IFC18FF00FF07FE0FF83FC03FC1FE03F83FF0F8003FC03FC1FF8387F03FC07FE07F87FC07F87F8,K07FF87IFC30FF00FF07FC07F83FC03FC1FE03F83FFK03FC03FE0FF8003E03FC03FC07F8FF807F87FFC,K07FFDE3FFE31FF00FF03FC07F87FC03FC3FC07F83FEK03FC03FE0FFJ0803FC03FC07F8FF807F87FFC,K03IFC1IFE1FF00FF83FC07F87FC03FC3FC0FF83FEK03FC03FE0FFL0FFC03FC07F8FF807F83IFE,K03IFC1IFE1FF00FF83FC07F87F803FC3KF83FEK03FC01FE0FFK07FFC03FC07F8FF807F83IFE,K01IF80IFE1FE00FF83FC07F87F803FC3KF83FEK03FC01FE0FFJ03FBFC03FC07F8FF807F81JF,K01IF80IFC1FE00FF83FC07F87F803FC3FF8I03FEK03FC01FE0FFJ0FE3FC03FC07F8FF807F81JF,L0IF807FFC1FF00FF83FC07F87F803FC3FFJ03FEK03FC03FE0FFI01F83FC03FC07F8FF807F807IF8181C,L0IF007FF81FF00FF83FC07F87FC03FC3FEJ03FEK03FC03FE0FFI03F83FC03FC07F8FF807F801IF83FFC,L07FF003FF81FF00FF03FC07F87FC03FC3FEJ03FEK03FC03FE0FFI07F03FC03FC07F8FF807F8003FF81FFC,L07FE003FF80FF00FF03FC07F87FC03FC1FEJ03FEK03FC03FC0FFI07F03FC03FC07F8FF807F87007F81FF8,L03FE001FF00FF00FF03FC07F83FC03FC1FF00103FEK03FC03FC0FFI0FF03FC03FC07F87FC07F87803F81FF8,L03FE001FF007F01FE03FC07F83FE03FC1FF80303FEK03FC07FC0FFI0FF03FC03FC07F87FC07F87C03F81FF8,L01FCI0FE007F81FE07FC07F81FF07FC0FFE0F83FEK03FE0FF81FF800FF87FC03FC07F83FE0FF87C03F81FF8,L01FCI0FE003FC7FC07FC07F81KFE07JF03FFK07KF01FFC007FCFFC87FC07F83KFC7C03F01FF8,M0F8I07C001JF80FFC0FFC0LF03IFE07FF8J0KFC07FFE007KF87FC0FFC1KFE7E07E01FF8,M0F8I07CI0JF01IF3FFE07KF01IFC0IFEI01KFC07IF003FF9FF9IF3FFE0KFE3IFC01FFC,M078I03CI03FFC01IF1IF03FF3FF007FF00IFCJ0FF8FF807FFE001FE0FF1IF1IF03FE7FE0IF003FFC,M07J038J03CI07FE0FFE003M07T018001FF8I03801807FE0FFE007L0F,,::::::::::^FS

                ^CF0,55
                ^FO50,160^FDOrden: {so_name}^FS
                ^CF0,50
                ^FO50,225^FDFecha: {create_date}^FS
                ^CF0,30
                ^FO50,290^FDEquipo: {team}^FS
                ^FO50,330^FDTransportista: {carrier}^FS
                ^FO50,370^GB700,3,3^FS

                ^CFA,30
                ^FO50,430^FDOUT: {out_name}^FS
                ^FO50,480^FD{almacen}^FS
                ^FO50,530^FDGuia: {display_name}^FS
                ^FO50,630^GB700,3,3^FS

                ^FX Codigo de barras gigante con la secuencia (S00030/1)
                ^BY4,2,200
                ^FO50,660^BC^FD{display_name}^FS
                ^CF0,40
                ^FO50,900^FDEtiqueta {attach.sequence_number} de {total_labels}^FS
                ^XZ
                """
                full_zpl_code += zpl_code

            # Retornamos todo el código concatenado como texto crudo
            return full_zpl_code.encode('utf-8'), 'text'

        # Si no es ninguno de nuestros reportes especiales, flujo normal
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)