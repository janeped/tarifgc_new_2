# -*- coding: utf-8 -*-
"""
Segmentation Produits - Classifications pour la tarification
"""

from odoo import models, fields, api, _


class ProductPricingGroup(models.Model):
    _name = 'product.pricing.group'
    _description = 'Groupe de Tarification Produit'
    _order = 'sequence, name'

    name = fields.Char(string='Nom du Groupe', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    sequence = fields.Integer(string='Séquence', default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('product.pricing.group', string='Groupe Parent')
    child_ids = fields.One2many('product.pricing.group', 'parent_id', string='Sous-groupes')
    product_ids = fields.One2many('product.product', 'product_pricing_group_id', string='Produits')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]


class ProductDiscountExceptional(models.Model):
    _name = 'product.discount.exceptional'
    _description = 'Classe de Remise Exceptionnelle Produit'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    default_discount_rule_ids = fields.Many2many('discount.rule',
                                                  string='Règles de Remise par Défaut')
    product_ids = fields.One2many('product.product', 
                                  'product_exceptional_discount_class_id',
                                  string='Produits')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]


class ProductPromotionalFamily(models.Model):
    _name = 'product.promotional.family'
    _description = 'Famille Promotionnelle Produit'
    _order = 'name'

    name = fields.Char(string='Nom de la Famille', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    promotional_code = fields.Char(string='Code Promotionnel')
    product_ids = fields.One2many('product.product',
                                  'product_promotional_family_id',
                                  string='Produits')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]