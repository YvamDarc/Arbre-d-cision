
# app.py
# Streamlit Decision Tree App for Accounting Firm Offer Definition
# Author: ChatGPT
# Run: streamlit run app.py

import streamlit as st
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
import datetime

st.set_page_config(page_title="Arbre d'offre - Cabinet EC", page_icon="📊", layout="wide")

# -----------------------------
# Data Structures & Utilities
# -----------------------------

@dataclass
class ClientProfile:
    nom_client: str
    secteur: str                  # ex: BTP, Commerce, Services, Industrie, Agricole, Libéral
    nb_salaries: int
    presence_cadres: bool
    type_contrats: str            # Aucun, CDD, CDI, Mixte
    rse_sensible: bool
    rse_pollution: str            # Faible/Non, Moyenne, Importante
    coaching_client: bool
    patrimoine_dirigeant: str     # Modeste, Important
    particulier_fiscal: List[str] # TVA partic., Crédit impôt, JEI, ZFU/ZRR, LMNP, International, BIC/BNC mixte, Holding, SCI
    caisse: bool                  # Besoin de suivi de trésorerie / cash management
    patrimoniale: bool            # Besoin d'ingénierie patrimoniale
    digitalisation: str           # Non informatique, Informatique rudimentaire, Avancée
    proche_retraite: str          # Loin, A 5 ans, < 2 ans
    succession_envisagee: bool
    clients_particuliers_avec_tva: bool

PRICING_TABLE = {
    "social_basique": {"libelle": "Paie & obligations sociales - Pack Essentiel", "prix": 180},
    "social_plus": {"libelle": "Paie & RH - Pack Plus (audit + procédures)", "prix": 350},
    "social_premium": {"libelle": "Paie & RH - Pack Premium (SIRH + KPI sociaux)", "prix": 550},
    "rse_diag": {"libelle": "Diagnostic RSE & plan d'actions", "prix": 1200},
    "rse_reporting": {"libelle": "Reporting RSE/CSRD adapté TPE/PME", "prix": 450},
    "coaching_light": {"libelle": "Coaching dirigeant - Pack Starter (1h/mois)", "prix": 190},
    "coaching_pro": {"libelle": "Coaching dirigeant - Pack Pro (2h/mois + ateliers)", "prix": 390},
    "patrimoine_base": {"libelle": "Bilan patrimonial dirigeant", "prix": 900},
    "patrimoine_avance": {"libelle": "Ingénierie patrimoniale avancée (holdings/SCI/IF)", "prix": 1800},
    "fiscal_part": {"libelle": "Traitements fiscaux particuliers (notes spécifiques)", "prix": 380},
    "tresorerie": {"libelle": "Cash management & prévisionnels de trésorerie", "prix": 320},
    "digital_start": {"libelle": "Digitalisation - Starter (outils facturation, banque)", "prix": 150},
    "digital_full": {"libelle": "Digitalisation - Full (OCR, Hub, flux API)", "prix": 420},
    "btp_pack": {"libelle": "Pack BTP (suivi chantiers, retenues, DGD)", "prix": 350},
    "gestion_budget": {"libelle": "Tableaux de bord & budget (mensuel)", "prix": 280},
    "revue_qualite": {"libelle": "Revue Qualité comptable & fiscale (trimestrielle)", "prix": 240},
    "succession": {"libelle": "Anticipation transmission / pacte Dutreil (pré-étude)", "prix": 1200},
    "retraite": {"libelle": "Bilan retraite & optimisation (étude complète)", "prix": 750},
    "international": {"libelle": "International (TVA/DEB/DES/EMEA sanity check)", "prix": 650},
}

