import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Wir geben uns als echter Browser aus, um nicht blockiert zu werden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://www.psychologen.at/go.asp?sektion=personen&bereich_id=9003&berufsgruppe=psy&geschlecht=A&spq_id=113&suchformular_id=9&aktion=view"
DOMAIN = "https://www.psychologen.at/"

def get_email(profile_url):
    try:
        res = requests.get(profile_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            # Suche nach mailto-Links
            mail_match = re.search(r'mailto:([\w\.-]+@[\w\.-]+\.\w+)', res.text)
            if mail_match:
                return mail_match.group(1)
            # Fallback: Suche nach E-Mail-Muster im Text
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', res.text)
            if email_match:
                return email_match.group(0)
    except:
        pass
    return ""

def determine_anrede(name):
    female_indicators = ["Mag.a", "Dr.in", "Bakk.a", "Dipl.-Ing.in", "Frau"]
    if any(ind in name for ind in female_indicators):
        return "Frau"
    return "Herr"

def run_scraper():
    all_data = []
    # Testen wir erst mal die ersten 3 Seiten (0, 15, 30), um zu sehen ob es klappt
    for start_val in range(0, 225, 15):
        print(f"Scanne Seite ab Eintrag {start_val}...")
        url = f"{BASE_URL}&start={start_val}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Alle Links finden, die auf ein Personenprofil deuten
            links = soup.find_all('a', href=True)
            profile_links = list(set([l['href'] for l in links if "person_id=" in l['href']]))
            
            if not profile_links:
                print(f"Warnung: Keine Links auf Seite {start_val} gefunden.")
                continue

            for link_suffix in profile_links:
                full_profile_url = DOMAIN + link_suffix if not link_suffix.startswith('http') else link_suffix
                
                print(f"Extrahiere Profil: {full_profile_url}")
                profile_res = requests.get(full_profile_url, headers=HEADERS, timeout=10)
                profile_soup = BeautifulSoup(profile_res.text, 'html.parser')
                
                # Name finden
                name_tag = profile_soup.find('h1')
                if not name_tag:
                    continue
                    
                full_name = name_tag.get_text(strip=True)
                anrede = determine_anrede(full_name)
                email = get_email(full_profile_url)
                
                if email: # Nur speichern, wenn wir eine E-Mail gefunden haben
                    all_data.append({
                        "Anrede": anrede,
                        "Name": full_name,
                        "Email": email,
                        "Profil": full_profile_url
                    })
                
                time.sleep(0.5) # Fair Use
                
        except Exception as e:
            print(f"Fehler bei Start {start_val}: {e}")

    # Speichern
    with open('arbeitspsychologen_at.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["Anrede", "Name", "Email", "Profil"], delimiter=';')
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"Erfolg! {len(all_data)} Kontakte mit E-Mail extrahiert.")

if __name__ == "__main__":
    run_scraper()
