# -*- coding: utf-8 -*-
"""
Moteur de Tarification APIC - Service Central

Coeur du système de calcul tarifaire.
Implémente la logique d'entonnoir complète :
1. Promotions prioritaires (OLIM, BR)
2. Tarifs spécifiques client (TS, CR, CU)
3. Tarif général (TG)
4. Repli sur conditions par défaut

Puis applique les remises dans l'ordre :
1. R99 (exclusive) si présente
2. Code remise promotionnelle (RPCREARE)
3. Code remise standard (RCREAREF)
4. Remises client par défaut
"""

from odoo import models, api, _
from odoo.tools import float_round
from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)


class PricingEngineService(models.AbstractModel):
    _name = 'pricing.engine.service'
    _description = 'Service Moteur de Tarification APIC'

    @api.model
    def calculate_full_pricing(self, product_id, partner_id, order_date=None,
                                quantity=1.0, currency_id=None):
        """
        Méthode principale de calcul tarifaire complet.
        """
        product = self.env['product.product'].browse(product_id)
        partner = self.env['res.partner'].browse(partner_id)
        currency = self.env['res.currency'].browse(currency_id) if currency_id else self.env.company.currency_id
        
        check_datetime = order_date or fields.Datetime.now(self)
        if isinstance(check_datetime, date) and not isinstance(check_datetime, datetime):
            check_datetime = datetime.combine(check_datetime, datetime.min.time())
        
        _logger.info(f"[APIC Pricing] Calcul pour produit={product.name}, client={partner.name}, date={check_datetime}, qty={quantity}")
        
        # ÉTAPE 1: Déterminer le prix de base via l'entonnoir tarifaire
        price_result = self._determine_base_price(
            product=product, partner=partner, order_date=check_datetime,
            quantity=quantity, currency=currency
        )
        
        base_price = price_result['price']
        pricing_rule = price_result['rule']
        price_type = price_result.get('price_type', 'brut')
        promotion_applied = price_result.get('promotion')
        
        # ÉTAPE 2: Déterminer les remises applicables
        discounts_result = self._determine_discounts(
            product=product, partner=partner, order_date=check_datetime,
            quantity=quantity, base_price=base_price, price_type=price_type,
            promotion=promotion_applied
        )
        
        discounts = discounts_result['discounts']
        is_r99_exclusive = discounts_result.get('is_r99_exclusive', False)
        
        # ÉTAPE 3: Calculer le prix final après remises
        calculation = self._calculate_final_price(
            base_price=base_price, discounts=discounts, quantity=quantity,
            partner=partner, product=product
        )
        
        final_price = calculation['final_unit_price']
        total_discount_percent = calculation['total_discount_percent']
        total_discount_amount = calculation['total_discount_amount']
        
        # ÉTAPE 4: Construire la traçabilité
        traceability = self._build_traceability(
            product=product, partner=partner, order_date=check_datetime,
            quantity=quantity, pricing_rule=pricing_rule, promotion=promotion_applied,
            discounts=discounts, base_price=base_price, final_price=final_price,
            total_discount_percent=total_discount_percent,
            calculation_details=calculation
        )
        
        return {
            'base_price': base_price,
            'final_price': final_price,
            'price_type': price_type,
            'rule_id': pricing_rule.id if pricing_rule else False,
            'rule_code': pricing_rule.code if pricing_rule else '',
            'promotion_id': promotion_applied.id if promotion_applied else False,
            'discounts': discounts,
            'total_discount_percent': total_discount_percent,
            'total_discount_amount': total_discount_amount,
            'traceability': traceability,
            'is_r99_exclusive': is_r99_exclusive,
        }

    def _determine_base_price(self, product, partner, order_date, quantity, currency):
        """Détermine le prix de base selon la logique d'entonnoir."""
        # Vérifier pilotage par autre référence
        if product.use_reference_pricing and product.reference_product_id:
            return self._determine_base_price(
                product=product.reference_product_id, partner=partner,
                order_date=order_date, quantity=quantity, currency=currency
            )
        
        # 1. Chercher promotions actives prioritaires (OLIM, BR)
        promotion_model = self.env['pricing.promotion']
        active_promotions = promotion_model.get_active_promotions(
            product_id=product.id, partner_id=partner.id, order_date=order_date
        )
        
        if active_promotions:
            best_promo = active_promotions[0]
            promo_price = best_promo.apply_promotion_price(product.list_price, product)
            return {
                'price': promo_price,
                'rule': self.env['pricing.rule'],
                'price_type': 'net' if best_promo.promo_is_net_price else 'brut',
                'promotion': best_promo,
            }
        
        # 2. Chercher tarif spécifique client (CR, CU, TS)
        tariff_code = partner.customer_tariff_code or 'TG'
        
        pricing_rule_model = self.env['pricing.rule']
        specific_rule = pricing_rule_model.search([
            ('code', '=', tariff_code),
            ('active', '=', True),
            '|', ('date_start', '<=', order_date.date() if hasattr(order_date, 'date') else order_date),
            ('date_start', '=', False),
            '|', ('date_end', '>=', order_date.date() if hasattr(order_date, 'date') else order_date),
            ('date_end', '=', False),
        ], limit=1, order='priority desc, date_start desc')
        
        if specific_rule and specific_rule.code != 'TG':
            if pricing_rule_model._match_product(specific_rule, product):
                price = specific_rule._calculate_price(product, quantity, order_date)
                return {
                    'price': price,
                    'rule': specific_rule,
                    'price_type': specific_rule.price_type,
                    'promotion': None,
                }
        
        # 3. Rechercher tarif général TG
        tg_rule = pricing_rule_model.search([
            ('code', '=', 'TG'),
            ('active', '=', True),
            '|', ('date_start', '<=', order_date.date() if hasattr(order_date, 'date') else order_date),
            ('date_start', '=', False),
            '|', ('date_end', '>=', order_date.date() if hasattr(order_date, 'date') else order_date),
            ('date_end', '=', False),
        ], limit=1, order='priority desc, date_start desc')
        
        if tg_rule:
            if pricing_rule_model._match_product(tg_rule, product):
                price = tg_rule._calculate_price(product, quantity, order_date)
                return {
                    'price': price,
                    'rule': tg_rule,
                    'price_type': tg_rule.price_type,
                    'promotion': None,
                }
        
        # 4. Repli sur prix de vente standard
        return {
            'price': product.list_price,
            'rule': self.env['pricing.rule'],
            'price_type': 'brut',
            'promotion': None,
        }

    def _determine_discounts(self, product, partner, order_date, quantity, base_price, price_type, promotion=None):
        """Détermine les remises applicables selon la hiérarchie."""
        discount_model = self.env['discount.rule']
        exclusion_model = self.env['pricing.exclusion']
        
        if product.exclude_from_all_discounts:
            return {'discounts': [], 'is_r99_exclusive': False}
        
        if exclusion_model.is_product_excluded_from_discount(product.id):
            return {'discounts': [], 'is_r99_exclusive': False}
        
        # Prix net non remisable (sauf R99 et pied)
        if price_type == 'net' and not promotion:
            r99_discounts = self._get_r99_discounts(partner, order_date, product)
            return {'discounts': r99_discounts, 'is_r99_exclusive': len(r99_discounts) > 0}
        
        discounts = []
        is_r99_exclusive = False
        
        # 1. Vérifier R99 (remise exceptionnelle exclusive)
        r99_discounts = self._get_r99_discounts(partner, order_date, product)
        if r99_discounts:
            return {'discounts': r99_discounts, 'is_r99_exclusive': True}
        
        # 2. Code remise promotionnelle (RPCREARE)
        if partner.customer_promotional_discount_code:
            promo_discount_rules = discount_model.search([
                ('code', '=', partner.customer_promotional_discount_code),
                ('active', '=', True),
            ])
            
            for rule in promo_discount_rules:
                if discount_model._match_product(rule, product) and discount_model._match_customer(rule, partner):
                    if quantity >= rule.min_quantity:
                        discounts.append({
                            'rule_id': rule.id,
                            'rule_code': rule.code,
                            'rule_name': rule.name,
                            'discount_value': rule.discount_value,
                            'discount_type': rule.discount_type,
                            'application_mode': rule.application_mode,
                            'level': rule.discount_level,
                        })
        
        # 3. Code remise standard (RCREAREF)
        if partner.customer_discount_code and not any(d.get('rule_code', '').startswith('RP') for d in discounts):
            standard_discount_rules = discount_model.search([
                ('code', '=', partner.customer_discount_code),
                ('active', '=', True),
            ])
            
            for rule in standard_discount_rules:
                if discount_model._match_product(rule, product) and discount_model._match_customer(rule, partner):
                    if quantity >= rule.min_quantity:
                        existing_levels = [d.get('level') for d in discounts]
                        if rule.discount_level not in existing_levels:
                            discounts.append({
                                'rule_id': rule.id,
                                'rule_code': rule.code,
                                'rule_name': rule.name,
                                'discount_value': rule.discount_value,
                                'discount_type': rule.discount_type,
                                'application_mode': rule.application_mode,
                                'level': rule.discount_level,
                            })
        
        # 4. Remises client par défaut (si pas encore 3 niveaux)
        while len(discounts) < 3:
            current_level = len(discounts) + 1
            discount_field = f'customer_default_discount_{current_level}'
            mode_field = f'customer_default_discount_{current_level}_mode'
            
            discount_percent = getattr(partner, discount_field, 0.0)
            if discount_percent > 0:
                discounts.append({
                    'rule_id': False,
                    'rule_code': f'DEFAULT_{current_level}',
                    'rule_name': f'Remise défaut niveau {current_level}',
                    'discount_value': discount_percent,
                    'discount_type': 'percent',
                    'application_mode': getattr(partner, mode_field, 'successive'),
                    'level': current_level,
                })
            else:
                break
        
        discounts.sort(key=lambda d: d.get('level', 99))
        
        return {'discounts': discounts[:3], 'is_r99_exclusive': is_r99_exclusive}

    def _get_r99_discounts(self, partner, order_date, product):
        """Récupère la remise exceptionnelle R99 si applicable."""
        check_date = order_date.date() if hasattr(order_date, 'date') else order_date
        
        r99_percent = partner.customer_exceptional_r99
        if r99_percent <= 0:
            return []
        
        # Vérifier bornage temporel
        date_start = partner.customer_r99_date_start
        date_end = partner.customer_r99_date_end
        
        if date_start and check_date < date_start:
            return []
        
        if date_end and check_date > date_end:
            return []
        
        # Vérifier exclusions produits
        exclusion_model = self.env['pricing.exclusion']
        if exclusion_model.is_product_excluded_from_discount(product.id):
            return []
        
        return [{
            'rule_id': False,
            'rule_code': 'R99',
            'rule_name': 'Remise Exceptionnelle R99',
            'discount_value': r99_percent,
            'discount_type': 'percent',
            'application_mode': 'successive',
            'level': 1,
            'is_exclusive': True,
        }]

    def _calculate_final_price(self, base_price, discounts, quantity, partner, product):
        """Calcule le prix final après application des remises."""
        current_price = base_price
        cumulative_percent = 0.0
        details = []
        
        cumulative_discounts = [d for d in discounts if d.get('application_mode') == 'cumulative']
        successive_discounts = [d for d in discounts if d.get('application_mode') == 'successive']
        
        # Additionner les pourcentages cumulatifs
        for disc in cumulative_discounts:
            if disc.get('discount_type') == 'percent':
                cumulative_percent += disc.get('discount_value', 0.0)
        
        # Appliquer remise cumulative
        if cumulative_percent > 0:
            discount_amount = current_price * (cumulative_percent / 100)
            current_price -= discount_amount
            details.append({
                'type': 'cumulative',
                'percent': cumulative_percent,
                'amount': discount_amount,
                'rules': [d.get('rule_code') for d in cumulative_discounts],
            })
        
        # Appliquer remises successives en cascade
        for disc in successive_discounts:
            if disc.get('discount_type') == 'percent':
                discount_amount = current_price * (disc.get('discount_value', 0.0) / 100)
                current_price -= discount_amount
                details.append({
                    'type': 'successive',
                    'percent': disc.get('discount_value', 0.0),
                    'amount': discount_amount,
                    'rule_code': disc.get('rule_code'),
                })
            elif disc.get('discount_type') == 'fixed':
                current_price -= disc.get('discount_value', 0.0)
                details.append({
                    'type': 'successive',
                    'fixed': disc.get('discount_value', 0.0),
                    'rule_code': disc.get('rule_code'),
                })
        
        # Arrondi selon préférences client
        precision = int(getattr(partner, 'customer_price_decimal_precision', '2') or '2')
        rounding_method = getattr(partner, 'customer_rounding_method', 'nearest')
        
        if rounding_method == 'up':
            final_price = float_round(current_price, precision_digits=precision, rounding_method='UP')
        elif rounding_method == 'down':
            final_price = float_round(current_price, precision_digits=precision, rounding_method='DOWN')
        else:
            # Règle Graine Créative : si 3ème décimale = 5 → arrondi supérieur
            final_price = float_round(current_price, precision_digits=precision, rounding_method='HALF-UP')
        
        if base_price > 0:
            total_effective_percent = ((base_price - final_price) / base_price) * 100
        else:
            total_effective_percent = 0.0
        
        return {
            'final_unit_price': final_price,
            'total_discount_percent': round(total_effective_percent, 2),
            'total_discount_amount': base_price - final_price,
            'details': details,
        }

    def _build_traceability(self, product, partner, order_date, quantity, pricing_rule,
                            promotion, discounts, base_price, final_price,
                            total_discount_percent, calculation_details):
        """Construit l'objet de traçabilité complet."""
        return {
            'product': {'id': product.id, 'name': product.name, 'default_code': product.default_code},
            'partner': {'id': partner.id, 'name': partner.name, 'ref': partner.ref},
            'order_date': str(order_date),
            'quantity': quantity,
            'pricing_rule': {
                'id': pricing_rule.id if pricing_rule else False,
                'code': pricing_rule.code if pricing_rule else '',
                'name': pricing_rule.name if pricing_rule else '',
            } if pricing_rule else None,
            'promotion': {
                'id': promotion.id if promotion else False,
                'code': promotion.code if promotion else '',
                'name': promotion.name if promotion else '',
            } if promotion else None,
            'base_price': base_price,
            'final_price': final_price,
            'total_discount_percent': total_discount_percent,
            'discounts_applied': discounts,
            'calculation_details': calculation_details.get('details', []),
            'timestamp': fields.Datetime.now(self),
        }