import streamlit as st
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Pronos St-Nolff", 
    page_icon="🏸", 
    layout="centered"
)

# 2. STYLE OPTIMISÉ POUR MOBILE (Correction Couleurs et Tailles)
st.markdown("""
    <style>
    /* Forcer le fond en clair pour éviter le conflit mode sombre */
    .stApp { background-color: #ffffff; }
    
    /* Titre plus petit pour mobile */
    .header-box {
        background-color: #004a99;
        color: white !important;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
        border-bottom: 4px solid #ffcc00;
    }
    .header-box h1 {
        font-size: 1.5rem !important; /* Taille réduite */
        margin: 0;
        color: white !important;
    }

    /* Texte des questions et boutons radio en NOIR */
    .stMarkdown, p, b, label, .stRadio {
        color: #1a1a1a !important;
    }

    /* Cartes de match simplifiées */
    .match-card {
        background: #f1f3f5;
        padding: 8px;
        border-radius: 8px;
        border-left: 5px solid #004a99;
        margin-top: 15px;
        margin-bottom: 5px;
        font-weight: bold;
        color: #004a99 !important;
        font-size: 0.9rem;
    }

    /* Ajustement des colonnes sur mobile */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALISATION DES DONNÉES
if 'classement' not in st.session_state:
    st.session_state.classement = {} 
if 'votes_en_cours' not in st.session_state:
    st.session_state.votes_en_cours = {} 

# 4. PRÉSENTATION
st.markdown("""
    <div class="header-box">
        <h1>🏸 AO ST-NOLFF BAD</h1>
        <p style='margin:0;'>Pronos : 1pt/match + 3pts bonus</p>
    </div>
    """, unsafe_allow_html=True)

# 5. IDENTIFICATION
nom_joueur = st.text_input("👤 Ton Prénom & Nom :", placeholder="Ex: Lucas B").strip()

# 6. GRILLE DE PRONOSTICS
matchs = [
    "Simple Homme 1 🧔", "Simple Homme 2 🧔", 
    "Simple Dame 1 👩", "Simple Dame 2 👩", 
    "Double Homme 👨‍🤝‍👨", "Double Dame 👩‍❤️‍👩", 
    "Mixte 1 👫", "Mixte 2 👫"
]

if nom_joueur:
    st.subheader("📝 Tes Pronos")
    pronos_actuels = {}
    
    for i, m in enumerate(matchs):
        st.markdown(f'<div class="match-card">{m}</div>', unsafe_allow_html=True)
        # Radio horizontal pour gagner de la place sur mobile
        pronos_actuels[m] = st.radio(
            f"Vainqueur {m}", 
            ["St-Nolff", "Adversaire"], 
            key=f"p_{m}", 
            label_visibility="collapsed",
            horizontal=True 
        )

    if st.button("🚀 VALIDER MES CHOIX"):
        st.session_state.votes_en_cours[nom_joueur] = pronos_actuels
        st.success(f"Enregistré, merci {nom_joueur} !")
        st.balloons()

# 7. MENU ADMINISTRATEUR
st.divider()
with st.expander("🛠️ ESPACE ADMIN"):
    st.write("Résultats réels :")
    res_officiels = {}
    for m in matchs:
        res_officiels[m] = st.selectbox(f"{m}", ["-", "St-Nolff", "Adversaire"], key=f"adm_{m}")
    
    if st.button("🏆 VALIDER LA RENCONTRE"):
        if not any(v == "-" for v in res_officiels.values()):
            for joueur, ses_pronos in st.session_state.votes_en_cours.items():
                bons = sum(1 for m in matchs if ses_pronos[m] == res_officiels[m])
                total = bons + (3 if bons == 8 else 0)
                st.session_state.classement[joueur] = st.session_state.classement.get(joueur, 0) + total
            st.session_state.votes_en_cours = {}
            st.rerun()
        else:
            st.error("Remplis tous les scores !")

# 8. CLASSEMENT
st.subheader("🏆 CLASSEMENT")
if st.session_state.classement:
    data = [{"Joueur": k, "Pts": v} 
            for k, v in sorted(st.session_state.classement.items(), key=lambda item: item[1], reverse=True)]
    st.table(pd.DataFrame(data))
else:
    st.info("Aucun point validé.")
