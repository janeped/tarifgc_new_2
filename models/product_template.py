# -*- coding: utf-8 -*-
"""
Extension product.template / product.product - Champs tarifaires produits
"""

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ========== SEGMENTATION PRODUIT ==========
    product_pricing_group_ids = fields.Many2many(
        'product.pricing.group',
        string='Groupes de Tarification',
    )
    
    product_exceptional_discount_class_id = fields.Many2one(
        'product.discount.exceptional',
        string='Classe de Remise Exceptionnelle',
    )
    
    product_promotional_family_id = fields.Many2one(
        'product.promotional.family',
        string='Famille Promotionnelle',
    )
    
    # ========== PILOTAGE PAR AUTRE RÉFÉRENCE ==========
    use_reference_pricing = fields.Boolean(
        string='Utiliser le tarif d\'une autre référence',
        help="Si coché, le prix de ce produit sera celui de la référence spécifiée"
    )
    
    reference_product_id = fields.Many2one(
        'product.product',
        string='Référence de Substitution',
        help="Référence dont le tarif sera utilisé (ex: RFIMO454 pour FIMO coloris)"
    )
    
    # ========== TYPE DE PRIX ==========
    price_type_default = fields.Selection([
        ('brut', 'Prix Brut (remisable)'),
        ('net', 'Prix Net (non remisable sauf pied)'),
    ], string='Type de Prix par Défaut', default='brut')
    
    # ========== EXCLUSIONS ==========
    exclude_from_all_discounts = fields.Boolean(
        string='Exclure de toutes remises ligne',
        help="Si coché, aucune remise ligne ne s'applique sur ce produit"
    )
    
    exclude_from_promotions = fields.Boolean(
        string='Exclure des promotions',
    )
    
    # ========== KITS / DÉCOMPOSITIONS ==========
    is_kit_composite = fields.Boolean(
        string='Article Composé (Kit)',
    )
    
    kit_valuation_method = fields.Selection([
        ('composite', 'Valorisation au composé'),
        ('components', 'Valorisation aux composants'),
    ], string='Méthode de Valorisation Kit', default='composite')
    
    # ========== PRÉFÉRENCES D'ARRONDI ==========
    price_decimal_precision = fields.Selection([
        ('2', '2 décimales'),
        ('3', '3 décimales'),
    ], string='Précision Prix Produit', default='2')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Héritage des champs template
    product_pricing_group_ids = fields.Many2many(
        related='product_tmpl_id.product_pricing_group_ids',
        readonly=False
    )
    
    product_exceptional_discount_class_id = fields.Many2one(
        related='product_tmpl_id.product_exceptional_discount_class_id',
        readonly=False
    )
    
    use_reference_pricing = fields.Boolean(
        related='product_tmpl_id.use_reference_pricing',
        readonly=False
    )
    
    reference_product_id = fields.Many2one(
        related='product_tmpl_id.reference_product_id',
        readonly=False
    )
    
    price_type_default = fields.Selection(
        related='product_tmpl_id.price_type_default',
        readonly=False
    )
    
    exclude_from_all_discounts = fields.Boolean(
        related='product_tmpl_id.exclude_from_all_discounts',
        readonly=False
    )
    
    is_kit_composite = fields.Boolean(
        related='product_tmpl_id.is_kit_composite',
        readonly=False
    )
    
    kit_valuation_method = fields.Selection(
        related='product_tmpl_id.kit_valuation_method',
        readonly=False
    )