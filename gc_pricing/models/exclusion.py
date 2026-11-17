# -*- coding: utf-8 -*-
"""
Exclusions - Gestion des exceptions négatives

Permet d'exclure automatiquement :
- Un produit d'une remise de sa famille
- Une gamme d'une promotion générale
- Un client d'une opération commerciale
- Une famille de clients d'un tarif promotionnel
- Un tarif net de remises complémentaires
"""

from odoo import models, fields, api, _


class PricingExclusion(models.Model):
    _name = 'pricing.exclusion'
    _description = 'Exclusion Commerciale'
    _order = 'priority desc, id desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nom de l\'Exclusion', required=True)
    
    active = fields.Boolean(default=True)
    
    priority = fields.Integer(string='Priorité', default=10)
    
    exclusion_type = fields.Selection([
        ('product_from_discount', 'Produit exclu d\'une remise'),
        ('product_from_promotion', 'Produit exclu d\'une promotion'),
        ('customer_from_discount', 'Client exclu d\'une remise'),
        ('customer_from_promotion', 'Client exclu d\'une promotion'),
        ('customer_from_tariff', 'Client exclu d\'un tarif'),
        ('group_from_discount', 'Groupe exclu d\'une remise'),
        ('group_from_promotion', 'Groupe exclu d\'une promotion'),
        ('net_price_from_discount', 'Tarif net exclu de remises'),
    ], string="Type d'Exclusion", required=True)
    
    # Produit concerné
    product_ids = fields.Many2many('product.product', string='Produits Exclus',
                                   domain=[('sale_ok', '=', True)])
    
    product_template_ids = fields.Many2many('product.template', string='Modèles de Produits')
    
    product_category_ids = fields.Many2many('product.category', string='Catégories de Produits')
    
    product_group_ids = fields.Many2many('product.pricing.group', 
                                         string='Groupes de Produits Exclus')
    
    # Client concerné
    customer_ids = fields.Many2many('res.partner', string='Clients Exclus',
                                    domain=[('customer_rank', '>', 0)])
    
    customer_group_ids = fields.Many2many('client.segmentation.group',
                                          string='Groupes de Clients Exclus',
                                          domain=[('type', '=', 'customer')])
    
    # Remise/Promotion/Tarif dont on exclut
    discount_rule_ids = fields.Many2many('discount.rule', string='Règles de Remise Exclues')
    
    promotion_ids = fields.Many2many('pricing.promotion', string='Promotions Exclues')
    
    pricing_rule_ids = fields.Many2many('pricing.rule', string='Règles Tarifaires Exclues')
    
    # Scope de l'exclusion
    exclude_from_all_discounts = fields.Boolean(string='Exclure de TOUTES les remises',
                                                 help="Le produit/client est exclu de toute remise")
    
    exclude_from_all_promotions = fields.Boolean(string='Exclure de TOUTES les promotions')
    
    net_price_cannot_be_discounted = fields.Boolean(
        string='Prix Net Non Remisable',
        help="Si coché, les produits avec cette exclusion ne peuvent recevoir aucune remise ligne"
    )
    
    note = fields.Text(string='Commentaire')
    
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    def is_product_excluded_from_discount(self, product_id, discount_rule_id=None, 
                                           promotion_id=None):
        """Vérifie si un produit est exclu d'une remise ou promotion."""
        product = self.env['product.product'].browse(product_id)
        
        domain = [
            ('active', '=', True),
            ('exclusion_type', 'in', ['product_from_discount', 'product_from_promotion']),
        ]
        
        exclusions = self.search(domain)
        
        for excl in exclusions:
            if not self._match_product(excl, product):
                continue
            
            if excl.exclude_from_all_discounts and discount_rule_id:
                return True
            
            if excl.exclude_from_all_promotions and promotion_id:
                return True
            
            if discount_rule_id and discount_rule_id in excl.discount_rule_ids:
                return True
            
            if promotion_id and promotion_id in excl.promotion_ids:
                return True
        
        return False

    def is_customer_excluded_from_discount(self, partner_id, discount_rule_id=None,
                                            promotion_id=None, pricing_rule_id=None):
        """Vérifie si un client est exclu d'une remise/promotion/tarif."""
        partner = self.env['res.partner'].browse(partner_id)
        
        domain = [
            ('active', '=', True),
            ('exclusion_type', 'in', [
                'customer_from_discount', 
                'customer_from_promotion',
                'customer_from_tariff',
                'group_from_discount',
                'group_from_promotion',
            ]),
        ]
        
        exclusions = self.search(domain)
        
        for excl in exclusions:
            if not self._match_customer(excl, partner):
                continue
            
            if excl.exclude_from_all_discounts and discount_rule_id:
                return True
            
            if excl.exclude_from_all_promotions and promotion_id:
                return True
            
            if discount_rule_id and discount_rule_id in excl.discount_rule_ids:
                return True
            
            if promotion_id and promotion_id in excl.promotion_ids:
                return True
            
            if pricing_rule_id and pricing_rule_id in excl.pricing_rule_ids:
                return True
        
        return False

    def _match_product(self, exclusion, product):
        """Vérifie si le produit correspond aux critères d'exclusion."""
        if not exclusion.product_ids and not exclusion.product_template_ids \
           and not exclusion.product_category_ids and not exclusion.product_group_ids:
            return False
        
        if product in exclusion.product_ids:
            return True
        
        if product.product_tmpl_id in exclusion.product_template_ids:
            return True
        
        categ_path = product.categ_id.parent_path.split('/')
        categ_ids = [int(c) for c in categ_path if c.isdigit()]
        if exclusion.product_category_ids.filtered(lambda c: c.id in categ_ids):
            return True
        
        if exclusion.product_group_ids & product.product_pricing_group_ids:
            return True
        
        return False

    def _match_customer(self, exclusion, partner):
        """Vérifie si le client correspond aux critères d'exclusion."""
        if partner in exclusion.customer_ids:
            return True
        
        partner_groups = partner.client_segmentation_group_ids or self.env['client.segmentation.group']
        if exclusion.customer_group_ids & partner_groups:
            return True
        
        return False