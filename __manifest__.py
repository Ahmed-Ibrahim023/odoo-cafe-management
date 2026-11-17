{
    'name': 'Cafe Management',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Recipes, automatic ingredient deduction, kitchen display, waste and profit for cafes',
    'description': """
Cafe Management System
======================
* Ingredients and recipes (per product or per size variant)
* Automatic ingredient deduction from stock when a POS order is paid (idempotent)
* Kitchen / barista queue
* Waste tracking
* Real drink cost, margin and profit analysis
* Low stock alerts, roles (cashier / barista / storekeeper / manager)
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'stock', 'account', 'mail', 'product', 'bus'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cafe_data.xml',
        'data/cron.xml',
        'views/cafe_ingredient_views.xml',
        'views/cafe_recipe_views.xml',
        'views/cafe_kitchen_views.xml',
        'views/cafe_waste_views.xml',
        'views/pos_views.xml',
        'views/cafe_report_views.xml',
        'views/cafe_menus.xml',
        'report/cafe_receipt.xml',
    ],
    'demo': ['demo/cafe_demo.xml'],
    'assets': {
        'web.assets_backend': [
            'cafe_management/static/src/backend/*.js',
        ],
        'point_of_sale._assets_pos': [
            'cafe_management/static/src/pos/*.js',
            'cafe_management/static/src/pos/*.xml',
        ],
    },
    'application': True,
    'installable': True,
}
