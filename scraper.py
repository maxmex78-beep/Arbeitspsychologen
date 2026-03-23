import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Konfiguration
BASE_URL = "https://www.psychologen.at/go.asp?sektion=personen&bereich_id=9003&berufsgruppe=psy&geschlecht=A&spq_id=113&suchformular_id=9&aktion=view"
DOMAIN = "https://www.psychologen.at/"

def get_email(profile_url):
    """Sucht im Einzelprofil nach der E-Mail Adresse."""
    try:
        res = requests.get(profile_url, timeout=10)
        if res.status_code == 200:
            # Suche nach mailto oder Text-Mustern
            soup = BeautifulSoup(res.text, 'html.parser')
            # Oft in mailto-Links versteckt
            mail_links = soup.find_all('a', href=re.compile(r'mailto:'))
            if mail_links:
                return mail_links[0]['href'].replace('mailto:', '').split('?')[0]
            # Fallback: Suche nach E-Mail-Muster im Text
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', res.text)
            if email_match:
                return email_match.group(0)
    except:
        return ""
    return ""

def determine_anrede(name):
    """Bestimmt die Anrede basierend auf österreichischen Gendertiteln."""
    female_indicators = ["Mag.a", "Dr.in", "Bakk.a", "Dipl.-Ing.in", "Frau"]
    if any(ind in name for ind in female_indicators):
        return "Frau"
    return "Herr"

def run_scraper():
    all_data = []
    # 217 Einträge / 15 pro Seite = ca. 15 Seiten
    for start_val in range(0, 225, 15):
        print(f"Scanne Seite ab Eintrag {start_val}...")
        url = f"{BASE_URL}&start={start_val}"
        
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Suche alle Profil-Links
            links = soup.find_all('a', href=re.compile(r'person_id='))
            
            # Dubletten vermeiden (Links tauchen oft doppelt auf)
            unique_links = []
            for l in links:
                if l['href'] not in unique_links:
                    unique_links.append(l['href'])
            
            for link_suffix in unique_links:
                name = ""
                # Den Namen finden (steht oft im Link-Text)
                full_profile_url = DOMAIN + link_suffix
                
                # Wir rufen das Profil auf
                print(f"Checke Profil: {full_profile_url}")
                profile_res = requests.get(full_profile_url, timeout=10)
                profile_soup = BeautifulSoup(profile_res.text, 'html.parser')
                
                # Name aus dem Title oder H1 extrahieren
                name_tag = profile_soup.find('h1') or profile_soup.find('title')
                full_name = name_tag.get_text(strip=True).replace(" - Psychologen.at", "")
                
                anrede = determine_anrede(full_name)
                email = get_email(full_profile_url)
                
                all_data.append({
                    "Anrede": anrede,
                    "Name": full_name,
                    "Email": email,
                    "Profil": full_profile_url
                })
                # Fair-use Pause
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Fehler bei Start {start_val}: {e}")

    # Speichern
    with open('arbeitspsychologen_at.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["Anrede", "Name", "Email", "Profil"], delimiter=';')
        writer.writeheader()
        writer.writerows(all_data)
    print(f"Fertig! {len(all_data)} Kontakte extrahiert.")

if __name__ == "__main__":
    run_scraper()
