# 4a. Chercher d'abord une règle avec le code exact du client
        for rule in all_rules:
            if rule.code == tariff_code and rule.code != 'TG':
                # Appel direct sur l'instance rule, pas sur le modèle
                if rule._match_product(product) and rule._match_customer(partner):
                    price = rule._calculate_price(product, quantity, order_date)
                    return {
                        'price': price,
                        'rule': rule,
                        'price_type': rule.price_type,
                        'promotion': None,
                    }
        
        # 4b. Si pas trouvé, chercher TG (s'applique à tous si pas de critères clients)
        tg_rule = all_rules.filtered(lambda r: r.code == 'TG')
        for rule in tg_rule:
            # Pour TG, on vérifie produit ET client - appel direct sur l'instance
            if rule._match_product(product) and rule._match_customer(partner):
                price = rule._calculate_price(product, quantity, order_date)
                return {
                    'price': price,
                    'rule': rule,
                    'price_type': rule.price_type,
                    'promotion': None,
                }