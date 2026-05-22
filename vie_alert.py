import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import hashlib
from datetime import datetime

# ── Configuration ──────────────────────────────────────────
GMAIL_FROM  = "clemencepineau01@gmail.com"
GMAIL_PASS  = "batfex-voBgix-riqcu3"
EMAIL_TO    = "clemencepineau01@gmail.com"
DOMAINES    = ["marketing"]  # liste vide = tous les domaines
STATE_FILE  = "vie_seen.json"
URL_OFFRES  = "https://mon-vie-via.businessfrance.fr/offres/recherche?latest=true"
# ────────────────────────────────────────────────────────────

def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f)

def fetch_offres():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; VIE-Alert/1.0)"}
    r = requests.get(URL_OFFRES, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    offres = []
    for card in soup.select(".offre-item, .offer-card, [class*='offre'], [class*='offer']"):
        titre = card.select_one("h2, h3, .title, .offre-titre, [class*='title']")
        lien  = card.select_one("a[href]")
        domaine_el = card.select_one(".domaine, .category, [class*='domaine'], [class*='sector']")
        pays_el    = card.select_one(".pays, .country, [class*='pays'], [class*='country']")
        date_el    = card.select_one(".date, time, [class*='date']")

        titre_txt   = titre.get_text(strip=True)   if titre    else "Sans titre"
        href        = lien["href"]                  if lien     else "#"
        domaine_txt = domaine_el.get_text(strip=True) if domaine_el else ""
        pays_txt    = pays_el.get_text(strip=True)   if pays_el    else ""
        date_txt    = date_el.get_text(strip=True)   if date_el    else ""

        if not href.startswith("http"):
            href = "https://mon-vie-via.businessfrance.fr" + href

        uid = hashlib.md5((titre_txt + href).encode()).hexdigest()
        offres.append({
            "id": uid, "titre": titre_txt, "lien": href,
            "domaine": domaine_txt, "pays": pays_txt, "date": date_txt
        })
    return offres

def filtrer(offres):
    if not DOMAINES:
        return offres
    mots = [d.lower() for d in DOMAINES]
    return [o for o in offres if any(m in o["domaine"].lower() or m in o["titre"].lower() for m in mots)]

def envoyer_email(nouvelles):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌍 {len(nouvelles)} nouvelle(s) offre(s) VIE — {datetime.now().strftime('%d/%m %H:%M')}"
    msg["From"]    = GMAIL_FROM
    msg["To"]      = EMAIL_TO

    lignes_html = ""
    for o in nouvelles:
        lignes_html += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee">
            <a href="{o['lien']}" style="font-weight:600;color:#185FA5;text-decoration:none">{o['titre']}</a><br>
            <span style="font-size:12px;color:#888">{o['pays']} · {o['domaine']} · {o['date']}</span>
          </td>
        </tr>"""

    html = f"""<html><body style="font-family:sans-serif;color:#333;max-width:600px;margin:auto">
      <h2 style="color:#185FA5">Nouvelles offres VIE</h2>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:8px;overflow:hidden">
        {lignes_html}
      </table>
      <p style="font-size:12px;color:#aaa;margin-top:16px">
        Généré automatiquement · <a href="{URL_OFFRES}">Voir toutes les offres</a>
      </p>
    </body></html>"""

    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_FROM, GMAIL_PASS)
        s.sendmail(GMAIL_FROM, EMAIL_TO, msg.as_string())
    print(f"[{datetime.now():%H:%M:%S}] Email envoyé — {len(nouvelles)} nouvelle(s) offre(s)")

def main():
    print(f"[{datetime.now():%H:%M:%S}] Vérification des offres VIE...")
    seen  = load_seen()
    try:
        offres = fetch_offres()
    except Exception as e:
        print(f"Erreur lors de la récupération : {e}")
        return

    offres = filtrer(offres)
    nouvelles = [o for o in offres if o["id"] not in seen]

    if nouvelles:
        try:
            envoyer_email(nouvelles)
        except Exception as e:
            print(f"Erreur envoi email : {e}")
        seen.update(o["id"] for o in nouvelles)
        save_seen(seen)
    else:
        print(f"[{datetime.now():%H:%M:%S}] Aucune nouvelle offre.")

if __name__ == "__main__":
    main()
