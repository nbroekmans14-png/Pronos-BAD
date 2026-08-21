import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

# Fichiers de données
HISTORIQUE_VOTES_FILE = "historique_votes.csv"
SCORES_FILE = "classement_general.csv"
MSG_FILE = "message_admin.txt"
CONFIG_FILE = "config_journee.txt" # Format: journee;status (ex: J1;unlocked)
RESULTATS_FILE = "historique_resultats.csv"

match_data = [
    ("Simple Homme 1", "👨"), ("Simple Homme 2", "👨"),
    ("Simple Dame 1", "👩"), ("Simple Dame 2", "👩"),
    ("Double Homme", "👬"), ("Double Dame", "👭"),
    ("Mixte 1", "👫"), ("Mixte 2", "👫")
]
MATCH_NAMES = [m[0] for m in match_data]

# --- FONCTIONS DE GESTION ---

def load_text(filename, default_text):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read().strip()
        except: return default_text
    return default_text

def save_text(filename, text):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def load_df(filename, columns):
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            if not df.empty: return df
        except: pass
    return pd.DataFrame(columns=columns)

def save_df(df, filename):
    df.to_csv(filename, index=False)

def get_config():
    raw = load_text(CONFIG_FILE, "J1;unlocked")
    parts = raw.split(";")
    if len(parts) == 2:
        return parts[0], parts[1]
    return "J1", "unlocked"

def set_config(journee, status):
    save_text(CONFIG_FILE, f"{journee};{status}")

