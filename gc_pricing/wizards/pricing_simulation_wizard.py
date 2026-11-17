# -*- coding: utf-8 -*-
"""
Wizard de Simulation Tarifaire

Permet de tester une combinaison client/article/date/quantité
et voir le résultat complet du calcul tarifaire avant saisie.
"""

from odoo import models, fields, api, _


class PricingSimulationWizard(models.TransientModel):
    _name = 'pricing.simulation.wizard'
    _description = 'Simulation Tarifaire'

    partner_id = fields.Many2one('res.partner', string='Client', required=True)
    product_id = fields.Many2one('product.product', string='Produit', required=True)
    order_date = fields.Datetime(string='Date de Commande', 
                                  default=fields.Datetime.now, required=True)
    quantity = fields.Float(string='Quantité', default=1.0, required=True)
    
    base_price = fields.Float(string='Prix de Base', readonly=True, digits='Product Price')
    pricing_rule_code = fields.Char(string='Code Tarif', readonly=True)
    pricing_rule_name = fields.Char(string='Règle Tarifaire', readonly=True)
    price_type = fields.Selection([('brut', 'Prix Brut'), ('net', 'Prix Net')], 
                                   string='Type de Prix', readonly=True)
    
    promotion_applied = fields.Char(string='Promotion Appliquée', readonly=True)
    discount_details = fields.Text(string='Détail des Remises', readonly=True)
    total_discount_percent = fields.Float(string='Remise Totale (%)', 
                                           readonly=True, digits=(5, 2))
    
    final_price = fields.Float(string='Prix Final Unitaires', 
                                readonly=True, digits='Product Price')
    final_total = fields.Float(string='Montant Total', readonly=True, digits='Product Price')
    
    state = fields.Selection([('draft', 'À simuler'), ('calculated', 'Calculé')], 
                             string='État', default='draft')

    def action_calculate(self):
        """Lance le calcul tarifaire."""
        self.ensure_one()
        
        engine = self.env['pricing.engine.service']
        
        result = engine.calculate_full_pricing(
            product_id=self.product_id.id,
            partner_id=self.partner_id.id,
            order_date=self.order_date,
            quantity=self.quantity,
            currency_id=self.env.company.currency_id.id
        )
        
        discount_text = ""
        for disc in result.get('discounts', []):
            mode_label = "Cumul" if disc.get('application_mode') == 'cumulative' else "Successif"
            discount_text += f"- {disc.get('rule_code', 'N/A')}: {disc.get('discount_value', 0)}% ({mode_label})\n"
        
        if not discount_text:
            discount_text = "Aucune remise applicable"
        
        self.write({
            'base_price': result.get('base_price', 0.0),
            'pricing_rule_code': result.get('rule_code', ''),
            'pricing_rule_name': result.get('traceability', {}).get('pricing_rule', {}).get('name', ''),
            'price_type': result.get('price_type', 'brut'),
            'promotion_applied': result.get('traceability', {}).get('promotion', {}).get('code', '') or '-',
            'discount_details': discount_text,
            'total_discount_percent': result.get('total_discount_percent', 0.0),
            'final_price': result.get('final_price', 0.0),
            'final_total': result.get('final_price', 0.0) * self.quantity,
            'state': 'calculated',
        })
        
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_new_simulation(self):
        """Réinitialise pour une nouvelle simulation."""
        self.write({
            'base_price': 0.0, 'pricing_rule_code': '', 'pricing_rule_name': '',
            'price_type': False, 'promotion_applied': '', 'discount_details': '',
            'total_discount_percent': 0.0, 'final_price': 0.0, 'final_total': 0.0,
            'state': 'draft',
        })
        
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}