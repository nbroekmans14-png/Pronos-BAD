import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION
st.set_page_config(page_title="Pronos St-Nolff", page_icon="🏸", layout="centered")

# Fichiers de sauvegarde
VOTES_FILE = "tous_les_votes.csv"
SCORES_FILE = "classement_general.csv"

# Fonctions de sauvegarde
def save_data(df, filename):
    df.to_csv(filename, index=False)

def load_data(filename):
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# 2. STYLE CSS (Optimisé Mobile)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .header-box { background-color: #004a99; color: white !important; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 4px solid #ffcc00; }
    .header-box h1 { color: white !important; font-size: 1.6rem !important; }
    .match-card { background: #f1f3f5; padding: 10px; border-radius: 8px; border-left: 5px solid #004a99; margin-top: 15px; font-weight: bold; color: #004a99 !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: #1a1a1a !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>🏸 AO ST-NOLFF PRONOS</h1></div>', unsafe_allow_html=True)

# 3. INTERFACE JOUEUR (VOTE)
st.subheader("1️⃣ Fais ton prono !")
nom = st.text_input("👤 Ton Prénom & Nom :", placeholder="Ex: Lucas B").strip()

matchs = ["Simple Homme 1 🧔", "Simple Homme 2 🧔", "Simple Dame 1 👩", "Simple Dame 2 👩", 
          "Double Homme 👨‍🤝‍👨", "Double Dame 👩‍❤️‍👩", "Mixte 1 👫", "Mixte 2 👫"]

if nom:
    pronos = {}
    for m in matchs:
        st.markdown(f'<div class="match-card">{m}</div>', unsafe_allow_html=True)
        pronos[m] = st.radio(f"Vainqueur {m}", ["St-Nolff", "Adversaire"], key=f"p_{m}", horizontal=True, label_visibility="collapsed")
    
    if st.button("🚀 ENREGISTRER MON VOTE"):
        df_v = load_data(VOTES_FILE)
        nouveau_vote = {"Joueur": nom}
        nouveau_vote.update(pronos)
        df_v = pd.concat([df_v, pd.DataFrame([nouveau_vote])], ignore_index=True)
        save_data(df_v, VOTES_FILE)
        st.success(f"C'est enregistré {nom} ! Bonne chance.")
        st.balloons()

st.divider()

# 4. CLASSEMENT GÉNÉRAL
st.subheader("🏆 CLASSEMENT GÉNÉRAL")
df_scores = load_data(SCORES_FILE)
if not df_scores.empty:
    # Tri par points
    df_scores = df_scores.sort_values(by="Points", ascending=False)
    st.table(df_scores)
else:
    st.info("Le classement sera mis à jour après la rencontre.")

# 5. ESPACE ADMIN (Validation et Réinitialisation)
st.divider()
with st.expander("🛠️ MENU ADMINISTRATEUR"):
    
    # --- PARTIE VALIDATION ---
    st.write("--- 🏁 VALIDER UNE RENCONTRE ---")
    reels = {m: st.selectbox(f"Gagnant {m}", ["-", "St-Nolff", "Adversaire"], key=f"adm_{m}") for m in matchs}
    
    if st.button("✅ CALCULER LES POINTS"):
        df_v = load_data(VOTES_FILE)
        if df_v.empty:
            st.error("Aucun vote enregistré pour cette rencontre.")
        elif any(v == "-" for v in reels.values()):
            st.error("Remplis tous les résultats avant de valider.")
        else:
            df_gen = load_data(SCORES_FILE)
            if df_gen.empty:
                df_gen = pd
