def _match_customer(self, partner):
        """Vérifie si le client correspond aux critères de la règle."""
        if not self.customer_ids and not self.customer_group_ids \
           and not self.customer_tariff_family and not self.customer_tariff_exceptional \
           and not self.customer_code_tariff:
            return True
        
        if partner in self.customer_ids:
            return True
        
        partner_groups = partner.client_segmentation_group_ids or self.env['client.segmentation.group']
        if self.customer_group_ids & partner_groups:
            return True
        
        if self.customer_tariff_family and partner.customer_tariff_family == self.customer_tariff_family:
            return True
        
        if self.customer_tariff_exceptional and partner.customer_tariff_exceptional == self.customer_tariff_exceptional:
            return True
        
        if self.customer_code_tariff and partner.customer_tariff_code == self.customer_code_tariff:
            return True
        
        return False

    def _match_product(self, product):
        """Vérifie si le produit correspond aux critères de la règle."""
        if self.use_reference_price and self.reference_product_id:
            return product == self.reference_product_id
        
        if not self.product_ids and not self.product_template_ids \
           and not self.product_category_ids and not self.product_group_ids:
            if not self.use_reference_price:
                return True
        
        if product in self.product_ids:
            return True
        
        if product.product_tmpl_id in self.product_template_ids:
            return True
        
        categ_path = product.categ_id.parent_path.split('/')
        categ_ids = [int(c) for c in categ_path if c.isdigit()]
        if self.product_category_ids.filtered(lambda c: c.id in categ_ids):
            return True
        
        if self.product_group_ids & product.product_pricing_group_ids:
            return True
        
        return False