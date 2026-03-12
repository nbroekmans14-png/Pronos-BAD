import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

# Fichiers de sauvegarde
VOTES_FILE = "tous_les_votes.csv"
SCORES_FILE = "classement_general.csv"
MSG_FILE = "message_admin.txt"

# --- SECURITE : INITIALISATION DU SESSION STATE ---
if 'votes_backup' not in st.session_state:
    if os.path.exists(VOTES_FILE):
        st.session_state.votes_backup = pd.read_csv(VOTES_FILE)
    else:
        st.session_state.votes_backup = pd.DataFrame()

# Fonctions de gestion avec renforcement
def save_data(df, filename):
    try:
        df.to_csv(filename, index=False)
        # On double la sauvegarde dans la mémoire vive de Streamlit
        if filename == VOTES_FILE:
            st.session_state.votes_backup = df
        return True
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")
        return False

def load_data(filename):
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename)
        except:
            return pd.DataFrame()
    # Secours : si le fichier a disparu mais qu'on a la sauvegarde en mémoire
    if filename == VOTES_FILE and not st.session_state.votes_backup.empty:
        return st.session_state.votes_backup
    return pd.DataFrame()

def save_message(text):
    with open(MSG_FILE, "w", encoding="utf-8") as f:
        f.write(text)

def load_message():
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "Préparez vos pronos pour la prochaine rencontre !"

# 2. DESIGN (FORCÉ)
st.markdown("""
    <style>
    :root { --primary-color: #d32f2f; --background-color: #ffffff; --text-color: #31333F; }
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    .header-box { background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 25px; border-radius: 0px 0px 20px 20px; text-align: center; margin: -60px -20px 10px -20px; }
    .header-box h1 { color: white !important; }
    .header-box p { color: #ffeb3b !important; }
    .admin-msg { background-color: #f0f2f6 !important; padding: 18px; border-radius: 12px; text-align: center; font-weight: 700; font-size: 1.15rem !important; border: 1px solid #d1d5db; }
    .match-header { background-color: #f0f2f6 !important; padding: 10px 15px; font-weight: 700; color: #000000 !important; border-radius: 8px; margin-top: 10px; }
    .stButton>button { background-color: #f0f2f6 !important; color: #31333F !important; border: 1px solid #d1d5db !important; border-radius: 12px; font-weight: bold; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- CONTENU ---
st.markdown('<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>1pt par bon prono • +3pts bonus si 8/8</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="admin-msg">📢 {load_message()}</div>', unsafe_allow_html=True)

try:
    st.image("image_c4425f.jpg.jpeg", use_container_width=True)
except:
    pass

st.divider()

# 3. ESPACE VOTE
st.subheader("🎯 Fais tes pronos")
nom_input = st.text_input("Ton Prénom & Nom", placeholder="Ex: Lucas B").strip()

match_data = [
    ("Simple Homme 1", "👨"), ("Simple Homme 2", "👨"),
    ("Simple Dame 1", "👩"), ("Simple Dame 2", "👩"),
    ("Double Homme", "👬"), ("Double Dame", "👭"),
    ("Mixte 1", "👫"), ("Mixte 2", "👫")
]

if nom_input:
    pronos = {}
    for match_name, emoji in match_data:
        st.markdown(f'<div class="match-header">{emoji} {match_name}</div>', unsafe_allow_html=True)
        pronos[match_name] = st.radio(f"Vainqueur {match_name}", ["St-Nolff 🐺", "Adversaire"], key=f"p_{match_name}", horizontal=True, label_visibility="collapsed")
        
    if st.button("🚀 VALIDER MA GRILLE"):
        df_v = load_data(VOTES_FILE)
        
        if not df_v.empty and nom_input.lower() in df_v["Joueur"].str.lower().values:
            st.error(f"Désolé {nom_input}, tu as déjà voté ! 🐺")
        else:
            nouveau_vote = {"Joueur": nom_input}
            for k, v in pronos.items():
                nouveau_vote[k] = "St-Nolff" if v == "St-Nolff 🐺" else v
            
            df_v = pd.concat([df_v, pd.DataFrame([nouveau_vote])], ignore_index=True)
            if save_data(df_v, VOTES_FILE):
                st.success("Grille bien enregistrée sur le serveur ! Aouuuuuuh 🐺")
                st.balloons()

st.divider()

# 4. CLASSEMENT
st.subheader("🏆 Classement Général")
df_scores = load_data(SCORES_FILE)
if not df_scores.empty:
    df_scores = df_scores.sort_values(by="Points", ascending=False).reset_index(drop=True)
    df_scores["Rang"] = df_scores.index + 1
    if "AncienRang" not in df_scores.columns: df_scores["AncienRang"] = 0
    def get_evolution(row):
        if row["AncienRang"] == 0: return "🆕"
        diff = int(row["AncienRang"]) - int(row["Rang"])
        return f"🟢 +{diff}" if diff > 0 else (f"🔴 {diff}" if diff < 0 else "〓")
    df_scores["Évo"] = df_scores.apply(get_evolution, axis=1)
    st.table(df_scores[["Rang", "Évo", "Joueur", "Points"]].set_index("Rang"))

try:
    st.image("image_c4423b.jpg.jpeg", use_container_width=True)
except:
    pass

# 5. ADMIN (RENFORCÉ)
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🛠️ Administration"):
    mdp = st.text_input("Code", type="password")
    if mdp == "2003":
        t1, t2, t3, t4 = st.tabs(["Résultats", "Votes", "Message", "Reset"])
        with t1:
            reels = {m[0]: st.selectbox(f"{m[0]}", ["St-Nolff", "Adversaire"], key=f"adm_{m[0]}") for m in match_data}
            if st.button("Valider la journée"):
                df_v = load_data(VOTES_FILE)
                if not df_v.empty:
                    df_gen = load_data(SCORES_FILE)
                    if "AncienRang" not in df_gen.columns: df_gen["AncienRang"] = 0
                    
                    for _, row in df_v.iterrows():
                        j_nom, b = row['Joueur'], sum(1 for m, _ in match_data if row[m] == reels[m])
                        pts_jour = b + (3 if b == 8 else 0)
                        mask = df_gen['Joueur'].str.lower() == j_nom.lower()
                        if mask.any():
                            df_gen.loc[mask, 'Points'] += pts_jour
                        else:
                            df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": j_nom, "Points": pts_jour, "AncienRang": 0}])], ignore_index=True)
                    
                    save_data(df_gen, SCORES_FILE)
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    st.session_state.votes_backup = pd.DataFrame()
                    st.rerun()
        with t2:
            st.write("### Votants enregistrés")
            df_v = load_data(VOTES_FILE)
            if not df_v.empty:
                st.dataframe(df_v, use_container_width=True)
                # --- SÉCURITÉ SUPPLÉMENTAIRE ---
                csv_download = df_v.to_csv(index=False).encode('utf-8')
                st.download_button("📥 TÉLÉCHARGER UNE SAUVEGARDE (CSV)", csv_download, "votes_backup.csv", "text/csv")
            else:
                st.info("Aucun vote en mémoire.")
        with t3:
            msg = st.text_area("Annonce :", load_message())
            if st.button("Modifier"): save_message(msg); st.rerun()
