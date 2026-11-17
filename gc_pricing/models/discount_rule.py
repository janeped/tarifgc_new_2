# -*- coding: utf-8 -*-
"""
Règles de Remises - Gestion multi-niveaux

Supporte :
- 3 niveaux de remises maximum par ligne
- Remises cumulatives (additionnées) ou successives (en cascade)
- Exceptions par client/article/groupe
- Bornage temporel optionnel
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class DiscountRule(models.Model):
    _name = 'discount.rule'
    _description = 'Règle de Remise'
    _order = 'priority desc, date_start desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    code = fields.Char(string='Code Remise', required=True, copy=False)
    
    active = fields.Boolean(default=True)
    
    discount_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fixed', 'Montant Fixe'),
    ], string='Type de Remise', default='percent', required=True)
    
    discount_value = fields.Float(string='Valeur Remise', digits=(5, 2), required=True)
    
    application_mode = fields.Selection([
        ('cumulative', 'Cumulative (additionnée)'),
        ('successive', 'Successive (en cascade)'),
    ], string='Mode d\'Application', default='successive', required=True)
    
    discount_level = fields.Integer(string='Niveau de Remise', default=1)
    
    priority = fields.Integer(string='Priorité', default=10)
    
    date_start = fields.Date(string='Date de début')
    date_end = fields.Date(string='Date de fin')
    
    customer_ids = fields.Many2many('res.partner', string='Clients',
                                    domain=[('customer_rank', '>', 0)])
    
    customer_group_ids = fields.Many2many('client.segmentation.group', 
                                          string='Groupes de Clients',
                                          domain=[('type', '=', 'customer')])
    
    customer_code_discount = fields.Char(string='Code Remise Client')
    customer_exceptional_class = fields.Many2one('client.discount.exceptional',
                                                  string='Classe de Remise Exceptionnelle')
    
    product_ids = fields.Many2many('product.product', string='Produits',
                                   domain=[('sale_ok', '=', True)])
    
    product_template_ids = fields.Many2many('product.template', string='Modèles de Produits',
                                            domain=[('sale_ok', '=', True)])
    
    product_category_ids = fields.Many2many('product.category', string='Catégories de Produits')
    
    product_group_ids = fields.Many2many('product.pricing.group', 
                                         string='Groupes de Tarification Produit')
    
    product_exceptional_class = fields.Many2one('product.discount.exceptional',
                                                 string='Classe de Remise Exceptionnelle Produit')
    
    is_exclusive = fields.Boolean(string='Remise Exclusive (R99)',
                                  help="Si coché, cette remplace toutes les autres remises ligne")
    
    min_quantity = fields.Float(string='Quantité Minimum', default=1.0)
    
    min_amount = fields.Monetary(string='Montant Minimum', currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)
    
    apply_on_net_price = fields.Boolean(string='Applicable sur Prix Net', default=False)
    
    note = fields.Text(string='Commentaire')
    
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rule in self:
            if rule.date_start and rule.date_end and rule.date_end < rule.date_start:
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
                raise ValidationError(_('Le code remise doit être unique par société.'))

    @api.constrains('discount_level')
    def _check_discount_level(self):
        for rule in self:
            if not 1 <= rule.discount_level <= 3:
                raise ValidationError(_('Le niveau de remise doit être entre 1 et 3.'))

    def _match_customer(self, rule, partner):
        """Vérifie si le client correspond aux critères."""
        if not rule.customer_ids and not rule.customer_group_ids \
           and not rule.customer_code_discount and not rule.customer_exceptional_class:
            return True
        
        if partner in rule.customer_ids:
            return True
        
        partner_groups = partner.client_segmentation_group_ids or self.env['client.segmentation.group']
        if rule.customer_group_ids & partner_groups:
            return True
        
        if rule.customer_code_discount and partner.customer_discount_code == rule.customer_code_discount:
            return True
        
        if rule.customer_exceptional_class and partner.customer_exceptional_discount_class == rule.customer_exceptional_class:
            return True
        
        return False

    def _match_product(self, rule, product):
        """Vérifie si le produit correspond aux critères."""
        if not rule.product_ids and not rule.product_template_ids \
           and not rule.product_category_ids and not rule.product_group_ids \
           and not rule.product_exceptional_class:
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
        
        if rule.product_exceptional_class and product.product_exceptional_discount_class == rule.product_exceptional_class:
            return True
        
        return False