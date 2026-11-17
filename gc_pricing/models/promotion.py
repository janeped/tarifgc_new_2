# -*- coding: utf-8 -*-
"""
Promotions - Conditions commerciales temporaires prioritaires

Gère les opérations promotionnelles bornées dans le temps :
- OLIM (promotions générales type Noël, Carnaval, Été)
- Promotions spécifiques par groupe de clients
- Priorité sur les tarifs permanents
- Date de commande différente de la date de saisie
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PricingPromotion(models.Model):
    _name = 'pricing.promotion'
    _description = 'Promotion Commerciale'
    _order = 'priority desc, date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom de la Promotion', required=True, tracking=True)
    code = fields.Char(string='Code Promotion', required=True, copy=False,
                       help="Code identifiant la promotion (ex: OLIM, RPCREARE, BR...)")
    
    active = fields.Boolean(default=True)
    
    # Période de validité OBLIGATOIRE pour les promotions
    date_start = fields.Datetime(string='Date et heure de début', required=True, tracking=True)
    date_end = fields.Datetime(string='Date et heure de fin', required=True, tracking=True)
    
    # Priorité très élevée par défaut pour les promotions
    priority = fields.Integer(string='Priorité', default=100,
                              help="Les promotions ont priorité sur les tarifs permanents.")
    
    # Type de promotion
    promotion_type = fields.Selection([
        ('price', 'Tarif Promotionnel'),
        ('discount', 'Remise Promotionnelle'),
        ('both', 'Tarif + Remise'),
    ], string='Type de Promotion', default='both', required=True)
    
    # Éligibilité clients
    customer_ids = fields.Many2many('res.partner', string='Clients Éligibles',
                                    domain=[('customer_rank', '>', '0')])
    
    customer_group_ids = fields.Many2many('client.segmentation.group',
                                          string='Groupes de Clients',
                                          domain=[('type', '=', 'customer')])
    
    is_available_to_all = fields.Boolean(string='Disponible à tous les clients', default=False)
    
    # Produits concernés
    product_ids = fields.Many2many('product.product', string='Produits en Promotion',
                                   domain=[('sale_ok', '=', True)])
    
    product_template_ids = fields.Many2many('product.template', string='Modèles de Produits',
                                            domain=[('sale_ok', '=', True)])
    
    product_category_ids = fields.Many2many('product.category', string='Catégories de Produits')
    
    is_available_to_all_products = fields.Boolean(string='Disponible sur tous les produits',
                                                   default=False)
    
    # Configuration tarifaire
    promo_price_type = fields.Selection([
        ('fixed', 'Prix Fixe'),
        ('discount_percent', 'Remise % sur tarif de base'),
        ('discount_fixed', 'Réduction montant fixe'),
    ], string='Type de Prix Promotionnel')
    
    promo_fixed_price = fields.Float(string='Prix Fixe Promotionnel', digits='Product Price')
    promo_discount_percent = fields.Float(string='Remise %', digits=(5, 2))
    promo_discount_amount = fields.Monetary(string='Réduction Montant', 
                                            currency_field='promo_currency_id')
    
    promo_currency_id = fields.Many2one('res.currency', string='Devise',
                                        default=lambda self: self.env.company.currency_id)
    
    promo_is_net_price = fields.Boolean(string='Prix Net (non remisable)', default=False)
    
    # Configuration remise promotionnelle
    promo_discount_rule_ids = fields.One2many('pricing.promotion.discount.line',
                                               'promotion_id',
                                               string='Règles de Remise Promotionnelles')
    
    # Exclusivité
    exclude_from_standard_discounts = fields.Boolean(
        string='Exclure des remises standards',
        help="Si coché, les remises client habituelles ne s'appliquent pas"
    )
    
    replaces_base_price = fields.Boolean(string='Remplace le prix de base', default=True)
    
    note = fields.Text(string='Commentaire')
    
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for promo in self:
            if promo.date_end <= promo.date_start:
                raise ValidationError(_('La date de fin doit être postérieure à la date de début.'))

    @api.constrains('code')
    def _check_code_unique(self):
        for promo in self:
            existing = self.search([
                ('code', '=', promo.code),
                ('id', '!=', promo.id),
                ('company_id', '=', promo.company_id.id)
            ])
            if existing:
                raise ValidationError(_('Le code promotion doit être unique par société.'))

    @api.model
    def get_active_promotions(self, product_id=None, partner_id=None, order_date=None):
        """Retourne les promotions actives à une date donnée."""
        check_datetime = order_date or fields.Datetime.now(self)
        
        domain = [
            ('active', '=', True),
            ('date_start', '<=', check_datetime),
            ('date_end', '>=', check_datetime),
        ]
        
        candidates = self.search(domain).sorted('priority', reverse=True)
        
        if not product_id and not partner_id:
            return candidates
        
        applicable = self.env['pricing.promotion']
        product = self.env['product.product'].browse(product_id) if product_id else None
        partner = self.env['res.partner'].browse(partner_id) if partner_id else None
        
        for promo in candidates:
            if partner and not promo._is_customer_eligible(partner):
                continue
            
            if product and not promo._is_product_eligible(product):
                continue
            
            applicable |= promo
        
        return applicable

    def _is_customer_eligible(self, partner):
        """Vérifie si le client est éligible à la promotion."""
        self.ensure_one()
        
        if self.is_available_to_all:
            return True
        
        if partner in self.customer_ids:
            return True
        
        partner_groups = partner.client_segmentation_group_ids or self.env['client.segmentation.group']
        if self.customer_group_ids & partner_groups:
            return True
        
        return False

    def _is_product_eligible(self, product):
        """Vérifie si le produit est éligible à la promotion."""
        self.ensure_one()
        
        if self.is_available_to_all_products:
            return True
        
        if product in self.product_ids:
            return True
        
        if product.product_tmpl_id in self.product_template_ids:
            return True
        
        categ_path = product.categ_id.parent_path.split('/')
        categ_ids = [int(c) for c in categ_path if c.isdigit()]
        if self.product_category_ids.filtered(lambda c: c.id in categ_ids):
            return True
        
        return False

    def apply_promotion_price(self, base_price, product=None):
        """Applique le prix promotionnel au prix de base."""
        self.ensure_one()
        
        if self.promotion_type not in ('price', 'both'):
            return base_price
        
        if self.promo_price_type == 'fixed':
            return self.promo_fixed_price
        
        elif self.promo_price_type == 'discount_percent':
            return base_price * (1 - self.promo_discount_percent / 100)
        
        elif self.promo_price_type == 'discount_fixed':
            return max(0, base_price - self.promo_discount_amount)
        
        return base_price


class PricingPromotionDiscountLine(models.Model):
    _name = 'pricing.promotion.discount.line'
    _description = 'Ligne de Remise Promotionnelle'
    _order = 'sequence, id'

    promotion_id = fields.Many2one('pricing.promotion', string='Promotion',
                                    required=True, ondelete='cascade')
    
    sequence = fields.Integer(string='Séquence', default=10)
    
    discount_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fixed', 'Montant Fixe'),
    ], string='Type de Remise', required=True, default='percent')
    
    discount_value = fields.Float(string='Valeur', digits=(5, 2), required=True)
    
    application_mode = fields.Selection([
        ('cumulative', 'Cumulative'),
        ('successive', 'Successive'),
    ], string='Mode d\'Application', required=True, default='successive')
    
    min_quantity = fields.Float(string='Quantité Minimum', default=1.0)
    
    note = fields.Char(string='Note')