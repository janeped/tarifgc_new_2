# -*- coding: utf-8 -*-
"""
Segmentation Clients - Classifications pour la tarification
"""

from odoo import models, fields, api, _


class ClientSegmentationGroup(models.Model):
    _name = 'client.segmentation.group'
    _description = 'Groupe de Segmentation Client'
    _order = 'sequence, name'

    name = fields.Char(string='Nom du Groupe', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    sequence = fields.Integer(string='Séquence', default=10)
    type = fields.Selection([
        ('customer', 'Clients'),
        ('supplier', 'Fournisseurs'),
        ('both', 'Les deux'),
    ], string='Type de Tiers', default='customer')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('client.segmentation.group', string='Groupe Parent')
    child_ids = fields.One2many('client.segmentation.group', 'parent_id', string='Sous-groupes')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]


class CustomerTariffFamily(models.Model):
    _name = 'client.tariff.family'
    _description = 'Famille Tarifaire Client'
    _order = 'name'

    name = fields.Char(string='Nom de la Famille', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    is_exceptional = fields.Boolean(string='Famille Exceptionnelle', default=False)
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]


class ClientTariffExceptional(models.Model):
    _name = 'client.tariff.exceptional'
    _description = 'Famille Tarifaire Exceptionnelle Client'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]


class ClientDiscountExceptional(models.Model):
    _name = 'client.discount.exceptional'
    _description = 'Classe de Remise Exceptionnelle Client'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    default_discount_rule_ids = fields.Many2many('discount.rule', 
                                                  string='Règles de Remise par Défaut')
    company_id = fields.Many2one('res.company', string='Société',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Le code doit être unique par société !')
    ]