# -*- coding: utf-8 -*-
"""
Wizard de Visualisation de Traçabilité

Affiche le détail complet du calcul tarifaire pour une ligne de commande.
"""

from odoo import models, fields, api, _


class PricingTraceabilityWizard(models.TransientModel):
    _name = 'pricing.traceability.wizard'
    _description = 'Traçabilité du Calcul Tarifaire'

    sale_line_id = fields.Many2one('sale.order.line', string='Ligne de Commande', readonly=True)
    product_id = fields.Many2one('product.product', string='Produit', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True)
    order_date = fields.Date(string='Date de Commande', readonly=True)
    quantity = fields.Float(string='Quantité', readonly=True)
    
    pricing_rule_code = fields.Char(string='Code Tarif', readonly=True)
    pricing_rule_name = fields.Char(string='Règle Tarifaire', readonly=True)
    price_type = fields.Selection([('brut', 'Prix Brut'), ('net', 'Prix Net')], 
                                   string='Type de Prix', readonly=True)
    
    promotion_code = fields.Char(string='Code Promotion', readonly=True)
    promotion_name = fields.Char(string='Promotion', readonly=True)
    
    base_price = fields.Float(string='Prix de Base', readonly=True, digits='Product Price')
    
    discount_line_1 = fields.Char(string='Remise Niveau 1', readonly=True)
    discount_line_2 = fields.Char(string='Remise Niveau 2', readonly=True)
    discount_line_3 = fields.Char(string='Remise Niveau 3', readonly=True)
    
    total_discount_percent = fields.Float(string='Remise Totale (%)', readonly=True)
    total_discount_amount = fields.Float(string='Montant Remise', readonly=True)
    final_price = fields.Float(string='Prix Final', readonly=True, digits='Product Price')
    
    calculation_details = fields.Text(string='Détail du Calcul', readonly=True)
    full_traceability = fields.Json(string='Traçabilité JSON', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Charge les données depuis la ligne de commande."""
        res = super().default_get(fields_list)
        
        line_id = self.env.context.get('default_sale_line_id')
        if line_id:
            line = self.env['sale.order.line'].browse(line_id)
            
            res.update({
                'sale_line_id': line.id,
                'product_id': line.product_id.id,
                'partner_id': line.order_id.partner_id.id,
                'order_date': line._get_effective_order_date(),
                'quantity': line.product_uom_qty,
                'pricing_rule_code': line.pricing_rule_code,
                'pricing_rule_name': line.pricing_rule_applied_id.name if line.pricing_rule_applied_id else '',
                'price_type': line.price_type_applied,
                'base_price': line.price_base,
                'total_discount_percent': line.total_discount_percent,
                'total_discount_amount': line.total_discount_amount,
                'final_price': line.price_after_discounts,
            })
            
            traceability = line.discount_traceability or {}
            discounts = traceability.get('discounts_applied', [])
            
            if len(discounts) >= 1:
                d1 = discounts[0]
                res['discount_line_1'] = f"{d1.get('rule_code', 'N/A')}: {d1.get('discount_value', 0)}%"
            
            if len(discounts) >= 2:
                d2 = discounts[1]
                res['discount_line_2'] = f"{d2.get('rule_code', 'N/A')}: {d2.get('discount_value', 0)}%"
            
            if len(discounts) >= 3:
                d3 = discounts[2]
                res['discount_line_3'] = f"{d3.get('rule_code', 'N/A')}: {d3.get('discount_value', 0)}%"
            
            promo = traceability.get('promotion')
            if promo:
                res['promotion_code'] = promo.get('code', '')
                res['promotion_name'] = promo.get('name', '')
            
            res['full_traceability'] = traceability
        
        return res