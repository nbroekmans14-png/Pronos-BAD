import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION ET PERSISTANCE
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

# Noms des fichiers (doivent être identiques pour la persistance)
VOTES_FILE = "tous_les_votes.csv"
SCORES_FILE = "classement_general.csv"
MSG_FILE = "message_admin.txt"
LOCK_FILE = "lock_status.txt"

# FONCTION DE SAUVEGARDE BLINDÉE
def save_to_disk(df, filename):
    try:
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        st.error(f"Erreur critique lors de la sauvegarde de {filename}: {e}")
        return False

# CHARGEMENT SÉCURISÉ
def load_from_disk(filename, default_type="df"):
    if os.path.exists(filename):
        try:
            if default_type == "df":
                return pd.read_csv(filename)
            else:
                with open(filename, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except:
            return pd.DataFrame() if default_type == "df" else ""
    return pd.DataFrame() if default_type == "df" else ""

# 2. DESIGN (FORCÉ POUR TOUS LES MODES)
st.markdown("""
    <style>
    :root { --primary: #d32f2f; --bg: white; --text: #31333F; }
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    
    .header-box { 
        background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); 
        padding: 25px; border-radius: 0 0 20px 20px; 
        text-align: center; margin: -60px -20px 10px -20px; 
    }
    .header-box h1 { color: white !important; }
    .header-box p { color: #ffeb3b !important; }

    .admin-msg { 
        background-color: #f0f2f6 !important; padding: 18px; 
        border-radius: 12px; text-align: center; 
        font-weight: 700; font-size: 1.15rem !important; 
        border: 1px solid #d1d5db; margin: 15px 0; 
    }

    .match-header { 
        background-color: #f0f2f6 !important; padding: 10px 15px; 
        font-weight: 700; color: #000000 !important; 
        border-radius: 8px; margin-top: 10px; 
    }
    
    .stButton>button { 
        background-color: #f0f2f6 !important; color: #31333F !important; 
        border: 1px solid #d1d5db !important; border-radius: 12px; 
        font-weight: bold; width: 100%; height: 3.5em; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES DONNÉES ---
if not os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "w") as f: f.write("unlocked")

# --- HEADER ---
st.markdown('<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>1pt par bon prono • +3pts bonus si 8/8</p></div>', unsafe_allow_html=True)

# --- MESSAGE ADMIN (CONSERVÉ) ---
current_msg = load_from_disk(MSG_FILE, "text")
if not current_msg: current_msg = "Préparez vos pronos !"
st.markdown(f'<div class="admin-msg">📢 {current_msg}</div>', unsafe_allow_html=True)

try:
    st.image("image_c4425f.jpg.jpeg", use_container_width=True)
except:
    pass

st.divider()

# 3. ESPACE VOTE
is_locked = load_from_disk(LOCK_FILE, "text") == "locked"

if is_locked:
    st.error("🔒 Les votes sont actuellement clos pour cette rencontre.")
else:
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
        for m_name, emoji in match_data:
            st.markdown(f'<div class="match-header">{emoji} {m_name}</div>', unsafe_allow_html=True)
            pronos[m_name] = st.radio(f"Vainqueur {m_name}", ["St-Nolff 🐺", "Adversaire"], key=f"v_{m_name}", horizontal=True, label_visibility="collapsed")
            st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)
            
        if st.button("🚀 VALIDER MA GRILLE"):
            df_v = load_from_disk(VOTES_FILE)
            if not df_v.empty and nom_input.lower() in df_v["Joueur"].str.lower().values:
                st.warning(f"Désolé {nom_input}, ton vote est déjà enregistré !")
            else:
                nouveau_vote = {"Joueur": nom_input}
                for k, v in pronos.items():
                    nouveau_vote[k] = "St-Nolff" if v == "St-Nolff 🐺" else v
                
                df_v = pd.concat([df_v, pd.DataFrame([nouveau_vote])], ignore_index=True)
                if save_to_disk(df_v, VOTES_FILE):
                    st.success("Vote bien enregistré ! Bonne chance 🐺")
                    st.balloons()

st.divider()

# 4. CLASSEMENT (CONSERVÉ)
st.subheader("🏆 Classement Général")
df_scores = load_from_disk(SCORES_FILE)
if not df_scores.empty:
    df_scores = df_scores.sort_values(by="Points", ascending=False).reset_index(drop=True)
    df_scores["Rang"] = df_scores.index + 1
    # Gestion de l'évolution
    if "AncienRang" not in df_scores.columns: df_scores["AncienRang"] = 0
    def get_evo(row):
        if row["AncienRang"] == 0: return "🆕"
        diff = int(row["AncienRang"]) - int(row["Rang"])
        return f"🟢 +{diff}" if diff > 0 else (f"🔴 {diff}" if diff < 0 else "〓")
    df_scores["Évo"] = df_scores.apply(get_evo, axis=1)
    st.table(df_scores[["Rang", "Évo", "Joueur", "Points"]].set_index("Rang"))
else:
    st.info("Le classement sera affiché après la validation de la première rencontre.")

# --- PHOTO SUPPORTERS ---
try:
    st.image("image_c4423b.jpg.jpeg", use_container_width=True)
except:
    pass

# 5. ADMINISTRATION RENFORCÉE
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🛠️ Administration"):
    mdp = st.text_input("Code", type="password")
    if mdp == "2003":
        t1, t2, t3, t4, t5 = st.tabs(["Résultats", "Votants", "Annonce", "Verrou", "RESET"])
        
        with t1:
            st.write("Entrez les résultats officiels :")
            reels = {m[0]: st.selectbox(f"{m[0]}", ["St-Nolff", "Adversaire"], key=f"adm_{m[0]}") for m in match_data}
            if st.button("Valider et calculer les points"):
                df_v = load_from_disk(VOTES_FILE)
                df_gen = load_from_disk(SCORES_FILE)
                if not df_v.empty:
                    if "AncienRang" not in df_gen.columns: df_gen["AncienRang"] = 0
                    for _, row in df_v.iterrows():
                        j_nom = row['Joueur']
                        bons = sum(1 for m, _ in match_data if row[m] == reels[m])
                        pts = bons + (3 if bons == 8 else 0)
                        
                        mask = df_gen['Joueur'].str.lower() == j_nom.lower()
                        if mask.any():
                            df_gen.loc[mask, 'Points'] += pts
                        else:
                            df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": j_nom, "Points": pts, "AncienRang": 0}])], ignore_index=True)
                    
                    save_to_disk(df_gen, SCORES_FILE)
                    # On efface les votes SEULEMENT ici
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    st.success("Classement mis à jour !")
                    st.rerun()

        with t2:
            df_v = load_from_disk(VOTES_FILE)
            if not df_v.empty:
                st.write(f"Nombre de votants : {len(df_v)}")
                st.dataframe(df_v[["Joueur"]])
                st.download_button("Sauvegarder les votes (CSV)", df_v.to_csv(index=False), "sauvegarde_votes.csv")
            else:
                st.info("Aucun vote enregistré pour le moment.")

        with t3:
            nouv_msg = st.text_area("Modifier le message d'annonce :", current_msg)
            if st.button("Enregistrer le message"):
                with open(MSG_FILE, "w", encoding="utf-8") as f:
                    f.write(nouv_msg)
                st.success("Message mis à jour !")
                st.rerun()

        with t4:
            lock_st = load_from_disk(LOCK_FILE, "text")
            st.write(f"Statut : **{'🔒 BLOQUÉ' if lock_st == 'locked' else '🔓 OUVERT'}**")
            if st.button("Bloquer les votes"):
                with open(LOCK_FILE, "w") as f: f.write("locked")
                st.rerun()
            if st.button("Débloquer les votes"):
                with open(LOCK_FILE, "w") as f: f.write("unlocked")
                st.rerun()

        with t5:
            st.warning("ZONE DANGEREUSE")
            if st.button("RÉINITIALISER TOUT LE CLASSEMENT"):
                if os.path.exists(SCORES_FILE): os.remove(SCORES_FILE)
                st.success("Le classement a été remis à zéro.")
                st.rerun()
