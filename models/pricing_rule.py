# -*- coding: utf-8 -*-
"""
Règles Tarifaires - Coeur du moteur de tarification

Gère la détermination des prix selon la logique d'entonnoir :
1. Tarif promotionnel prioritaire (OLIM, BR)
2. Tarif spécifique client (TS, CR, CU)
3. Tarif général (TG)
4. Repli sur conditions par défaut
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class PricingRule(models.Model):
    _name = 'pricing.rule'
    _description = 'Règle Tarifaire'
    _order = 'priority desc, date_start desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Code Tarif', required=True, tracking=True,
                       help="Code identifiant le tarif (ex: TG, TS, OLIM, BR, CU...)")
    
    code = fields.Char(string='Référence', required=True, copy=False,
                       help="Référence unique du tarif")
    
    active = fields.Boolean(default=True)
    
    # Type de prix
    price_type = fields.Selection([
        ('brut', 'Prix Brut (remisable)'),
        ('net', 'Prix Net (non remisable sauf pied)'),
    ], string='Type de Prix', default='brut', required=True, tracking=True)
    
    # Devise et unité
    currency_id = fields.Many2one('res.currency', string='Devise', 
                                   default=lambda self: self.env.company.currency_id,
                                   required=True)
    is_ht = fields.Boolean(string='Prix HT', default=True)
    
    # Période de validité
    date_start = fields.Date(string='Date de début', required=True, tracking=True,
                             default=fields.Date.context_today)
    date_end = fields.Date(string='Date de fin', tracking=True)
    
    # Priorité (plus le nombre est élevé, plus la règle est prioritaire)
    priority = fields.Integer(string='Priorité', default=10,
                              help="Promotion=100, Spécifique=50, Général=10")
    
    # Segmentations clients
    customer_ids = fields.Many2many('res.partner', string='Clients',
                                    domain=[('customer_rank', '>', 0)])
    
    customer_group_ids = fields.Many2many('client.segmentation.group', 
                                          string='Groupes de Clients',
                                          domain=[('type', '=', 'customer')])
    
    customer_tariff_family = fields.Many2one('client.tariff.family', 
                                             string='Famille Tarifaire Client')
    
    customer_tariff_exceptional = fields.Many2one('client.tariff.exceptional',
                                                  string='Famille Exceptionnelle Client')
    
    customer_code_tariff = fields.Char(string='Code Tarif Client')
    
    # Segmentations produits
    product_ids = fields.Many2many('product.product', string='Produits',
                                   domain=[('sale_ok', '=', True)])
    
    product_template_ids = fields.Many2many('product.template', string='Modèles de Produits',
                                            domain=[('sale_ok', '=', True)])
    
    product_category_ids = fields.Many2many('product.category', string='Catégories de Produits')
    
    product_group_ids = fields.Many2many('product.pricing.group', 
                                         string='Groupes de Tarification Produit')
    
    # Reprise de tarif d'une autre référence
    use_reference_price = fields.Boolean(string='Utiliser le prix d\'une autre référence')
    reference_product_id = fields.Many2one('product.product', 
                                           string='Produit de référence',
                                           help="Le prix sera celui de ce produit de référence")
    
    # Prix
    fixed_price = fields.Float(string='Prix Fixe', digits='Product Price')
    
    # Dégressivité
    is_degressive = fields.Boolean(string='Tarif Dégressif')
    degressive_qty_intervals = fields.One2many('pricing.rule.degressive.qty', 
                                                'rule_id', 
                                                string='Paliers de Quantités')
    
    # Notes
    note = fields.Text(string='Commentaire')
    
    company_id = fields.Many2one('res.company', string='Société', 
                                 default=lambda self: self.env.company)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rule in self:
            if rule.date_end and rule.date_end < rule.date_start:
                raise ValidationError(_('La date de fin doit être postérieure à la date de début.'))

    @api.constrains('code')
    def _check_code_unique(self):
        for rule in self:
            existing = self.search([
                ('code', '=', rule.code),
                ('id', '!=', rule.id),
                ('company_id', '=', rule.company_id.id)
            ])
            if existing:
                raise ValidationError(_('Le code tarif doit être unique par société.'))

    def _match_customer(self, rule, partner):
        """Vérifie si le client correspond aux critères de la règle."""
        if not rule.customer_ids and not rule.customer_group_ids \
           and not rule.customer_tariff_family and not rule.customer_tariff_exceptional \
           and not rule.customer_code_tariff:
            return True
        
        if partner in rule.customer_ids:
            return True
        
        partner_groups = partner.client_segmentation_group_ids or self.env['client.segmentation.group']
        if rule.customer_group_ids & partner_groups:
            return True
        
        if rule.customer_tariff_family and partner.customer_tariff_family == rule.customer_tariff_family:
            return True
        
        if rule.customer_tariff_exceptional and partner.customer_tariff_exceptional == rule.customer_tariff_exceptional:
            return True
        
        if rule.customer_code_tariff and partner.customer_tariff_code == rule.customer_code_tariff:
            return True
        
        return False

    def _match_product(self, rule, product):
        """Vérifie si le produit correspond aux critères de la règle."""
        if rule.use_reference_price and rule.reference_product_id:
            return product == rule.reference_product_id
        
        if not rule.product_ids and not rule.product_template_ids \
           and not rule.product_category_ids and not rule.product_group_ids:
            if not rule.use_reference_price:
                return True
        
        if product in rule.product_ids:
            return True
        
        if product.product_tmpl_id in rule.product_template_ids:
            return True
        
        categ_path = product.categ_id.parent_path.split('/')
        categ_ids = [int(c) for c in categ_path if c.isdigit()]
        if rule.product_category_ids.filtered(lambda c: c.id in categ_ids):
            return True
        
        if rule.product_group_ids & product.product_pricing_group_ids:
            return True
        
        return False

    def _calculate_price(self, product, quantity, check_date):
        """Calcule le prix applicable selon la règle."""
        self.ensure_one()
        
        if self.use_reference_price and self.reference_product_id:
            base_price = self.reference_product_id.list_price
        elif self.fixed_price:
            base_price = self.fixed_price
        else:
            base_price = product.list_price
        
        if self.is_degressive and self.degressive_qty_intervals:
            base_price = self._apply_degressive_price(base_price, quantity)
        
        return base_price

    def _apply_degressive_price(self, base_price, quantity):
        """Applique les paliers dégressifs."""
        self.ensure_one()
        
        applicable_interval = self.degressive_qty_intervals.filtered(
            lambda i: i.min_quantity <= quantity
        ).sorted('min_quantity', reverse=True).limit(1)
        
        if applicable_interval:
            if applicable_interval.price_type == 'fixed':
                return applicable_interval.fixed_price
            elif applicable_interval.price_type == 'discount':
                return base_price * (1 - applicable_interval.discount_percent / 100)
        
        return base_price


class PricingRuleDegressiveQty(models.Model):
    _name = 'pricing.rule.degressive.qty'
    _description = 'Palier de Quantité Dégressif'
    _order = 'min_quantity asc'

    rule_id = fields.Many2one('pricing.rule', string='Règle Tarifaire', 
                              required=True, ondelete='cascade')
    
    min_quantity = fields.Float(string='Quantité minimum', required=True, default=1.0)
    
    price_type = fields.Selection([
        ('fixed', 'Prix Fixe'),
        ('discount', 'Remise %'),
    ], string='Type', required=True, default='fixed')
    
    fixed_price = fields.Float(string='Prix Fixe', digits='Product Price')
    discount_percent = fields.Float(string='Remise %', digits=(5, 2))
    
    @api.constrains('min_quantity')
    def _check_positive_quantity(self):
        for interval in self:
            if interval.min_quantity <= 0:
                raise ValidationError(_('La quantité minimum doit être supérieure à 0.'))