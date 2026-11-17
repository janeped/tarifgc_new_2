# -*- coding: utf-8 -*-
"""
Wizard d'Import en Masse des Tarifs et Remises

Permet d'importer depuis Excel/CSV :
- Les grilles tarifaires (TG, TS, OLIM, etc.)
- Les règles de remises
- Les promotions
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    xlrd = None


class MassImportWizard(models.TransientModel):
    _name = 'pricing.mass.import.wizard'
    _description = 'Import en Masse des Tarifs et Remises'

    import_type = fields.Selection([
        ('pricing_rules', 'Règles Tarifaires'),
        ('discount_rules', 'Règles de Remises'),
        ('promotions', 'Promotions'),
    ], string="Type d'Import", required=True, default='pricing_rules')
    
    file_data = fields.Binary(string='Fichier Excel/CSV', required=True)
    file_name = fields.Char(string='Nom du Fichier')
    
    delimiter = fields.Selection([(',', 'Virgule'), (';', 'Point-virgule'), ('\t', 'Tabulation')], 
                                  string='Délimiteur CSV', default=';')
    
    has_header = fields.Boolean(string='En-têtes présentes', default=True)
    
    import_log = fields.Text(string='Journal d\'Import', readonly=True)
    records_created = fields.Integer(string='Créés', readonly=True)
    records_updated = fields.Integer(string='Mis à jour', readonly=True)
    errors_count = fields.Integer(string='Erreurs', readonly=True)
    
    state = fields.Selection([('draft', 'Brouillon'), ('validated', 'Validé'), ('done', 'Terminé')], 
                             string='État', default='draft')

    def action_parse_file(self):
        """Lit et valide le fichier avant import."""
        self.ensure_one()
        
        if not self.file_data:
            raise ValidationError(_('Veuillez charger un fichier.'))
        
        file_content = base64.b64decode(self.file_data)
        
        try:
            if self.file_name.endswith('.xlsx') or self.file_name.endswith('.xls'):
                if not xlrd:
                    raise ValidationError(_('Le module xlrd n\'est pas installé.'))
                
                book = xlrd.open_workbook(file_contents=file_content)
                sheet = book.sheet_by_index(0)
                
                preview_data = []
                for row_idx in range(min(5, sheet.nrows)):
                    row_data = [str(cell.value) for cell in sheet.row_values(row_idx)]
                    preview_data.append(row_data)
                
                total_rows = sheet.nrows - (1 if self.has_header else 0)
                
            else:
                import csv
                from io import StringIO
                
                decoded = file_content.decode('utf-8')
                reader = csv.reader(StringIO(decoded), delimiter=self.delimiter)
                
                preview_data = []
                for i, row in enumerate(reader):
                    if i >= 5:
                        break
                    preview_data.append(row)
                
                total_rows = len(decoded.splitlines()) - (1 if self.has_header else 0)
            
            message = _("Fichier validé avec succès.\n")
            message += f"Lignes totales estimées: {total_rows}\n\n"
            message += "Aperçu (5 premières lignes):\n"
            for i, row in enumerate(preview_data):
                message += f"Ligne {i+1}: {' | '.join(row)}\n"
            
            self.import_log = message
            self.state = 'validated'
            
        except Exception as e:
            raise ValidationError(_('Erreur lors de la lecture du fichier: %s') % str(e))
        
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_import(self):
        """Exécute l'import complet."""
        self.ensure_one()
        
        if not self.file_data:
            raise ValidationError(_('Veuillez charger un fichier.'))
        
        file_content = base64.b64decode(self.file_data)
        
        created = 0
        updated = 0
        errors = 0
        log_lines = []
        
        try:
            if self.import_type == 'pricing_rules':
                created, updated, errors, log_lines = self._import_pricing_rules(file_content)
            
            summary = f"\n{'='*50}\nRÉSULTAT DE L'IMPORT\n{'='*50}\n"
            summary += f"Créés: {created}\nMis à jour: {updated}\nErreurs: {errors}\n"
            
            self.import_log = '\n'.join(log_lines) + summary
            self.records_created = created
            self.records_updated = updated
            self.errors_count = errors
            self.state = 'done'
            
        except Exception as e:
            _logger.exception("Erreur during import")
            raise ValidationError(_('Erreur durant l\'import: %s') % str(e))
        
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def _import_pricing_rules(self, file_content):
        """Import des règles tarifaires depuis Excel."""
        created = 0
        updated = 0
        errors = 0
        log_lines = []
        
        if not xlrd:
            raise ValidationError(_('xlrd non installé'))
        
        book = xlrd.open_workbook(file_contents=file_content)
        sheet = book.sheet_by_index(0)
        
        headers = [str(cell.value).strip().upper() for cell in sheet.row_values(0)]
        
        col_map = {}
        for idx, header in enumerate(headers):
            if 'REFERENCE' in header or 'ARTICLE' in header:
                col_map['product'] = idx
            elif 'CODE TARIF' in header:
                col_map['tariff_code'] = idx
            elif 'PRIX' in header and 'TYPE' not in header:
                col_map['price'] = idx
            elif 'DATE DEBUT' in header:
                col_map['date_start'] = idx
            elif 'DATE FIN' in header:
                col_map['date_end'] = idx
            elif 'TYPE PRIX' in header:
                col_map['price_type'] = idx
        
        pricing_rule_model = self.env['pricing.rule']
        product_model = self.env['product.product']
        
        start_row = 1 if self.has_header else 0
        
        for row_idx in range(start_row, sheet.nrows):
            try:
                row = sheet.row_values(row_idx)
                
                product_code = str(int(row[col_map.get('product', 0)])) if row[col_map.get('product', 0)] else ''
                product = product_model.search([('default_code', '=', product_code)], limit=1)
                
                if not product:
                    log_lines.append(f"Ligne {row_idx+1}: Produit '{product_code}' non trouvé - IGNORÉ")
                    errors += 1
                    continue
                
                tariff_code = str(row[col_map.get('tariff_code', 0)]).strip() if col_map.get('tariff_code') else 'TG'
                price = float(row[col_map.get('price', 0)]) if col_map.get('price') else 0.0
                date_start = fields.Date.context_today(self)
                date_end = False
                price_type = 'brut'
                
                values = {
                    'name': f"{tariff_code} - {product.default_code}",
                    'code': tariff_code,
                    'fixed_price': price,
                    'date_start': date_start,
                    'date_end': date_end,
                    'price_type': price_type,
                    'product_ids': [(6, 0, [product.id])],
                }
                
                existing = pricing_rule_model.search([
                    ('code', '=', tariff_code),
                    ('product_ids', 'in', [product.id]),
                ], limit=1)
                
                if existing:
                    existing.write(values)
                    updated += 1
                    log_lines.append(f"Ligne {row_idx+1}: {product.default_code} - {tariff_code} - MIS À JOUR")
                else:
                    pricing_rule_model.create(values)
                    created += 1
                    log_lines.append(f"Ligne {row_idx+1}: {product.default_code} - {tariff_code} - CRÉÉ")
                
            except Exception as e:
                errors += 1
                log_lines.append(f"Ligne {row_idx+1}: ERREUR - {str(e)}")
        
        return created, updated, errors, log_lines