SECTEURS = ["BTP", "Commerce", "Services", "Industrie", "Agricole", "Professions libérales", "E-commerce", "Autre"]
CONTRATS = ["Aucun salarié", "CDD", "CDI", "Mixte"]
POLLUTION = ["Faible/Non", "Moyenne", "Importante"]
PATRIMOINE = ["Modeste", "Important"]
DIGITAL = ["Pas informatique", "Informatique rudimentaire", "Informatique avancée"]
HORIZON_RETRAITE = ["Loin", "À 5 ans", "< 2 ans"]

def euro(n: float) -> str:
    return f"{n:,.0f} €".replace(",", " ").replace(".", ",")

def safe_add(dic: Dict[str, Any], key: str, value: Any):
    if key not in dic:
        dic[key] = []
    dic[key].append(value)

def infer_segment(profile: ClientProfile) -> Dict[str, Any]:
    """Derive segment, risk flags, and compliance intensity from the profile."""
    segment = []
    risk_flags = []
    compliance_intensity = "Standard"

    # Segment by size
    if profile.nb_salaries == 0 or profile.type_contrats == "Aucun salarié":
        segment.append("Solo/Très petite structure")
    elif profile.nb_salaries < 11:
        segment.append("TPE < 11")
    else:
        segment.append("PME ≥ 11")

    # Sector specifics
    if profile.secteur == "BTP":
        segment.append("BTP")
        risk_flags.append("Gestion des chantiers et retenues de garantie")
        compliance_intensity = "Renforcée"
    if profile.secteur == "E-commerce":
        risk_flags.append("TVA OSS/IOSS et plateformes")
    if profile.secteur == "Industrie":
        risk_flags.append("Stocks et immo complexes")

    # HR complexity
    if profile.nb_salaries > 0:
        if profile.presence_cadres:
            risk_flags.append("Cadres & forfait jours")
        if profile.nb_salaries >= 11:
            risk_flags.append("CSE / obligations sociales renforcées")
            compliance_intensity = "Renforcée"

    # RSE
    if profile.rse_sensible:
        if profile.rse_pollution == "Importante":
            risk_flags.append("Enjeux environnementaux critiques")
        elif profile.rse_pollution == "Moyenne":
            risk_flags.append("Suivi empreinte & conformité environnementale")

    # Digital
    if profile.digitalisation == "Pas informatique":
        risk_flags.append("Faible digitalisation (risque d'erreurs et coûts)")
    elif profile.digitalisation == "Informatique rudimentaire":
        risk_flags.append("Digitalisation partielle à structurer")

    # Dirigeant / Transmission
    if profile.proche_retraite in ("À 5 ans", "< 2 ans"):
        risk_flags.append("Horizon retraite à anticiper")

    if profile.succession_envisagee:
        risk_flags.append("Projet de succession / transmission")

    # Particularités fiscales
    if "International" in profile.particulier_fiscal:
        risk_flags.append("Flux internationaux (prix de transfert/TVA)")
        compliance_intensity = "Renforcée"

    if "Holding" in profile.particulier_fiscal or "SCI" in profile.particulier_fiscal:
        risk_flags.append("Groupe / structuration patrimoniale")

    if profile.clients_particuliers_avec_tva:
        risk_flags.append("Risque TVA B2C (règles spécifiques)")

    return {
        "segment": " | ".join(segment) if segment else "Standard",
        "risk_flags": risk_flags,
        "compliance_intensity": compliance_intensity
    }

