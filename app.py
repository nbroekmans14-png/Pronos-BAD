import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION
st.set_page_config(page_title="Pronos St-Nolff", page_icon="🏸", layout="centered")

# Fichiers de sauvegarde (pour ne jamais perdre les points)
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

# 2. STYLE CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .header-box { background-color: #004a99; color: white !important; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 4px solid #ffcc00; }
    .header-box h1 { color: white !important; font-size: 1.6rem !important; margin: 0; }
    .match-card { background: #f1f3f5; padding: 10px; border-radius: 8px; border-left: 5px solid #004a99; margin-top: 10px; font-weight: bold; color: #004a99 !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: #1a1a1a !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>🏸 AO ST-NOLFF PRONOS</h1></div>', unsafe_allow_html=True)

# 3. INTERFACE JOUEUR (VOTE)
st.subheader("1️⃣ Fais ton prono !")
nom = st.text_input("Ton Prénom & Nom :", placeholder="Ex: Lucas B").strip()

matchs = ["Simple Homme 1", "Simple Homme 2", "Simple Dame 1", "Simple Dame 2", 
          "Double Homme", "Double Dame", "Mixte 1", "Mixte 2"]

if nom:
    pronos = {}
    for m in matchs:
        st.markdown(f '<div class="match-card">{m}</div>', unsafe_allow_html=True)
        pronos[m] = st.radio(f"Vainqueur {m}", ["St-Nolff", "Adversaire"], key=f"p_{m}", horizontal=True, label_visibility="collapsed")
    
    if st.button("🚀 ENREGISTRER MON VOTE"):
        df_v = load_data(VOTES_FILE)
        nouveau_vote = {"Joueur": nom}
        nouveau_vote.update(pronos)
        df_v = pd.concat([df_v, pd.DataFrame([nouveau_vote])], ignore_index=True)
        save_data(df_v, VOTES_FILE)
        st.success("C'est enregistré ! Attend la fin des matchs pour voir tes points.")
        st.balloons()

st.divider()

# 4. CLASSEMENT GÉNÉRAL (VISIBLE PAR TOUS)
st.subheader("🏆 CLASSEMENT GÉNÉRAL")
df_scores = load_data(SCORES_FILE)
if not df_scores.empty:
    st.table(df_scores.sort_values(by="Points", ascending=False))
else:
    st.info("Le classement sera mis à jour après la validation des matchs par l'admin.")

# 5. ESPACE ADMIN (POUR TOI)
with st.expander("🛠️ ADMIN : GESTION DE LA RENCONTRE"):
    
    # --- SECTION VALIDATION DES POINTS ---
    st.write("### ✅ Valider la rencontre")
    st.write("Saisis les résultats réels :")
    reels = {m: st.selectbox(f"Gagnant {m}", ["-", "St-Nolff", "Adversaire"], key=f"adm_{m}") for m in matchs}
    
    if st.button("CALCULER LES POINTS DE TOUT LE MONDE"):
        df_v = load_data(VOTES_FILE)
        if df_v.empty:
            st.error("Personne n'a encore voté !")
        elif any(v == "-" for v in reels.values()):
            st.error("Remplis tous les résultats avant de valider.")
        else:
            df_gen = load_data(SCORES_FILE)
            if df_gen.empty:
                df_gen = pd.DataFrame(columns=["Joueur", "Points"])

            for index, row in df_v.iterrows():
                joueur = row['Joueur']
                bons = sum(1 for m in matchs if row[m] == reels[m])
                pts = bons + (3 if bons == 8 else 0)
                
                if joueur in df_gen['Joueur'].values:
                    df_gen.loc[df_gen['Joueur'] == joueur, 'Points'] += pts
                else:
                    df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": joueur, "Points": pts}])], ignore_index=True)
            
            save_data(df_gen, SCORES_FILE)
            if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
            st.success("Classement mis à jour ! Les votes ont été archivés.")
            st.rerun()

    st.divider()

    # --- SECTION RÉINITIALISATION (ZONE DANGER) ---
    st.write("### ⚠️ Zone de danger")
    if st.button("🗑️ Réinitialiser tout le classement à zéro"):
        st.session_state.confirm_reset = True

    if st.session_state.get('confirm_reset', False):
        st.warning("Êtes-vous sûr ? Cela effacera définitivement tous les points cumulés.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🔴 OUI, TOUT SUPPRIMER"):
                if os.path.exists(SCORES_FILE): os.remove(SCORES_FILE)
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                st.session_state.confirm_reset = False
                st.success("Classement réinitialisé.")
                st.rerun()
        with col_c2:
            if st.button("Annuler"):
                st.session_state.confirm_reset = False
                st.rerun()

st.markdown("<br><center><small>AO St-Nolff Badminton 🏸</small></center>", unsafe_allow_html=True)