# 2. DESIGN CSS
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    .header-box { background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 25px; border-radius: 0 0 20px 20px; text-align: center; margin: -60px -20px 10px -20px; }
    .header-box h1 { color: white !important; margin: 0; }
    .header-box p { color: #ffeb3b !important; margin-top: 5px; font-weight: bold; }
    .admin-msg { background-color: #f0f2f6 !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: 700; border: 1px solid #d1d5db; margin: 15px 0; }
    .match-header { background-color: #f0f2f6 !important; padding: 8px 12px; font-weight: 700; color: black !important; border-radius: 8px; margin-top: 10px; }
    .card-piege { background-color: #fff3cd; border: 2px dashed #ffebaa; border-radius: 12px; padding: 15px; text-align: center; color: #856404; font-weight: bold; margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
current_j, lock_status = get_config()
st.markdown(f'<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>Journée Actuelle : {current_j} • 1pt/match • +3pts si 8/8 • +3pts si Score Exact</p></div>', unsafe_allow_html=True)

current_msg = load_text(MSG_FILE, "Préparez vos pronos !")
st.markdown(f'<div class="admin-msg">📢 {current_msg}</div>', unsafe_allow_html=True)

# 3. NAVIGATION PAR ONGLETS (3 onglets utilisateurs + admin)
tab_prono, tab_class, tab_renc, tab_stats, tab_admin = st.tabs([
    "🎯 Pronostiquer", 
    "🏆 Classement", 
    "📅 Rencontres", 
    "📊 Statistiques Saison",
    "🛠️ Administration"
])

# ---------------------------------------------------------
# TAB 1 : PRONOSTIQUER
# ---------------------------------------------------------
with tab_prono:
    is_locked = (lock_status == "locked")
    
    if is_locked:
        st.warning(f"🔒 Les votes sont clos pour la journée **{current_j}**.")
    else:
        st.subheader(f"🎯 Fais tes pronos pour la {current_j}")
        
        with st.form("form_pronostics"):
            nom_input = st.text_input("Ton Prénom & Nom", placeholder="Ex: Lucas B").strip()
            
            pronos = {}
            for m_name, emoji in match_data:
                st.markdown(f'<div class="match-header">{emoji} {m_name}</div>', unsafe_allow_html=True)
                choice = st.radio(
                    f"Vainqueur {m_name}", 
                    ["St-Nolff 🐺", "Adversaire"], 
                    key=f"v_{m_name}", 
                    horizontal=True, 
                    label_visibility="collapsed"
                )
                pronos[m_name] = choice
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 VALIDER MA GRILLE")
            
            if submitted:
                if not nom_input:
                    st.error("⚠️ Veuille renseigner ton nom avant de valider.")
                else:
                    df_v = load_df(HISTORIQUE_VOTES_FILE, ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                    
                    deja_vote = False
                    if not df_v.empty:
                        mask = (df_v["Journee"].astype(str) == str(current_j)) & (df_v["Joueur"].str.lower() == nom_input.lower())
                        if mask.any():
                            deja_vote = True
                    
                    if deja_vote:
                        st.warning(f"Désolé {nom_input}, ton vote pour la {current_j} est déjà enregistré !")
                    else:
                        count_nolff = sum(1 for v in pronos.values() if v == "St-Nolff 🐺")
                        count_adv = len(match_data) - count_nolff
                        score_prono = f"{count_nolff}-{count_adv}"
                        
                        nv = {
                            "Journee": current_j,
                            "Joueur": nom_input,
                            "ScoreFinalProno": score_prono
                        }
                        for k, v in pronos.items(): 
                            nv[k] = "St-Nolff" if v == "St-Nolff 🐺" else "Adversaire"
                        
                        df_v = pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True)
                        save_df(df_v, HISTORIQUE_VOTES_FILE)
                        st.success(f"Vote enregistré pour la {current_j} ! Score pronostiqué : {score_prono}")
                        st.balloons()

# ---------------------------------------------------------
# TAB 2 : CLASSEMENT
# ---------------------------------------------------------
with tab_class:
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
        st.download_button("💾 Sauvegarder classement (CSV)", df_scores.to_csv(index=False), "classement_general.csv")
    else:
        st.info("Le classement sera affiché après la validation des premiers résultats.")

# ---------------------------------------------------------
# TAB 3 : RENCONTRES
# ---------------------------------------------------------
with tab_renc:
    st.subheader("📅 Rencontres & Tendances par Journée")
    
    df_votes = load_df(HISTORIQUE_VOTES_FILE, ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
    df_res = load_df(RESULTATS_FILE, ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
    
    journees_dispos = [current_j]
    if not df_votes.empty:
        journees_dispos = sorted(list(set(df_votes["Journee"].astype(str).tolist() + [current_j])))
    
    j_visu = st.selectbox("Choisir une journée :", journees_dispos, index=len(journees_dispos)-1)
    
    votes_j = df_votes[df_votes["Journee"].astype(str) == str(j_visu)] if not df_votes.empty else pd.DataFrame()
    res_j = df_res[df_res["Journee"].astype(str) == str(j_visu)] if not df_res.empty else pd.DataFrame()
    
    is_j_locked = (lock_status == "locked") if j_visu == current_j else True
    
    if votes_j.empty:
        st.info(f"Aucun vote enregistré pour la {j_visu}.")
    elif not is_j_locked and j_visu == current_j:
        st.warning(f"🔒 Les pronostics des autres joueurs pour la {j_visu} sont masqués jusqu'à la fermeture des votes.")
        st.metric("Nombre de votants actuels", len(votes_j))
    else:
        st.success(f"👀 Tendances de la {j_visu} ({len(votes_j)} votants)")
        
        total_votes = len(votes_j)
        stats = []
        piege_match = None
        piege_pct = 100.0
        
        for m_name in MATCH_NAMES:
            nolff_cnt = sum(1 for v in votes_j[m_name] if v == "St-Nolff")
            pct_nolff = round((nolff_cnt / total_votes) * 100)
            pct_adv = 100 - pct_nolff
            
            row_stat = {
                "Match": m_name,
                "St-Nolff 🐺": f"{pct_nolff} %",
                "Adversaire 🏸": f"{pct_adv} %"
            }
            
            if not res_j.empty:
                vrai_gagnant = res_j.iloc[0][m_name]
                reussite = pct_nolff if vrai_gagnant == "St-Nolff" else pct_adv
                
                row_stat["Vainqueur Réel"] = vrai_gagnant
                row_stat["Taux Réussite"] = f"{reussite} %"
                
                if reussite < piege_pct:
                    piege_pct = reussite
                    piege_match = (m_name, vrai_gagnant, reussite)
            
            stats.append(row_stat)
        
        st.table(pd.DataFrame(stats).set_index("Match"))
        
        if piege_match and piege_pct < 50:
            st.markdown(f'''
            <div class="card-piege">
                ⚠️ Match piège de la journée : {piege_match[0]}<br>
                Seulement {piege_pct}% des pronostiqueurs avaient prévu la victoire de {piege_match[1]} !
            </div>
            ''', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4 : STATISTIQUES SAISON (GÉNÉRALES)
# ---------------------------------------------------------
with tab_stats:
    st.subheader("📊 Statistiques de la Saison")
    
    df_votes = load_df(HISTORIQUE_VOTES_FILE, ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
    df_res = load_df(RESULTATS_FILE, ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
    
    if df_res.empty or df_votes.empty:
        st.info("Les statistiques de la saison seront disponibles dès qu'une première journée sera jouée et validée.")
    else:
        # Ne prendre en compte que les journées terminées/validées
        journees_validees = df_res["Journee"].astype(str).unique().tolist()
        df_v_validees = df_votes[df_votes["Journee"].astype(str).isin(journees_validees)]
        
        nb_j = len(journees_validees)
        tot_pronos = len(df_v_validees)
        
        c1, c2 = st.columns(2)
        c1.metric("Journées jouées", nb_j)
        c2.metric("Grilles validées au total", tot_pronos)
        
        st.divider()
        st.markdown("### 🎯 Taux de réussite global du club par type de match")
        
        stats_saison = []
        tot_bons_global = 0
        tot_pronos_matchs_global = 0
        
        for m_name in MATCH_NAMES:
            bons_match = 0
            total_match = 0
            
            for j in journees_validees:
                res_j = df_res[df_res["Journee"].astype(str) == j]
                votes_j = df_v_validees[df_v_validees["Journee"].astype(str) == j]
                
                if not res_j.empty and not votes_j.empty:
                    vrai_gagnant = res_j.iloc[0][m_name]
                    bons = sum(1 for v in votes_j[m_name] if v == vrai_gagnant)
                    cnt = len(votes_j)
                    
                    bons_match += bons
                    total_match += cnt
            
            pct_saison = round((bons_match / total_match) * 100) if total_match > 0 else 0
            tot_bons_global += bons_match
            tot_pronos_matchs_global += total_match
            
            stats_saison.append({
                "Discipline": m_name,
                "Pronos Corrects": f"{bons_match} / {total_match}",
                "Taux de réussite": pct_saison
            })
        
        df_saison_stats = pd.DataFrame(stats_saison).sort_values(by="Taux de réussite", ascending=False).reset_index(drop=True)
        
        # Mettre en avant le match le plus prévisible et le plus difficile
        if not df_saison_stats.empty:
            top_m = df_saison_stats.iloc[0]
            flop_m = df_saison_stats.iloc[-1]
            
            c_top, c_flop = st.columns(2)
            c_top.success(f"🟢 **Le + facile :** {top_m['Discipline']} ({top_m['Taux de réussite']}%)")
            c_flop.error(f"🔴 **Le + imprévisible :** {flop_m['Discipline']} ({flop_m['Taux de réussite']}%)")
        
        # Formater pour l'affichage du tableau
        df_saison_stats["Taux de réussite"] = df_saison_stats["Taux de réussite"].astype(str) + " %"
        st.table(df_saison_stats.set_index("Discipline"))

# ---------------------------------------------------------
# TAB 5 : ADMINISTRATION
# ---------------------------------------------------------
with tab_admin:
    st.subheader("🛠️ Administration")
    mdp = st.text_input("Code Administrateur", type="password")
    
    if mdp == st.secrets.get("ADMIN_PASSWORD", "2003"):
        t1, t2, t3, t4, t5 = st.tabs(["Validation Résultats", "Votants", "Annonce & Config", "Restauration", "RESET"])
        
        with t1:
            st.subheader(f"1. Valider les résultats pour : {current_j}")
            reels = {}
            res_n = 0
            res_a = 0
            
            for m_name, _ in match_data:
                choice_adm = st.selectbox(f"{m_name}", ["St-Nolff", "Adversaire"], key=f"adm_{m_name}")
                reels[m_name] = choice_adm
                if choice_adm == "St-Nolff": res_n += 1
                else: res_a += 1
            
            score_final_reel = f"{res_n}-{res_a}"
            st.markdown(f"**Score final calculé : {score_final_reel}**")

            if st.button("Calculer & Enregistrer les résultats"):
                df_v = load_df(HISTORIQUE_VOTES_FILE, ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                df_gen = load_df(SCORES_FILE, ["Joueur", "Points", "AncienRang"])
                df_res = load_df(RESULTATS_FILE, ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
                
                votes_curr = df_v[df_v["Journee"].astype(str) == str(current_j)] if not df_v.empty else pd.DataFrame()
                
                if not votes_curr.empty:
                    if not df_gen.empty:
                        df_gen_sorted = df_gen.sort_values(by="Points", ascending=False).reset_index(drop=True)
                        df_gen_sorted["AncienRang"] = df_gen_sorted.index + 1
                        df_gen = df_gen_sorted
                    
                    for _, row in votes_curr.iterrows():
                        j_nom = row['Joueur']
                        bons = sum(1 for m_n in MATCH_NAMES if row[m_n] == reels[m_n])
                        pts_jour = bons
                        if bons == 8: pts_jour += 3
                        if str(row.get('ScoreFinalProno')) == score_final_reel: pts_jour += 3
                        
                        mask = df_gen['Joueur'].str.lower() == j_nom.lower()
                        if mask.any(): 
                            df_gen.loc[mask, 'Points'] = df_gen.loc[mask, 'Points'].astype(int) + pts_jour
                        else: 
                            df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": j_nom, "Points": pts_jour, "AncienRang": 0}])], ignore_index=True)
                    
                    res_row = {"Journee": current_j, "ScoreFinalReel": score_final_reel}
                    res_row.update(reels)
                    df_res = pd.concat([df_res[df_res["Journee"].astype(str) != str(current_j)], pd.DataFrame([res_row])], ignore_index=True)
                    
                    save_df(df_gen, SCORES_FILE)
                    save_df(df_res, RESULTATS_FILE)
                    
                    st.success(f"Journée {current_j} validée avec succès !")
                    st.rerun()
                else:
                    st.error("Aucun vote enregistré pour cette journée.")

        with t2:
            st.subheader("Liste globale des votes")
            df_v = load_df(HISTORIQUE_VOTES_FILE, ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
            if not df_v.empty:
                st.dataframe(df_v)
                st.download_button("📥 Télécharger Historique VOTES (CSV)", df_v.to_csv(index=False), "historique_votes.csv")
            else: st.info("Aucun vote enregistré.")

        with t3:
            st.subheader("Message d'Annonce")
            nouv_msg = st.text_area("Message affiché en haut", current_msg)
            if st.button("Sauvegarder Message"):
                save_text(MSG_FILE, nouv_msg)
                st.success("Message mis à jour !")
                st.rerun()
            
            st.divider()
            st.subheader("Gestion de la Journée")
            c_j, c_l = st.columns(2)
            s_journee = c_j.text_input("Journée actuelle (ex: J1, J2, J3)", current_j)
            s_lock = c_l.radio("Verrouillage des votes", ["unlocked", "locked"], index=0 if lock_status == "unlocked" else 1)
            
            if st.button("Sauvegarder Configuration Journée"):
                set_config(s_journee, s_lock)
                st.success("Configuration sauvegardée !")
                st.rerun()

        with t4:
            st.subheader("Restauration")
            f_score = st.file_uploader("Restaurer Classement (CSV)", type="csv")
            if f_score and st.button("Restaurer Classement"):
                save_df(pd.read_csv(f_score), SCORES_FILE)
                st.rerun()
            st.divider()
            f_vote = st.file_uploader("Restaurer Historique Votes (CSV)", type="csv")
            if f_vote and st.button("Restaurer Votes"):
                save_df(pd.read_csv(f_vote), HISTORIQUE_VOTES_FILE)
                st.rerun()

        with t5:
            st.warning("⚠️ Attention, cette action efface toutes les données !")
            if st.button("RÉINITIALISER TOUTES LES DONNÉES"):
                for f in [SCORES_FILE, HISTORIQUE_VOTES_FILE, RESULTATS_FILE, CONFIG_FILE, MSG_FILE]:
                    if os.path.exists(f): os.remove(f)
                st.rerun()