def compute_offers(profile: ClientProfile) -> Dict[str, Any]:
    """Decision rules mapping to recommended offers and pricing."""
    offers: List[Dict[str, Any]] = []
    rationales: Dict[str, List[str]] = {}

    def add_offer(code: str, reason: str):
        info = PRICING_TABLE[code]
        offers.append({"code": code, "libelle": info["libelle"], "prix": info["prix"]})
        safe_add(rationales, info["libelle"], reason)

    # Social / HR
    if profile.nb_salaries > 0:
        if profile.nb_salaries >= 11 or profile.presence_cadres:
            add_offer("social_plus", "≥ 11 salariés et/ou présence de cadres")
        else:
            add_offer("social_basique", "Paie et obligations sociales standard")
        if profile.nb_salaries >= 25:
            add_offer("social_premium", "Effectif significatif → SIRH & KPI sociaux")

    # RSE
    if profile.rse_sensible:
        add_offer("rse_diag", "Client sensible RSE → diagnostic & plan d'actions")
        if profile.rse_pollution in ("Moyenne", "Importante"):
            add_offer("rse_reporting", "Suivi des indicateurs RSE (empreinte, énergie, déchets)")

    # Coaching dirigeant
    if profile.coaching_client and profile.patrimoine_dirigeant == "Modeste":
        add_offer("coaching_light", "Accompagnement dirigeant régulier (starter)")
    if profile.coaching_client and profile.patrimoine_dirigeant == "Important":
        add_offer("coaching_pro", "Accompagnement renforcé pour enjeux stratégiques")

    # Patrimonial
    if profile.patrimoniale or profile.patrimoine_dirigeant == "Important":
        add_offer("patrimoine_base", "Besoin patrimonial identifié")
    if ("Holding" in profile.particulier_fiscal or "SCI" in profile.particulier_fiscal) and (profile.patrimoniale or profile.patrimoine_dirigeant == "Important"):
        add_offer("patrimoine_avance", "Structuration groupe / immo patrimonial")

    # Particularités fiscales
    if len(profile.particulier_fiscal) > 0:
        add_offer("fiscal_part", "Cas fiscaux spécifiques à documenter")
        if "International" in profile.particulier_fiscal:
            add_offer("international", "Flux intracommunautaires / export → contrôles dédiés")

    # Cash / gestion
    if profile.caisse or profile.secteur in ("E-commerce", "Industrie", "BTP"):
        add_offer("tresorerie", "Volatilité de trésorerie / besoin de pilotage")
    add_offer("gestion_budget", "Tableaux de bord et budget mensuel utiles à tout profil PME/TPE")
    add_offer("revue_qualite", "Sécuriser la qualité comptable et fiscale")

    # Digitalisation
    if profile.digitalisation == "Pas informatique":
        add_offer("digital_start", "Mettre en place la base des outils digitaux")
    elif profile.digitalisation == "Informatique rudimentaire":
        add_offer("digital_full", "Structurer et automatiser les flux (OCR/API/Banque)")

    # Sector packs
    if profile.secteur == "BTP":
        add_offer("btp_pack", "Spécificités chantiers (retenues, situations, DGD)")

    # Transmission / retraite
    if profile.proche_retraite in ("À 5 ans", "< 2 ans"):
        add_offer("retraite", "Horizon de départ → bilan retraite & options")
    if profile.succession_envisagee:
        add_offer("succession", "Projet de transmission → pré-étude Dutreil/holding")

    # Deduplicate by code (keep first occurrence)
    seen = set()
    unique_offers = []
    for o in offers:
        if o["code"] not in seen:
            unique_offers.append(o)
            seen.add(o["code"])

    total = sum(o["prix"] for o in unique_offers)
    return {
        "offers": unique_offers,
        "rationales": rationales,
        "total_ht": total
    }

