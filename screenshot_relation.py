#!/usr/bin/env python3
"""Capture d'écran de la relation entre deux individus."""

from datetime import datetime
from playwright.sync_api import sync_playwright
import os

# Configuration
URL = "http://localhost:8082"
PERSON_A = "Heida"  # Heïda Valvassori
PERSON_B = "Isabelle Zufferey"  # Isabelle Roxane Colette Stéphanie Zufferey Monachon
OUTPUT_DIR = "/home/ubuntu/dev/ged-relations/screencopy"

# Créer le timestamp
timestamp = datetime.now().strftime("screenshot.%y%m%d.%H%M")
output_file = os.path.join(OUTPUT_DIR, f"{timestamp}.png")

print(f"📸 Capture de la relation entre Heida Valvassori et Isabelle Zufferey Monachon")
print(f"📁 Sauvegarde : {output_file}")

with sync_playwright() as p:
    # Lancer le navigateur
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    # Naviguer vers la page d'accueil
    print(f"🌐 Navigation vers {URL}")
    page.goto(URL)
    page.wait_for_load_state("networkidle")
    
    # Remplir les champs de recherche
    print("🔍 Recherche des individus...")
    
    # Chercher la première personne
    page.fill("#person1", PERSON_A)
    page.wait_for_timeout(1500)  # Attendre la recherche AJAX
    
    # Cliquer sur le premier résultat
    result1 = page.query_selector("#results1 .search-result-item")
    if result1:
        result1.click()
        print(f"   ✓ Première personne sélectionnée")
    else:
        print(f"   ✗ Première personne non trouvée")
        browser.close()
        exit(1)
    
    page.wait_for_timeout(500)
    
    # Chercher la deuxième personne
    page.fill("#person2", PERSON_B)
    page.wait_for_timeout(1500)  # Attendre la recherche AJAX
    
    # Cliquer sur le deuxième résultat
    result2 = page.query_selector("#results2 .search-result-item")
    if result2:
        result2.click()
        print(f"   ✓ Deuxième personne sélectionnée")
    else:
        print(f"   ✗ Deuxième personne non trouvée")
        browser.close()
        exit(1)
    
    page.wait_for_timeout(500)
    
    # Cliquer sur le bouton de calcul
    print("🧮 Calcul de la relation...")
    page.click("#btnCalc")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)  # Attendre l'affichage
    
    # Faire la capture d'écran
    print(f"📸 Capture en cours...")
    page.screenshot(path=output_file, full_page=True)
    print(f"✅ Capture sauvegardée : {output_file}")
    
    # Fermer le navigateur
    browser.close()

print(f"\n🎉 Terminé ! Fichier : {output_file}")
