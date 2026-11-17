# -*- coding: utf-8 -*-
{
    'name': 'GC Pricing Engine',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Moteur de tarification avancé pour Graine Créative - Gestion des tarifs, remises et promotions multi-niveaux',
    'description': """
GC Pricing Engine - Gestion avancée des tarifs et remises pour Graine Créative
================================================================================

Développé par Apik Centre Val de Loire pour la migration Divalto 10.5 → Odoo 19

Fonctionnalités principales :
-----------------------------
* Entonnoir tarifaire (OLIM/BR > CR/CU/TS > TG)
* Prix bruts (remisables) et nets (non remisables sauf pied)
* 3 niveaux de remises maximum (cumulatives ou successives)
* Remise exceptionnelle R99 (exclusive, bornée, prioritaire)
* Promotions temporaires (OLIM, BR, RPCREARE, etc.)
* Date de commande ≠ date de saisie (pré-réservations événementielles)
* Exclusions clients/produits automatisées
* Reprise de tarif d'une autre référence (ex: FIMO générique)
* Tarifs dégressifs par quantités
* Kits/décompositions (valorisation au composé ou aux composants)
* Traçabilité complète du calcul tarifaire
* Remise en pied de facture/commande
* Import en masse depuis Excel

Segmentation Clients :
----------------------
* Code tarif client (TG, CR, CU, PI, IN, LE, etc.)
* Code tarif promotionnel (OLIM, BR, etc.)
* Code remise standard (RCREAREF, RCODIPPF, RINTERDA, etc.)
* Code remise promotionnelle (RPCREARE, RPCODIPF, RPPICWIC, etc.)
* Familles tarifaires (générale et exceptionnelle)
* Classes de remises (générale et exceptionnelle)
* Groupes de segmentation (CREAREF, CODIPA, CULTURA, PICWIC, etc.)

Segmentation Produits :
-----------------------
* Groupes de tarification
* Classes de remises exceptionnelles
* Familles promotionnelles
* Pilotage par référence générique (évite la duplication de tarifs)

Performance :
-------------
* Calcul automatique à la saisie de commande
* Optimisé pour milliers de références et commandes multi-lignes
* Indexation sur code, dates, priorités

""",
    'author': 'Apik Centre Val de Loire',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'product',
        'uom',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/pricing_security.xml',
        
        # Données de base
        'data/pricing_sequence.xml',
        
        # Vues modèles principaux
        'views/pricing_rule_views.xml',
        'views/discount_rule_views.xml',
        'views/promotion_views.xml',
        'views/exclusion_views.xml',
        'views/client_segmentation_views.xml',
        'views/product_pricing_views.xml',
        
        # Vues sale.order.line étendu
        'views/sale_order_line_views.xml',
        
        # Rapports et traçabilité
        'views/pricing_traceability_views.xml',
        
        # Wizards
        'views/simulation_wizard.xml',
        'views/traceability_wizard.xml',
        
        # Menus
        'views/pricing_menu.xml',
        
        # Héritages
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
    ],
    'demo': ['data/demo_pricing_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}