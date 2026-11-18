# -*- coding: utf-8 -*-
"""
Extension sale.order.line - Calcul automatique des prix et remises

Intègre le moteur de tarification APIC dans les lignes de commande.
Calcul automatique à la saisie avec traçabilité complète.
"""

from odoo import models, fields, api, _
from odoo.tools import float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ========== TRAÇABILITÉ TARIFAIRE ==========
    pricing_rule_applied_id = fields.Many2one(
        'pricing.rule', string='Règle Tarifaire Appliquée', readonly=True)
    
    pricing_rule_code = fields.Char(
        string='Code Tarif Appliqué', readonly=True)
    
    price_type_applied = fields.Selection([
        ('brut', 'Prix Brut'),
        ('net', 'Prix Net'),
    ], string='Type de Prix', readonly=True)
    
    # ========== TRAÇABILITÉ REMISES ==========
    discount_traceability = fields.Json(
        string='Traçabilité des Remises', readonly=True)
    
    discount_rule_1_id = fields.Many2one(
        'discount.rule', string='Règle Remise Niveau 1', readonly=True)
    
    discount_rule_2_id = fieldsMany2one_placeholder = None