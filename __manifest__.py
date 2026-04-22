{
    'name': 'WB Printer IoT Integration',
    'version': '18.0.1.0.0',
    'summary': 'Integración de impresión IoT para etiquetas y adjuntos',
    'author': 'Sergio Guerrero',
    'category': 'Inventory/Barcode',
    'depends': ['base', 'stock', 'stock_barcode', 'iot', 'sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'views/report_paperformats.xml',
        'views/report_actions.xml',
        'views/report_label_template.xml',
        'views/report_combinated.xml',
        'views/print_reason_wizard_views.xml',
        
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}