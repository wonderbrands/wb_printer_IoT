{
    'name': 'WB Printer IoT Integration',
    'version': '18.0.1.0.0',
    'summary': 'Integración de impresión IoT para etiquetas y adjuntos',
    'author': 'Sergio Guerrero',
    'category': 'Inventory/Barcode',
    'depends': ['base', 'stock', 'stock_barcode', 'iot'],
    'data': [
        'views/report_paperformats.xml',
        'views/report_actions.xml',
        'views/report_label_template.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}