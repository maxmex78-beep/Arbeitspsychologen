import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Professionelle Header, um menschliches Verhalten zu simulieren
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.psychologen.at/"
}

BASE_URL = "https://www.psychologen.at/go.asp?sektion=personen&bereich_id=9003&berufsgruppe=psy&geschlecht=A&spq_id=113&suchformular_id=9&aktion=view"
DOMAIN = "https://www.psychologen.at/"

def determine_anrede(name):
    female_indicators = ["Mag.a", "Dr.in", "Bakk.a", "Dipl.-Ing.in", "Frau"]
    if any(ind in name for ind in female_indicators):
        return "Frau"
    return "Herr"

def run_scraper():
    all_data = []
    # Wir loopen durch die Start-Indizes (0, 15, 30...)
    for start_val in range(0, 225, 15):
        print(f"--- Scanne Seite ab Eintrag {start_val} ---")
        url = f"{BASE_URL}&start={start_val}"
        
        try:
            session = requests.Session()
            response = session.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Alle Links finden, die "person_id=" enthalten
            links = soup.find_all('a', href=True)
            # Nur eindeutige Profil-Links filtern
            profile_paths = list(set([l['href'] for l in links if "person_id=" in l['href']]))
            
            print(f"Gefundene Profile auf dieser Seite: {len(profile_paths)}")

            for path in profile_paths:
                full_url = DOMAIN + path if not path.startswith('http') else path
                
                # Jedes Profil einzeln aufrufen
                res_profile = session.get(full_url, headers=HEADERS, timeout=15)
                p_soup = BeautifulSoup(res_profile.text, 'html.parser')
                
                # Name extrahieren (oft im <h1> oder im Title)
                name_tag = p_soup.find('h1')
                if not name_tag:
                    continue
                
                full_name = name_tag.get_text(strip=True)
                anrede = determine_anrede(full_name)
                
                # E-Mail finden: Suche nach mailto oder Regex im gesamten Text
                email = ""
                mail_link = p_soup.find('a', href=re.compile(r'mailto:'))
                if mail_link:
                    email = mail_link['href'].replace('mailto:', '').split('?')[0]
                else:
                    # Fallback Regex Suche
                    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', res_profile.text)
                    if match:
                        email = match.group(0)

                if email:
                    print(f"Treffer: {full_name} -> {email}")
                    all_data.append({
                        "Anrede": anrede,
                        "Name": full_name,
                        "Email": email,
                        "Profil": full_url
                    })
                
                # Wichtig: Kurze Pause, um nicht gesperrt zu werden
                time.sleep(1.2)
                
        except Exception as e:
            print(f"Fehler bei Start {start_val}: {e}")

    # Speichern der Ergebnisse
    with open('arbeitspsychologen_at.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["Anrede", "Name", "Email", "Profil"], delimiter=';')
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"FERTIG! Insgesamt {len(all_data)} Kontakte mit E-Mail gefunden.")

if __name__ == "__main__":
    run_scraper()
