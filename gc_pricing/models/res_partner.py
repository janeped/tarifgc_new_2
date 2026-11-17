# -*- coding: utf-8 -*-
"""
Extension res.partner - Champs tarifaires clients
"""

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ========== CODES TARIFAIRES ==========
    customer_tariff_code = fields.Char(
        string='Code Tarif Client',
        help="Code tarif principal (ex: TG, TS, CU, BR, CR, LE, PI, IN...)"
    )
    
    customer_promotional_tariff_code = fields.Char(
        string='Code Tarif Promotionnel',
        help="Code tarif promotionnel (ex: OLIM, BR, RPCREARE...)"
    )
    
    # ========== SEGMENTATION CLIENT ==========
    client_segmentation_group_ids = fields.Many2many(
        'client.segmentation.group',
        string='Groupes de Segmentation',
        help="Groupes auxquels appartient ce client (CREAREF, CODIPA, CULTURA...)"
    )
    
    customer_tariff_family = fields.Many2one(
        'client.tariff.family',
        string='Famille Tarifaire',
    )
    
    customer_tariff_exceptional = fields.Many2one(
        'client.tariff.exceptional',
        string='Famille Tarifaire Exceptionnelle',
    )
    
    # ========== CODES REMISE ==========
    customer_discount_code = fields.Char(
        string='Code Remise Client',
        help="Code remise standard (ex: RCREAREF, RCODIPPF, RINTERDA...)"
    )
    
    customer_promotional_discount_code = fields.Char(
        string='Code Remise Promotionnelle',
        help="Code remise promotionnelle temporaire (ex: RPCREARE, RPCULTUR...)"
    )
    
    # ========== CLASSES DE REMISE ==========
    customer_discount_class = fields.Many2one(
        'client.discount.exceptional',
        string='Classe de Remise Client',
    )
    
    customer_exceptional_discount_class = fields.Many2one(
        'client.discount.exceptional',
        string='Classe de Remise Exceptionnelle',
    )
    
    # ========== REMISES PAR DÉFAUT ==========
    customer_default_discount_1 = fields.Float(
        string='Remise Défaut Niveau 1 (%)',
        digits=(5, 2),
    )
    
    customer_default_discount_1_mode = fields.Selection([
        ('cumulative', 'Cumulative'),
        ('successive', 'Successive'),
    ], string='Mode Remise 1', default='successive')
    
    customer_default_discount_2 = fields.Float(
        string='Remise Défaut Niveau 2 (%)',
        digits=(5, 2),
    )
    
    customer_default_discount_2_mode = fields.Selection([
        ('cumulative', 'Cumulative'),
        ('successive', 'Successive'),
    ], string='Mode Remise 2', default='successive')
    
    customer_default_discount_3 = fields.Float(
        string='Remise Défaut Niveau 3 (%)',
        digits=(5, 2),
    )
    
    customer_default_discount_3_mode = fields.Selection([
        ('cumulative', 'Cumulative'),
        ('successive', 'Successive'),
    ], string='Mode Remise 3', default='successive')
    
    # ========== REMISE EXCEPTIONNELLE R99 ==========
    customer_exceptional_r99 = fields.Float(
        string='Remise Exceptionnelle R99 (%)',
        digits=(5, 2),
    )
    
    customer_r99_date_start = fields.Date(string='Date Début R99')
    customer_r99_date_end = fields.Date(string='Date Fin R99')
    
    # ========== PIED DE FACTURE ==========
    customer_foot_invoice_discount = fields.Float(
        string='Remise Pied de Facture (%)',
        digits=(5, 2),
    )
    
    # ========== PRÉFÉRENCES ==========
    customer_price_decimal_precision = fields.Selection([
        ('2', '2 décimales'),
        ('3', '3 décimales'),
    ], string='Précision Prix Client', default='2')
    
    customer_rounding_method = fields.Selection([
        ('up', 'Arrondi supérieur'),
        ('down', 'Arrondi inférieur'),
        ('nearest', 'Arrondi au plus proche'),
    ], string='Méthode d\'Arrondi', default='nearest')