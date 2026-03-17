import base64
import requests
from odoo import models, api, fields
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        
        # ---------------------------------------------------------
        # Etqiuetas 4x8 adjuntas en modelo nuevo de guías
        # ---------------------------------------------------------
        if report.report_name == 'wb_printer_IoT.report_attachment_dummy':
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
        # ZPL de respaldo (Basado en el PICK y los SKUs)
        # ---------------------------------------------------------
        elif report.report_name == 'wb_printer_IoT.report_zpl_backup':
            if not res_ids:
                raise UserError("No se ha seleccionado ninguna Orden de Venta.")
            
            order_id = res_ids[0]
            order = self.env['sale.order'].browse(order_id)
            if not order.exists():
                raise UserError("No se encontró la Orden de Venta.")

            # Variables generales de la SO
            so_name = order.name or ''
            marketplace = order.channel if order.channel else 'Sin marketplace'
            create_date = order.date_order.strftime('%Y-%m-%d') if order.date_order else ''
            
            # El campo nuevo del carrier
            carrier = order.data_carrier_selection_relational.name if order.data_carrier_selection_relational else 'Sin carrier'
            
            # Buscar el movimiento PICK asociado a la orden
            picking = self.env['stock.picking'].search([
                ('sale_id', '=', order.id),
                ('name', 'ilike', 'PICK')
            ], limit=1)
            
            if not picking:
                picking = self.env['stock.picking'].search([('sale_id', '=', order.id)], limit=1)

            if not picking:
                raise UserError(f"No se encontró un movimiento de inventario (PICK) para la orden {so_name}.")

            almacen = picking.picking_type_id.warehouse_id.name if picking.picking_type_id else 'Almacén Principal'
            
            moves = picking.move_ids
            
            # Calculamos el TOTAL REAL DE ETIQUETAS sumando las cantidades de cada línea
            total_labels = 0
            for m in moves:
                # Usamos quantity si ya se validó, si no, usamos product_uom_qty (demanda inicial)
                qty = m.quantity if m.quantity > 0 else m.product_uom_qty
                total_labels += int(qty)
            
            if total_labels == 0:
                raise UserError(f"El movimiento {picking.name} no tiene cantidades válidas a imprimir.")

            full_zpl_code = ""
            current_label_idx = 1 #Contador global

            #Recorremos cada línea sku del PICK
            for move in moves:
                product = move.product_id
                
                # Determinamos n copias de este SKU imprimir
                qty_to_print = int(move.quantity if move.quantity > 0 else move.product_uom_qty)
                
                if qty_to_print <= 0:
                    continue #Saltamos si la cantidad es cero
                
                #Extracción de campos del SKU
                sku = product.default_code or 'Sin SKU'
                product_name = product.name or 'Sin Nombre'
                if len(product_name) > 40:
                    product_name = product_name[:37] + "..."
                
                #Dimensiones y Peso
                p_length = getattr(product, 'packing_length', 0.0) or 0.0
                p_height = getattr(product, 'packing_height', 0.0) or 0.0
                p_width  = getattr(product, 'packing_width', 0.0) or 0.0
                p_weight = getattr(product, 'packing_weight', 0.0) or 0.0

                #Iteramos según la CANTIDAD del producto
                for _ in range(qty_to_print):
                    display_name = f"{so_name}/{current_label_idx}"
                    
                    zpl_code = f"""^XA
                                    ^CI28

                                    ^FX --- LOGOTIPO ---
                                    ^FO350,50^GFA,2940,2940,49,,:::::::::::gU03CV03CgO078,gT07FCU07FCgN0FF8,gS01FFCT01FFCgM03FF8,003FFE01IF003IFV01FFCT01FFCgM03FF8,I07FF803FFC00FFEW0FFCU0FFCgN0FF8,I03FFC01FFE007FEW07FCU07FCgN07F8,I03FFC00IF003FCW03FCU03FCgN07F8,I01FFE00IF003FCW03FCU03FCgN07F8,I01IF007FF801F8W03FCU03FCgN07F8,J0IF007FF801F8W03FCU03FCgN07F8,J0IF807FFC01FX07FCU03FCgN0FF8,J07FF807FFC00F00FFR07IFC001FCP03FF3FJ0607800FF8Q0JF800FF,J07FFC03FFE00E03FFCI0383F8001JFC007FF8001C1FI03JFC003E1FC07FFEI0383F8003JF807FFE,J03FFC03FFE00E0JF001F8FFC007JFC01IFC00FC7F8003JFE01FE3FE0JFI0F8FFE007JF80JF,J03FFE03IF00C1JF80FFDFFE00KFC03F07E07FCFFC003KF07FE7FE1F87F80FFDIF01KF81F83F,J01FFE03IF00C3FC3FC1LF00FF8FFC07F07F0FFCFFC003FF1FF8FFE7FE3F03F81LF01FF1FF83F01F,J01FFE03IF8187F81FE3LF01FF07FC0FE03F1KFC003FC0FFC7JFE3F03FC3LF03FE0FF83F01F,K0IF03IF818FF01FE1IF9FF83FE03FC1FE03F8IF9F8003FC07FC1FFCFC7F03FC0IF9FF87FC07F87F00F,K0IF07IFC18FF00FF07FE0FF83FC03FC1FE03F83FF0F8003FC03FC1FF8387F03FC07FE07F87FC07F87F8,K07FF87IFC30FF00FF07FC07F83FC03FC1FE03F83FFK03FC03FE0FF8003E03FC03FC07F8FF807F87FFC,K07FFDE3FFE31FF00FF03FC07F87FC03FC3FC07F83FEK03FC03FE0FFJ0803FC03FC07F8FF807F87FFC,K03IFC1IFE1FF00FF83FC07F87FC03FC3FC0FF83FEK03FC03FE0FFL0FFC03FC07F8FF807F83IFE,K03IFC1IFE1FF00FF83FC07F87F803FC3KF83FEK03FC01FE0FFK07FFC03FC07F8FF807F83IFE,K01IF80IFE1FE00FF83FC07F87F803FC3KF83FEK03FC01FE0FFJ03FBFC03FC07F8FF807F81JF,K01IF80IFC1FE00FF83FC07F87F803FC3FF8I03FEK03FC01FE0FFJ0FE3FC03FC07F8FF807F81JF,L0IF807FFC1FF00FF83FC07F87F803FC3FFJ03FEK03FC03FE0FFI01F83FC03FC07F8FF807F807IF8181C,L0IF007FF81FF00FF83FC07F87FC03FC3FEJ03FEK03FC03FE0FFI03F83FC03FC07F8FF807F801IF83FFC,L07FF003FF81FF00FF03FC07F87FC03FC3FEJ03FEK03FC03FE0FFI07F03FC03FC07F8FF807F8003FF81FFC,L07FE003FF80FF00FF03FC07F87FC03FC1FEJ03FEK03FC03FC0FFI07F03FC03FC07F8FF807F87007F81FF8,L03FE001FF00FF00FF03FC07F83FC03FC1FF00103FEK03FC03FC0FFI0FF03FC03FC07F87FC07F87803F81FF8,L03FE001FF007F01FE03FC07F83FE03FC1FF80303FEK03FC07FC0FFI0FF03FC03FC07F87FC07F87C03F81FF8,L01FCI0FE007F81FE07FC07F81FF07FC0FFE0F83FEK03FE0FF81FF800FF87FC03FC07F83FE0FF87C03F81FF8,L01FCI0FE003FC7FC07FC07F81KFE07JF03FFK07KF01FFC007FCFFC87FC07F83KFC7C03F01FF8,M0F8I07C001JF80FFC0FFC0LF03IFE07FF8J0KFC07FFE007KF87FC0FFC1KFE7E07E01FF8,M0F8I07CI0JF01IF3FFE07KF01IFC0IFEI01KFC07IF003FF9FF9IF3FFE0KFE3IFC01FFC,M078I03CI03FFC01IF1IF03FF3FF007FF00IFCJ0FF8FF807FFE001FE0FF1IF1IF03FE7FE0IF003FFC,M07J038J03CI07FE0FFE003M07T018001FF8I03801807FE0FFE007L0F,,::::::::::^FS

                                    ^FX --- BLOQUE 1: DATOS DE LA ORDEN ---
                                    ^CF0,60
                                    ^FO50,200^FDOrden: {so_name}^FS
                                    ^CF0,40
                                    ^FO50,290^FDFecha de orden: {create_date}^FS
                                    ^FO50,350^FDMarketplace: {marketplace}^FS
                                    ^FO50,410^FDCarrier: {carrier}^FS
                                    ^FO50,480^GB700,4,4^FS

                                    ^FX --- BLOQUE 2: DATOS DEL SKU Y CAJA ---
                                    ^CFA,40
                                    ^FO50,530^FDSKU: {sku}^FS
                                    ^CFA,30
                                    ^FO50,600^FB700,2,0,L,0^FDProd: {product_name}^FS

                                    ^FX --- TABLA DE DIMENSIONES (Cuadricula de 4 celdas) ---
                                    ^FO50,670^GB700,90,3^FS
                                    ^FO50,715^GB700,0,3^FS
                                    ^FO225,670^GB0,90,3^FS
                                    ^FO400,670^GB0,90,3^FS
                                    ^FO575,670^GB0,90,3^FS

                                    ^CF0,25
                                    ^FO50,685^FB175,1,0,C^FDLargo^FS
                                    ^FO225,685^FB175,1,0,C^FDAncho^FS
                                    ^FO400,685^FB175,1,0,C^FDAlto^FS
                                    ^FO575,685^FB175,1,0,C^FDPeso^FS

                                    ^CF0,30
                                    ^FO50,730^FB175,1,0,C^FD{p_length} cm^FS
                                    ^FO225,730^FB175,1,0,C^FD{p_width} cm^FS
                                    ^FO400,730^FB175,1,0,C^FD{p_height} cm^FS
                                    ^FO575,730^FB175,1,0,C^FD{p_weight} kg^FS

                                    ^FO50,790^GB700,4,4^FS

                                    ^FX --- BLOQUE 3: TRASLADO Y GUIA ---
                                    ^CFA,40
                                    ^FO50,830^FDPICK: {picking.name}^FS
                                    ^CFA,50
                                    ^FO50,910^FDEI: {display_name}^FS
                                    ^FO50,990^GB700,4,4^FS

                                    ^FX --- BLOQUE 4: CODIGO DE BARRAS ---
                                    ^BY6,2,300
                                    ^FO30,1050^BCN,300,N,N,N^FD{display_name}^FS

                                    ^FX --- BLOQUE 5: CONTADOR ---
                                    ^CF0,50
                                    ^FO50,1450^FDEtiqueta {current_label_idx} de {total_labels}^FS
                                    ^XZ
                                    """
                    full_zpl_code += zpl_code
                    current_label_idx += 1 #Aumentamos el contador para la siguiente etiqueta

            #Retornamos como raw
            return full_zpl_code.encode('utf-8'), 'text'
            # --- MODO PRUEBA PARA IMPRESORA TINTA (ZPL a PDF) ---
            # try:
            #     # Enviamos el ZPL a la API de Labelary pidiendo un PDF de 4x8
            #     url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x8/'
            #     headers = {'Accept': 'application/pdf'}
                
            #     # Hacemos la petición
            #     response = requests.post(url, data=full_zpl_code.encode('utf-8'), headers=headers, timeout=10)
                
            #     if response.status_code == 200:
            #         # Si todo sale bien, devolvemos el PDF descargado
            #         return response.content, 'pdf'
            #     else:
            #         raise UserError(f"Error en la API de prueba: {response.status_code}")
                    
            # except requests.exceptions.RequestException as e:
            #     raise UserError(f"No hay internet para la prueba o la API falló: {e}")

        # ---------------------------------------------------------
        # Etiquetas 2x1 
        # ---------------------------------------------------------
        elif report.report_name == 'wb_printer_IoT.report_custom_2x1':
            if not res_ids:
                raise UserError("No se ha seleccionado ninguna Orden de Venta.")
            
            order_id = res_ids[0]
            order = self.env['sale.order'].browse(order_id)
            marketplace = order.channel if order.channel else 'Sin marketplace'
            team_name = order.team_id.name if order.team_id else "Sin Equipo"
            if not order.exists():
                raise UserError("No se encontró la Orden de Venta.")

            so_attachments = self.env['sale.order.attachment'].search([
                ('so_id', '=', order.id)
            ], order='sequence_number asc')
            
            full_zpl_code = ""
            
            if so_attachments:
                # Si hay adjuntos, creamos una etiqueta 2x1 por cada uno
                len_so_attachments = len(so_attachments)
                for attach in so_attachments:
                    display_name = attach.display_name_custom or f"{order.name}/{attach.sequence_number}"
                    
                    zpl_code = f"""^XA
                                ^PW400
                                ^LL200
                                ^CFA,30
                                ^FO0,20^FB400,1,0,C,0^FD{display_name} de {len_so_attachments}^FS
                                ^CFA,20
                                ^FO0,60^FB400,1,0,C,0^FD{marketplace}^FS
                                ^BY2,2,70
                                ^FO60,90^BCN,90,N,N,N^FD{display_name}^FS
                                ^XZ
                                """
                    full_zpl_code += zpl_code
            else:
                # Si NO hay adjuntos, sacamos una de "Sin Guias"
                zpl_code = f"""^XA
                            ^PW400
                            ^LL200
                            ^CFA,30
                            ^FO0,50^FB400,1,0,C,0^FDSin Guias^FS
                            ^CFA,40
                            ^FO0,110^FB400,1,0,C,0^FD{order.name}^FS
                            ^XZ
                            """
                full_zpl_code += zpl_code

            return full_zpl_code.encode('utf-8'), 'text'

        # Si no es ninguno de nuestros reportes especiales, flujo normal
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)