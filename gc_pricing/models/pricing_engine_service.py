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
        
        # 2. Préparer la date pour comparaison
        if isinstance(order_date, datetime):
            check_date_str = order_date.date().strftime('%Y-%m-%d')
        elif isinstance(order_date, date):
            check_date_str = order_date.strftime('%Y-%m-%d')
        else:
            check_date_str = str(order_date)[:10]  # Prend juste YYYY-MM-DD
        
        _logger.info(f"[DEBUG] Date check: {check_date_str}")
        
        # 3. Chercher TOUTES les règles actives
        pricing_rule_model = self.env['pricing.rule']
        all_rules = pricing_rule_model.search([
            ('active', '=', True),
            '|', ('date_start', '<=', check_date_str),
            ('date_start', '=', False),
            '|', ('date_end', '>=', check_date_str),
            ('date_end', '=', False),
        ], order='priority desc, date_start desc')
        
        _logger.info(f"[DEBUG] Rules found: {len(all_rules)}")
        for r in all_rules:
            _logger.info(f"  - {r.code}: {r.name}, fixed={r.fixed_price}, customer_groups={len(r.customer_group_ids)}")
        
        # 4. Filtrer par code tarifaire du client
        tariff_code = partner.customer_tariff_code or 'TG'
        _logger.info(f"[DEBUG] Tarif code: '{tariff_code}'")
        
        # 4a. Chercher d'abord règles spécifiques (pas TG)
        for rule in all_rules:
            if rule.code == tariff_code and rule.code != 'TG':
                _logger.info(f"[DEBUG] Testing specific rule {rule.code}")
                try:
                    match_prod = rule._match_product(product)
                    match_cust = rule._match_customer(partner)
                    _logger.info(f"  match_product={match_prod}, match_customer={match_cust}")
                    if match_prod and match_cust:
                        price = rule._calculate_price(product, quantity, order_date)
                        _logger.info(f"  Price: {price}")
                        return {
                            'price': price,
                            'rule': rule,
                            'price_type': rule.price_type,
                            'promotion': None,
                        }
                except Exception as e:
                    _logger.error(f"[ERROR] Rule {rule.code} failed: {e}")
        
        # 4b. Chercher TG
        tg_rules = all_rules.filtered(lambda r: r.code == 'TG')
        _logger.info(f"[DEBUG] TG rules: {len(tg_rules)}")
        for rule in tg_rules:
            _logger.info(f"[DEBUG] Testing TG rule {rule.name}")
            try:
                match_prod = rule._match_product(product)
                match_cust = rule._match_customer(partner)
                _logger.info(f"  match_product={match_prod}, match_customer={match_cust}")
                _logger.info(f"  rule.customer_group_ids={rule.customer_group_ids}")
                _logger.info(f"  partner.client_segmentation_group_ids={partner.client_segmentation_group_ids}")
                if match_prod and match_cust:
                    price = rule._calculate_price(product, quantity, order_date)
                    _logger.info(f"  TG Price: {price}")
                    return {
                        'price': price,
                        'rule': rule,
                        'price_type': rule.price_type,
                        'promotion': None,
                    }
            except Exception as e:
                _logger.error(f"[ERROR] TG rule {rule.name} failed: {e}")
        
        # 5. Repli
        _logger.warning(f"[DEBUG] No rule matched, falling back to list_price={product.list_price}")
        return {
            'price': product.list_price,
            'rule': self.env['pricing.rule'],
            'price_type': 'brut',
            'promotion': None,
        }