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
    
    discount_rule_2_id = fields.Many2one(
        'discount.rule', string='Règle Remise Niveau 2', readonly=True)
    
    discount_rule_3_id = fields.Many2one(
        'discount.rule', string='Règle Remise Niveau 3', readonly=True)
    
    # ========== PROMO ==========
    promotion_applied_id = fields.Many2one(
        'pricing.promotion', string='Promotion Appliquée', readonly=True)
    
    # ========== PRIX DÉTAILLÉS ==========
    price_base = fields.Monetary(
        string='Prix de Base', readonly=True,
        help="Prix avant toute remise (issu de la règle tarifaire)")
    
    price_after_discounts = fields.Monetary(
        string='Prix après Remises Ligne', readonly=True)
    
    total_discount_percent = fields.Float(
        string='Taux de Remise Total (%)', readonly=True, digits=(5, 2))
    
    total_discount_amount = fields.Monetary(
        string='Montant Total Remise', readonly=True)
    
    # ========== DATE DE COMMANDE (différente de saisie) ==========
    order_date_override = fields.Date(
        string='Date de Commande',
        help="Date de commande effective (peut être différente de la date de saisie)")
    
    def _get_effective_order_date(self):
        """Retourne la date à utiliser pour le calcul tarifaire."""
        self.ensure_one()
        return self.order_date_override or self.order_id.date_order or fields.Date.context_today(self)

    @api.onchange('product_id', 'product_uom_qty', 'order_id.partner_id')
    def _onchange_product_compute_price(self):
        """Calcul automatique déclenché à la saisie."""
        for line in self:
            if not line.product_id or not line.order_id.partner_id:
                continue
            
            effective_date = line._get_effective_order_date()
            
            pricing_result = line._compute_apic_pricing(
                product_id=line.product_id.id,
                partner_id=line.order_id.partner_id.id,
                order_date=effective_date,
                quantity=line.product_uom_qty
            )
            
            if pricing_result:
                line.price_unit = pricing_result.get('final_price', line.price_unit)
                line.price_base = pricing_result.get('base_price', line.price_unit)
                line.price_after_discounts = pricing_result.get('final_price', line.price_unit)
                line.pricing_rule_applied_id = pricing_result.get('rule_id')
                line.pricing_rule_code = pricing_result.get('rule_code', '')
                line.price_type_applied = pricing_result.get('price_type', 'brut')
                line.promotion_applied_id = pricing_result.get('promotion_id')
                line.total_discount_percent = pricing_result.get('total_discount_percent', 0.0)
                line.total_discount_amount = pricing_result.get('total_discount_amount', 0.0)
                line.discount_traceability = pricing_result.get('traceability', {})
                
                discounts = pricing_result.get('discounts', [])
                if len(discounts) >= 1:
                    line.discount_rule_1_id = discounts[0].get('rule_id')
                if len(discounts) >= 2:
                    line.discount_rule_2_id = discounts[1].get('rule_id')
                if len(discounts) >= 3:
                    line.discount_rule_3_id = discounts[2].get('rule_id')
        
        return super(SaleOrderLine, self)._onchange_product_compute_price()

    def _compute_apic_pricing(self, product_id, partner_id, order_date, quantity):
        """Appelle le moteur de tarification APIC."""
        self.ensure_one()
        
        pricing_engine = self.env['pricing.engine.service']
        
        result = pricing_engine.calculate_full_pricing(
            product_id=product_id,
            partner_id=partner_id,
            order_date=order_date,
            quantity=quantity,
            currency_id=self.order_id.currency_id.id
        )
        
        return result

    def action_view_pricing_traceability(self):
        """Affiche le détail complet du calcul tarifaire."""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Traçabilité du Calcul Tarifaire'),
            'res_model': 'pricing.traceability.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_line_id': self.id,
                'default_product_id': self.product_id.id,
                'default_partner_id': self.order_id.partner_id.id,
                'default_order_date': self._get_effective_order_date(),
                'default_quantity': self.product_uom_qty,
            }
        }