import requests
import json
import os

WEBHOOK_URL = "https://discord.com/api/webhooks/1507375401192914995/k1rZ9dF8UoOEANjgBzsg_iWetbn0nmtKpB-M8pPkyvfcTbJGYNiyVaM9CK7mATN_pflf"
SEEN_FILE = "seen_jobs.json"
KEYWORDS = ["marketing", "communication", "brand", "digital", "fashion", "beauty", "luxury", "wine"]

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def send_discord(title, link, pays, domaine):
    data = {"content": f"Nouvelle offre VIE ! {title} - {pays} - {domaine} - {link}"}
    requests.post(WEBHOOK_URL, json=data)

def main():
    seen = load_seen()
    url = "https://mon-vie-via.businessfrance.fr/api/offres?limit=100&offset=0"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        offres = data.get("items", data.get("offres", data.get("results", [])))
        for o in offres:
            titre = o.get("titre", o.get("title", ""))
            lien = "https://mon-vie-via.businessfrance.fr/offres/" + str(o.get("id", ""))
            pays = o.get("pays", o.get("country", ""))
            domaine = o.get("domaine", o.get("sector", ""))
            uid = str(o.get("id", titre))
            if any(k.lower() in titre.lower() or k.lower() in domaine.lower() for k in KEYWORDS):
                if uid not in seen:
                    send_discord(titre, lien, pays, domaine)
                    seen.append(uid)
        save_seen(seen)
        print("Verification terminee")
    except Exception as e:
        print("Erreur:", e)

main()
