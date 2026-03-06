import streamlit as st
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Pronos AO St-Nolff", 
    page_icon="🏸", 
    layout="centered"
)

# 2. STYLE PERSONNALISÉ (Couleurs Club)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .header-box {
        background-color: #004a99;
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 5px solid #ffcc00;
    }
    .player-section {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .match-card {
        background: white;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid #004a99;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALISATION DES DONNÉES
if 'classement' not in st.session_state:
    st.session_state.classement = {} # Pour cumuler les points (Nom: Score)
if 'votes_en_cours' not in st.session_state:
    st.session_state.votes_en_cours = {} # Pour stocker les paris avant validation

# 4. PRÉSENTATION DU JEU
st.markdown("""
    <div class="header-box">
        <h1>🏸 AO ST-NOLFF BADMINTON</h1>
        <p style='font-size: 1.1em;'><b>Le Grand Jeu des Pronos</b></p>
        <p>🎯 1 pt par bon match | 🏅 +3 pts Bonus si 8/8 !</p>
    </div>
    """, unsafe_allow_html=True)

# 5. IDENTIFICATION DU JOUEUR
st.markdown('<div class="player-section">', unsafe_allow_html=True)
nom_joueur = st.text_input("👤 Entre ton Prénom et Nom :", placeholder="Ex: Lucas Bernard").strip()
st.markdown('</div>', unsafe_allow_html=True)

# 6. GRILLE DE PRONOSTICS
matchs = [
    "Simple Homme 1 🧔", "Simple Homme 2 🧔", 
    "Simple Dame 1 👩", "Simple Dame 2 👩", 
    "Double Homme 👨‍🤝‍👨", "Double Dame 👩‍❤️‍👩", 
    "Mixte 1 👫", "Mixte 2 👫"
]

if nom_joueur:
    st.header("📝 Tes Pronostics")
    st.info("Choisis qui gagnera chaque match selon toi :")
    
    pronos_actuels = {}
    col1, col2 = st.columns(2)
    
    for i, m in enumerate(matchs):
        dest_col = col1 if i < 4 else col2
        with dest_col:
            st.markdown(f'<div class="match-card">{m}</div>', unsafe_allow_html=True)
            pronos_actuels[m] = st.radio(f"Vainqueur {m}", ["St-Nolff", "Adversaire"], key=f"p_{m}", label_visibility="collapsed")

    if st.button("🚀 ENREGISTRER MES PRONOS"):
        st.session_state.votes_en_cours[nom_joueur] = pronos_actuels
        st.success(f"C'est tout bon {nom_joueur} ! Tes choix sont pris en compte.")
        st.balloons()

# 7. MENU ADMINISTRATEUR (Libre d'accès)
st.divider()
with st.expander("🛠️ ESPACE ADMINISTRATEUR"):
    st.write("Résultats réels de la rencontre :")
    res_officiels = {}
    c_adm1, c_adm2 = st.columns(2)
    for i, m in enumerate(matchs):
        z_adm = c_adm1 if i < 4 else c_adm2
        res_officiels[m] = z_adm.selectbox(f"Vainqueur {m}", ["-", "St-Nolff", "Adversaire"], key=f"adm_{m}")
    
    if st.button("🏆 VALIDER LA RENCONTRE ET COMPTER LES POINTS"):
        if any(v == "-" for v in res_officiels.values()):
            st.error("Attention : Tu dois remplir les 8 résultats avant de valider.")
        else:
            # Calcul pour chaque joueur ayant voté
            for joueur, ses_pronos in st.session_state.votes_en_cours.items():
                bons_matchs = sum(1 for m in matchs if ses_pronos[m] == res_officiels[m])
                points_matchs = bons_matchs
                bonus = 3 if bons_matchs == 8 else 0
                total_rencontre = points_matchs + bonus
                
                # Mise à jour du classement cumulé
                st.session_state.classement[joueur] = st.session_state.classement.get(joueur, 0) + total_rencontre
            
            # Reset des votes pour la rencontre suivante
            st.session_state.votes_en_cours = {}
            st.success("Points validés et ajoutés au classement !")
            st.rerun()

# 8. CLASSEMENT GÉNÉRAL
st.header("🏆 CLASSEMENT GÉNÉRAL DU CLUB")
if st.session_state.classement:
    # Création du tableau trié par points
    data = [{"Joueur": k, "Points Cumulés 🎖️": v} 
            for k, v in sorted(st.session_state.classement.items(), key=lambda item: item[1], reverse=True)]
    df = pd.DataFrame(data)
    st.table(df) # Affichage simple et clair
else:
    st.info("Aucun point n'a encore été validé par l'admin.")

# FOOTER
st.markdown("---")
st.caption("🏸 Application Pronos AO St-Nolff | Version Finale")