def export_proposal(profile: ClientProfile, segment_info: Dict[str, Any], offers_info: Dict[str, Any]) -> str:
    """Generate a Markdown commercial proposal and save to a file; return path."""
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# Proposition d'accompagnement — {profile.nom_client}")
    lines.append("")
    lines.append(f"_Date : {now}_")
    lines.append("")
    lines.append("## 1) Profil synthétique")
    lines.append("")
    pf = asdict(profile)
    key_map = {
        "nom_client": "Client",
        "secteur": "Secteur",
        "nb_salaries": "Nombre de salariés",
        "presence_cadres": "Présence de cadres",
        "type_contrats": "Type de contrats",
        "rse_sensible": "Sensibilité RSE",
        "rse_pollution": "Niveau d'impact environnemental",
        "coaching_client": "Souhaite coaching dirigeant",
        "patrimoine_dirigeant": "Patrimoine du dirigeant",
        "particulier_fiscal": "Particularités fiscales",
        "caisse": "Suivi de trésorerie",
        "patrimoniale": "Besoin patrimonial",
        "digitalisation": "Niveau de digitalisation",
        "proche_retraite": "Horizon retraite",
        "succession_envisagee": "Projet de succession",
        "clients_particuliers_avec_tva": "Clients particuliers avec TVA"
    }
    for k, v in pf.items():
        if k == "nom_client":
            continue
        label = key_map.get(k, k)
        value = ", ".join(v) if isinstance(v, list) else ("Oui" if isinstance(v, bool) and v else "Non" if isinstance(v, bool) else str(v))
        lines.append(f"- **{label}** : {value}")
    lines.append("")
    lines.append("## 2) Segmentation & risques")
    lines.append("")
    lines.append(f"- **Segment** : {segment_info['segment']}")
    lines.append(f"- **Intensité conformité** : {segment_info['compliance_intensity']}")
    if segment_info["risk_flags"]:
        for rf in segment_info["risk_flags"]:
            lines.append(f"  - ⚠️ {rf}")
    lines.append("")
    lines.append("## 3) Offre recommandée")
    lines.append("")
    for o in offers_info["offers"]:
        lib = o["libelle"]
        prix = euro(o["prix"])
        lines.append(f"- **{lib}** — {prix} / mois ou forfait")
        reasons = offers_info["rationales"].get(lib, [])
        for r in reasons:
            lines.append(f"  - Justification : {r}")
    lines.append("")
    lines.append(f"**Total indicatif** (HT) : {euro(offers_info['total_ht'])}")
    lines.append("")
    lines.append("## 4) Prochaines étapes")
    steps = [
        "Atelier de cadrage (1h) pour valider les priorités et le périmètre",
        "Plan d'onboarding (accès bancaires, facturation, paie, outils)",
        "Mise en place des rituels (comité de pilotage mensuel / trimestriel)",
        "Premiers livrables : budget, prévisionnel de trésorerie, diagnostic RSE"
    ]
    for s in steps:
        lines.append(f"- {s}")
    content = "\n".join(lines)
    filename = f"/mnt/data/Proposition_{profile.nom_client.replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

# -----------------------------
# UI
# -----------------------------

st.title("📊 Arbre de décision — Définir une offre commerciale (Cabinet d'EC)")
st.caption("Un configurateur intelligent pour qualifier le besoin client et bâtir une offre complète.")

with st.sidebar:
    st.header("🧾 Dossier client")
    nom_client = st.text_input("Nom du client / dossier", value="Client DEMO")
    secteur = st.selectbox("Secteur d'activité", SECTEURS, index=2)
    col_a, col_b = st.columns(2)
    with col_a:
        nb_salaries = st.number_input("Nombre de salariés", min_value=0, max_value=1000, value=0, step=1)
        presence_cadres = st.toggle("Présence de cadres", value=False)
        type_contrats = st.selectbox("Type de contrats", CONTRATS, index=0 if nb_salaries==0 else 3)
    with col_b:
        rse_sensible = st.toggle("Client sensible RSE", value=False)
        rse_pollution = st.selectbox("Impact environnemental", POLLUTION, index=0)
        coaching_client = st.toggle("Souhaite coaching dirigeant", value=False)

    patrimoine_dirigeant = st.selectbox("Patrimoine du dirigeant", PATRIMOINE, index=0)
    particulier_fiscal = st.multiselect(
        "Particularités fiscales",
        ["TVA particuliers", "Crédit d'impôt", "JEI", "ZFU/ZRR", "LMNP", "International", "BIC/BNC mixte", "Holding", "SCI"],
        default=[]
    )
    caisse = st.toggle("Besoin suivi trésorerie (cash management)", value=True if secteur in ("E-commerce","BTP","Industrie") else False)
    patrimoniale = st.toggle("Besoin d'ingénierie patrimoniale", value=(patrimoine_dirigeant=="Important"))
    digitalisation = st.selectbox("Niveau de digitalisation", DIGITAL, index=1)
    proche_retraite = st.selectbox("Horizon retraite du dirigeant", HORIZON_RETRAITE, index=0)
    succession_envisagee = st.toggle("Projet de succession / transmission", value=False)
    clients_particuliers_avec_tva = st.toggle("Clients particuliers avec TVA", value=False)

