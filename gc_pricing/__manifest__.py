# -*- coding: utf-8 -*-
{
    'name': 'GC Pricing Engine',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Moteur de tarification avancé pour Graine Créative - Gestion des tarifs, remises et promotions multi-niveaux',
    'author': 'Apik Centre Val de Loire',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'product',
    ],
    'data': [
        # 1. Charger d'abord les groupes de sécurité (prérequis pour les accès)
        'security/pricing_security.xml',
        
        # 2. Chargement des modèles via les vues (nécessaire avant le CSV)
        # Les fichiers viewsXML chargent les modèles Python dans le registry
        'views/pricing_rule_views.xml',
        'views/discount_rule_views.xml',
        'views/promotion_views.xml',
        'views/exclusion_views.xml',
        'views/client_segmentation_views.xml',
        'views/product_pricing_views.xml',
        'views/sale_order_line_views.xml',
        'views/pricing_traceability_views.xml',
        'views/simulation_wizard.xml',
        'views/traceability_wizard.xml',
        'views/pricing_menu.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        
        # 3. Séquences de données
        'data/pricing_sequence.xml',
        
        # 4. FINALEMENT les règles d'accès (après que TOUS les modèles soient créés)
        'security/ir.model.access.csv',
    ],
    'demo': ['data/demo_pricing_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}