import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

VOTES_FILE = "tous_les_votes.csv"
SCORES_FILE = "classement_general.csv"
MSG_FILE = "message_admin.txt"
LOCK_FILE = "lock_status.txt"

match_data = [
    ("Simple Homme 1", "👨"), ("Simple Homme 2", "👨"),
    ("Simple Dame 1", "👩"), ("Simple Dame 2", "👩"),
    ("Double Homme", "👬"), ("Double Dame", "👭"),
    ("Mixte 1", "👫"), ("Mixte 2", "👫")
]

# --- FONCTIONS DE GESTION ---

def load_text(filename, default_text):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default_text

def save_text(filename, text):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())

def load_df(filename, columns):
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            if not df.empty: return df
        except: pass
    return pd.DataFrame(columns=columns)

def save_df(df, filename):
    df.to_csv(filename, index=False)

# 2. DESIGN
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    .header-box { background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 25px; border-radius: 0 0 20px 20px; text-align: center; margin: -60px -20px 10px -20px; }
    .header-box h1 { color: white !important; margin: 0; }
    .header-box p { color: #ffeb3b !important; margin-top: 5px; }
    .admin-msg { background-color: #f0f2f6 !important; padding: 18px; border-radius: 12px; text-align: center; font-weight: 700; border: 1px solid #d1d5db; margin: 15px 0; }
    .match-header { background-color: #f0f2f6 !important; padding: 10px 15px; font-weight: 700; color: black !important; border-radius: 8px; margin-top: 10px; }
    .stButton>button { background-color: #f0f2f6 !important; color: #31333F !important; border: 1px solid #d1d5db !important; border-radius: 12px; font-weight: bold; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
st.markdown('<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>1pt par bon prono • +3pts bonus si 8/8</p></div>', unsafe_allow_html=True)
current_msg = load_text(MSG_FILE, "Préparez vos pronos !")
st.markdown(f'<div class="admin-msg">📢 {current_msg}</div>', unsafe_allow_html=True)

try:
    st.image("image_c4425f.jpg.jpeg", use_container_width=True)
except: pass

st.divider()

# 3. ESPACE VOTE
is_locked = load_text(LOCK_FILE, "unlocked") == "locked"

if is_locked:
    st.warning("🔒 Les votes sont clos pour cette rencontre.")
else:
    st.subheader("🎯 Fais tes pronos")
    nom_input = st.text_input("Ton Prénom & Nom", placeholder="Ex: Lucas B").strip()
    if nom_input:
        pronos = {}
        for m_name, emoji in match_data:
            st.markdown(f'<div class="match-header">{emoji} {m_name}</div>', unsafe_allow_html=True)
            pronos[m_name] = st.radio(f"Vainqueur {m_name}", ["St-Nolff 🐺", "Adversaire"], key=f"v_{m_name}", horizontal=True, label_visibility="collapsed")
        
        if st.button("🚀 VALIDER MA GRILLE"):
            df_v = load_df(VOTES_FILE, ["Joueur"])
            if not df_v.empty and nom_input.lower() in df_v["Joueur"].str.lower().values:
                st.warning(f"Désolé {nom_input}, ton vote est déjà enregistré !")
            else:
                nv = {"Joueur": nom_input}
                for k, v in pronos.items(): nv[k] = "St-Nolff" if v == "St-Nolff 🐺" else v
                df_v = pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True)
                save_df(df_v, VOTES_FILE)
                st.success("Vote bien enregistré !")
                st.balloons()

st.divider()

# 4. CLASSEMENT
st.subheader("🏆 Classement Général")
df_scores = load_df(SCORES_FILE, ["Joueur", "Points", "AncienRang"])
if not df_scores.empty:
    df_scores["Points"] = pd.to_numeric(df_scores["Points"])
    df_scores = df_scores.sort_values(by="Points", ascending=False).reset_index(drop=True)
    df_scores["Rang"] = df_scores.index + 1
    def get_evo(row):
        if row["AncienRang"] == 0: return "🆕"
        diff = int(row["AncienRang"]) - int(row["Rang"])
        return f"🟢 +{diff}" if diff > 0 else (f"🔴 {diff}" if diff < 0 else "〓")
    df_scores["Évo"] = df_scores.apply(get_evo, axis=1)
    st.table(df_scores[["Rang", "Évo", "Joueur", "Points"]].set_index("Rang"))
    
    # Bouton de sauvegarde du classement pour l'admin (visible uniquement si mdp saisi plus bas ou ici par sécurité)
    st.download_button("💾 Sauvegarder le classement actuel (CSV)", df_scores.to_csv(index=False), "classement_general_backup.csv")
else:
    st.info("Le classement sera affiché après la validation des résultats.")

try:
    st.image("image_c4423b.jpg.jpeg", use_container_width=True)
except: pass

# 5. ADMINISTRATION
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🛠️ Administration"):
    mdp = st.text_input("Code", type="password")
    if mdp == "2003":
        t1, t2, t3, t4, t5, t6 = st.tabs(["Résultats", "Votants", "Annonce", "Verrou", "📥 RESTAURATION", "RESET"])
        
        with t1:
            reels = {m[0]: st.selectbox(f"{m[0]}", ["St-Nolff", "Adversaire"], key=f"adm_{m[0]}") for m in match_data}
            if st.button("Valider la journée"):
                df_v = load_df(VOTES_FILE, ["Joueur"])
                df_gen = load_df(SCORES_FILE, ["Joueur", "Points", "AncienRang"])
                if not df_v.empty:
                    df_gen["AncienRang"] = range(1, len(df_gen) + 1) if not df_gen.empty else 0
                    for _, row in df_v.iterrows():
                        j_nom = row['Joueur']
                        bons = sum(1 for m_n, _ in match_data if row[m_n] == reels[m_n])
                        pts = bons + (3 if bons == 8 else 0)
                        mask = df_gen['Joueur'].str.lower() == j_nom.lower()
                        if mask.any(): df_gen.loc[mask, 'Points'] = df_gen.loc[mask, 'Points'].astype(int) + pts
                        else: df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": j_nom, "Points": pts, "AncienRang": 0}])], ignore_index=True)
                    save_df(df_gen, SCORES_FILE)
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    st.success("Scores mis à jour !")
                    st.rerun()

        with t2:
            df_v = load_df(VOTES_FILE, ["Joueur"])
            if not df_v.empty:
                st.dataframe(df_v)
                st.download_button("📥 Sauvegarder les votes avant validation", df_v.to_csv(index=False), "backup_votes.csv")
            else: st.info("Aucun vote.")

        with t3:
            nouv_msg = st.text_area("Nouveau message", current_msg)
            if st.button("Mettre à jour"): save_text(MSG_FILE, nouv_msg); st.rerun()

        with t4:
            st.write(f"Statut : **{load_text(LOCK_FILE, 'unlocked')}**")
            if st.button("Fermer les votes"): save_text(LOCK_FILE, "locked"); st.rerun()
            if st.button("Ouvrir les votes"): save_text(LOCK_FILE, "unlocked"); st.rerun()

        with t5:
            st.markdown("### 🚑 Récupération des données")
            st.info("Utilisez cette section uniquement si le site a été réinitialisé.")
            
            # Restauration Classement
            st.subheader("1. Restaurer le Classement Général")
            file_score = st.file_uploader("Charger le fichier classement_general_backup.csv", type="csv")
            if file_score and st.button("Confirmer la restauration du CLASSEMENT"):
                df_rest = pd.read_csv(file_score)
                save_df(df_rest, SCORES_FILE)
                st.success("🏆 Classement restauré avec succès !")
                st.rerun()

            st.divider()

            # Restauration Votes
            st.subheader("2. Restaurer les Votes de la journée")
            file_votes = st.file_uploader("Charger le fichier backup_votes.csv", type="csv")
            if file_votes and st.button("Confirmer la restauration des VOTES"):
                df_rest_v = pd.read_csv(file_votes)
                save_df(df_rest_v, VOTES_FILE)
                st.success("🗳️ Votes restaurés avec succès !")
                st.rerun()

        with t6:
            if st.button("RÉINITIALISER TOUT"):
                if os.path.exists(SCORES_FILE): os.remove(SCORES_FILE)
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                st.rerun()