profile = ClientProfile(
    nom_client=nom_client,
    secteur=secteur,
    nb_salaries=int(nb_salaries),
    presence_cadres=presence_cadres,
    type_contrats=type_contrats,
    rse_sensible=rse_sensible,
    rse_pollution=rse_pollution,
    coaching_client=coaching_client,
    patrimoine_dirigeant=patrimoine_dirigeant,
    particulier_fiscal=[p for p in particulier_fiscal if p != "TVA particuliers"],
    caisse=caisse,
    patrimoniale=patrimoniale,
    digitalisation=digitalisation,
    proche_retraite=proche_retraite,
    succession_envisagee=succession_envisagee,
    clients_particuliers_avec_tva=("TVA particuliers" in particulier_fiscal) or clients_particuliers_avec_tva
)

segment_info = infer_segment(profile)
offers_info = compute_offers(profile)

# Main layout
c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("🧩 Segmentation & risques")
    st.markdown(f"**Segment** : {segment_info['segment']}")
    st.markdown(f"**Intensité conformité** : {segment_info['compliance_intensity']}")
    if len(segment_info["risk_flags"]) == 0:
        st.success("Aucun signal de risque particulier identifié.")
    else:
        for rf in segment_info["risk_flags"]:
            st.warning(rf)

with c2:
    st.subheader("💼 Offre recommandée")
    total = offers_info["total_ht"]
    st.metric("Total indicatif (HT / mois ou forfait)", euro(total))
    for o in offers_info["offers"]:
        with st.expander(f"{o['libelle']} — {euro(o['prix'])}"):
            reasons = offers_info["rationales"].get(o["libelle"], [])
            if reasons:
                st.write("**Justifications :**")
                for r in reasons:
                    st.write(f"- {r}")
            else:
                st.write("Recommandé selon le profil.")

st.divider()
st.subheader("🧠 Règles clés (explicables)")
explain_rules = {
    "Taille & RH": "≥ 11 salariés implique CSE et obligations renforcées ; présence de cadres ⇒ complexité paie/RH.",
    "RSE": "Client sensible RSE ⇒ diagnostic + reporting si impact environnemental non négligeable.",
    "Digitalisation": "Faible maturité ⇒ mise en place d'outils ; maturité moyenne ⇒ automatisations avancées.",
    "Secteur BTP": "Suivi chantiers, retenues de garantie, situations de travaux ⇒ pack dédié.",
    "Transmission": "Horizon retraite ≤ 5 ans ou succession envisagée ⇒ études retraite et Dutreil.",
    "Fiscalité": "Cas spécifiques (international, holdings, SCI, etc.) ⇒ notes et contrôles dédiés."
}
st.json(explain_rules)

st.divider()
st.subheader("📤 Exporter la proposition commerciale")
if st.button("Générer le fichier Markdown"):
    path = export_proposal(profile, segment_info, offers_info)
    st.success(f"Proposition générée : {path}")
    with open(path, "r", encoding="utf-8") as f:
        st.download_button("Télécharger la proposition (.md)", data=f.read(), file_name=Path(path).name, mime="text/markdown")

st.caption("⚙️ Personnalisez les tarifs et libellés dans PRICING_TABLE en haut du fichier.")
