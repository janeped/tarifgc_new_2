# GC Pricing Engine - Module de Tarification Avancée pour Odoo 19

## 📋 Description

Module de gestion avancée des tarifs et remises pour Odoo 19, développé pour **Graine Créative** dans le cadre de leur migration Divalto → Odoo.

Ce module reproduit la richesse fonctionnelle du système tarifaire Divalto avec :
- Logique d'**entonnoir tarifaire** (OLIM > TS > TG)
- Gestion des **prix bruts vs nets**
- **3 niveaux de remises** (cumulatives ou successives)
- **Promotions bornées** dans le temps
- **Exclusions** clients/produits
- **Traçabilité complète** du calcul
- Support des **kits/décompositions**

## 🎯 Fonctionnalités Principales

### 1. Détermination Tarifaire par Entonnoir

### 2. Types de Prix

| Type | Remisable ? | Usage |
|------|-------------|-------|
| **Prix Brut** | Oui | Standard, remises ligne applicables |
| **Prix Net** | Non (sauf pied) | Marges faibles, livres, etc. |

### 3. Remises Multi-Niveaux

Jusqu'à **3 niveaux de remises** par ligne de commande :
- **Cumulative** : Les % s'additionnent avant application
- **Successive** : Chaque % s'applique au résultat précédent

### 4. R99 Exclusive

Remise exclusive qui **remplace toutes les autres** remises ligne si active.

### 5. Traçabilité Complète

Pour chaque ligne : règle tarifaire, promotion, remises détaillées, prix base → final.

## 🚀 Installation

1. Copier ce dossier dans `custom_addons/` de ton Odoo
2. Mettre à jour la liste des apps
3. Installer "GC Pricing Engine"

## 👥 Crédits

Développé par **Apik Centre Val de Loire**  
Pour **Graine Créative**  
Version : 19.0.1.0.0