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
    .header-box { 
        background-color: #004a99; 
        color: white !important; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        border-bottom: 4px solid #ffcc00; 
    }
    .header-box h1 { color: white !important; margin-bottom: 5px; font-size: 1.8rem !important; }
    .header-box p { color: white !important; font-size: 0.9rem !important; margin: 0; }
    .match-card { background: #f1f3f5; padding: 10px; border-radius: 8px; border-left: 5px solid #004a99; margin-top: 10px; font-weight: bold; color: #004a99 !important; }
    </style>
    """, unsafe_allow_html=True)

# Présentation mise à jour
st.markdown("""
    <div class="header-box">
        <h1>🏸 Le MPP de l'AOBD</h1>
        <p>Pronostique les 8 matchs : 1pt par bonne réponse + 3pts bonus si 8/8.<br>
        Joue à chaque journée pour faire grimper ton classement !</p>
    </div>
    """, unsafe_allow_html=True)

# 3. INTERFACE JOUEUR (VOTE)
st.subheader("1️⃣ Fais ton prono !")
nom = st.text_input("Ton Prénom & Nom :", placeholder="Ex: Lucas B").strip()

matchs = ["Simple Homme 1", "Simple Homme 2", "Simple Dame 1", "Simple Dame 2", 
          "Double Homme", "Double Dame", "Mixte 1", "Mixte 2"]

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
        st.success("C'est enregistré ! Attends la validation pour voir tes points.")
        st.balloons()

st.divider()

# 4. CLASSEMENT GÉNÉRAL (VISIBLE PAR TOUS)
st.subheader("🏆 CLASSEMENT GÉNÉRAL")
df_scores = load_data(SCORES_FILE)
if not df_scores.empty:
    # Tri par points décroissants pour voir le leader en haut
    st.table(df_scores.sort_values(by="Points", ascending=False))
else:
    st.info("Le classement sera mis à jour après la validation des matchs par l'admin.")

# 5. ESPACE ADMIN (SÉCURISÉ)
with st.expander("🛠️ ACCÈS ADMINISTRATEUR"):
    mdp = st.text_input("Entrez le mot de passe pour gérer les résultats :", type="password")
    
    if mdp == "2003":
        st.write("---")
        st.write("### ✅ Valider la rencontre")
        reels = {m: st.selectbox(f"Gagnant {m}", ["St-Nolff", "Adversaire"], key=f"adm_{m}") for m in matchs}
        
        if st.button("✅ CALCULER LES POINTS ET METTRE À JOUR LE CLASSEMENT"):
            df_v = load_data(VOTES_FILE)
            if df_v.empty:
                st.error("Personne n'a encore voté !")
            else:
                df_gen = load_data(SCORES_FILE)
                if df_gen.empty:
                    df_gen = pd.DataFrame(columns=["Joueur", "Points"])

                for index, row in df_v.iterrows():
                    joueur = row['Joueur']
                    bons = sum(1 for m in matchs if row[m] == reels[m])
                    pts_journee = bons + (3 if bons == 8 else 0)
                    
                    # MISE À JOUR SANS RÉINITIALISATION : 
                    # On cherche si le joueur existe déjà pour ajouter les points, sinon on le crée
                    if joueur in df_gen['Joueur'].values:
                        df_gen.loc[df_gen['Joueur'] == joueur, 'Points'] += pts_journee
                    else:
                        new_row = pd.DataFrame([{"Joueur": joueur, "Points": pts_journee}])
                        df_gen = pd.concat([df_gen, new_row], ignore_index=True)
                
                save_data(df_gen, SCORES_FILE)
                # On vide uniquement les votes de la journée, pas le classement général
                if os.path.exists(VOTES_FILE): 
                    os.remove(VOTES_FILE)
                
                st.success("Classement mis à jour avec succès !")
                st.rerun()
        
        st.write("---")
        if st.button("🗑️ Réinitialiser le classement (Fin de saison)"):
            if os.path.exists(SCORES_FILE): os.remove(SCORES_FILE)
            st.warning("Classement général supprimé.")
            st.rerun()
            
    elif mdp != "":
        st.error("Mot de passe incorrect.")
