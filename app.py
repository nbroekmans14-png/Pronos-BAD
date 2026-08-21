import streamlit as st
import pandas as pd
import gspread

# CONFIGURATION
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

MATCH_NAMES = ["Simple Homme 1", "Simple Homme 2", "Simple Dame 1", "Simple Dame 2", 
               "Double Homme", "Double Dame", "Mixte 1", "Mixte 2"]

# --- CONNEXION GOOGLE SHEETS & NETTOYAGE CLE PEM ---
@st.cache_resource
def get_gspread_client():
    creds = dict(st.secrets["gcp_service_account"])
    
    # Nettoyage automatique du format de la clé privée PEM
    pk = str(creds["private_key"])
    if "\\n" in pk:
        pk = pk.replace("\\n", "\n")
    creds["private_key"] = pk

    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url(st.secrets["SPREADSHEET_URL"])
    return sh

def load_sheet(sheet_name, columns):
    try:
        sh = get_gspread_client()
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except Exception:
        return pd.DataFrame(columns=columns)

def save_sheet(sheet_name, df):
    try:
        sh = get_gspread_client()
        worksheet = sh.worksheet(sheet_name)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.astype(str).values.tolist())
    except Exception as e:
        st.error(f"Erreur de sauvegarde dans Google Sheets ({sheet_name}) : {e}")

# GESTION DYNAMIQUE DE LA CONFIGURATION (JOURNÉE, LOCK, MESSAGE)
def get_config():
    df = load_sheet("config", ["Parametre", "Valeur"])
    config_dict = {"current_j": "J1", "lock_status": "unlocked", "msg_admin": "Préparez vos pronos !"}
    
    if not df.empty:
        for _, row in df.iterrows():
            config_dict[str(row["Parametre"])] = str(row["Valeur"])
            
    return config_dict["current_j"], config_dict["lock_status"], config_dict["msg_admin"]

def save_config(current_j, lock_status, msg_admin):
    df = pd.DataFrame([
        {"Parametre": "current_j", "Valeur": current_j},
        {"Parametre": "lock_status", "Valeur": lock_status},
        {"Parametre": "msg_admin", "Valeur": msg_admin}
    ])
    save_sheet("config", df)

def get_cotes(journee):
    df = load_sheet("cotes", ["Journee", "Match", "CoteNolff", "CoteAdv"])
    cotes_j = df[df["Journee"].astype(str) == str(journee)] if not df.empty else pd.DataFrame()
    res = {}
    for m in MATCH_NAMES:
        if not cotes_j.empty:
            row = cotes_j[cotes_j["Match"] == m]
            if not row.empty:
                res[m] = (int(row.iloc[0]["CoteNolff"]), int(row.iloc[0]["CoteAdv"]))
                continue
        res[m] = (50, 50)
    return res

# STYLE CSS
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    .header-box { background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 20px; border-radius: 0 0 15px 15px; text-align: center; margin: -60px -20px 10px -20px; }
    .header-box h1 { color: white !important; margin: 0; }
    .header-box p { color: #ffeb3b !important; margin-top: 5px; font-weight: bold; }
    .admin-msg { background-color: #f0f2f6 !important; padding: 12px; border-radius: 10px; text-align: center; font-weight: 700; margin: 15px 0; }
    .match-header { background-color: #f0f2f6 !important; padding: 6px 10px; font-weight: 700; border-radius: 6px; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# CHARGEMENT CONFIG
current_j, lock_status, msg_admin = get_config()

# HEADER
st.markdown(f'<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>Journée Actuelle : {current_j} • Cotes sur 100pts • +100pts si 8/8 • +100pts si Score Exact</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="admin-msg">📢 {msg_admin}</div>', unsafe_allow_html=True)

# ONGLETS
tab_prono, tab_class, tab_stats, tab_admin = st.tabs([
    "🎯 Pronostiquer", 
    "🏆 Classement", 
    "📊 Statistiques Saison",
    "🛠️ Administration"
])

# 1. PRONOSTIQUER
with tab_prono:
    if lock_status == "locked":
        st.warning(f"🔒 Les votes sont clos pour la journée **{current_j}**.")
    else:
        st.subheader(f"🎯 Pronostics {current_j}")
        cotes_actuelles = get_cotes(current_j)
        
        with st.form("form_pronostics"):
            nom_input = st.text_input("Ton Prénom & Nom").strip()
            pronos = {}
            for m in MATCH_NAMES:
                cN, cA = cotes_actuelles[m]
                st.markdown(f'<div class="match-header">{m}</div>', unsafe_allow_html=True)
                pronos[m] = st.radio(
                    f"Vainqueur {m}", 
                    [f"St-Nolff 🐺 ({cN} pts)", f"Adversaire ({cA} pts)"], 
                    key=f"v_{m}", horizontal=True, label_visibility="collapsed"
                )
            
            if st.form_submit_button("🚀 VALIDER MA GRILLE"):
                if not nom_input:
                    st.error("⚠️ Renseigne ton nom.")
                else:
                    df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                    if not df_v.empty and ((df_v["Journee"].astype(str) == str(current_j)) & (df_v["Joueur"].astype(str).str.lower() == nom_input.lower())).any():
                        st.warning(f"Ton vote pour la {current_j} est déjà enregistré !")
                    else:
                        nolff = sum(1 for v in pronos.values() if "St-Nolff" in v)
                        score_p = f"{nolff}-{len(MATCH_NAMES) - nolff}"
                        nv = {"Journee": current_j, "Joueur": nom_input, "ScoreFinalProno": score_p}
                        for k, v in pronos.items(): 
                            nv[k] = "St-Nolff" if "St-Nolff" in v else "Adversaire"
                        
                        df_v = pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True)
                        save_sheet("votes", df_v)
                        st.success(f"Vote enregistré ! Score pronostiqué : {score_p}")
                        st.balloons()

# 2. CLASSEMENT
with tab_class:
    st.subheader("🏆 Classement Général")
    df_scores = load_sheet("classement", ["Joueur", "Points", "AncienRang"])
    if not df_scores.empty:
        df_scores["Points"] = pd.to_numeric(df_scores["Points"])
        df_scores = df_scores.sort_values(by="Points", ascending=False).reset_index(drop=True)
        df_scores["Rang"] = df_scores.index + 1
        
        def evo(r):
            if int(r["AncienRang"]) == 0: return "🆕"
            d = int(r["AncienRang"]) - int(r["Rang"])
            return f"🟢 +{d}" if d > 0 else (f"🔴 {d}" if d < 0 else "〓")
            
        df_scores["Évo"] = df_scores.apply(evo, axis=1)
        st.table(df_scores[["Rang", "Évo", "Joueur", "Points"]].set_index("Rang"))
    else:
        st.info("Aucun résultat validé pour le moment.")

# 3. STATISTIQUES SAISON
with tab_stats:
    st.subheader("📊 Statistiques de la Saison")
    df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
    df_res = load_sheet("resultats", ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
    
    if df_res.empty or df_v.empty:
        st.info("Statistiques disponibles après la validation d'une 1re journée.")
    else:
        j_validees = df_res["Journee"].astype(str).unique().tolist()
        df_v_valid = df_v[df_v["Journee"].astype(str).isin(j_validees)]
        
        st.markdown("### 🏸 Réussite et points rapportés par match")
        stats_m = []
        for m in MATCH_NAMES:
            bons_tot, v_tot, pts_match_tot = 0, 0, 0
            for j in j_validees:
                res_j = df_res[df_res["Journee"].astype(str) == j]
                v_j = df_v_valid[df_v_valid["Journee"].astype(str) == j]
                cotes_j = get_cotes(j)
                
                if not res_j.empty and not v_j.empty:
                    vrai = res_j.iloc[0][m]
                    cote_gagnante = cotes_j[m][0] if vrai == "St-Nolff" else cotes_j[m][1]
                    
                    bons = sum(1 for v in v_j[m] if v == vrai)
                    bons_tot += bons
                    pts_match_tot += bons * cote_gagnante
                    v_tot += len(v_j)
            
            pct = round((bons_tot / v_tot) * 100) if v_tot > 0 else 0
            stats_m.append({"Match": m, "Points distribués": f"{pts_match_tot} pts", "Taux de réussite": f"{pct} %"})
            
        st.table(pd.DataFrame(stats_m).set_index("Match"))
        
        st.divider()
        st.markdown("### 👤 Détail des points par participant")
        
        participants = []
        for joueur, group in df_v_valid.groupby("Joueur"):
            pts_matchs, bonus_8, bonus_score, grilles = 0, 0, 0, len(group)
            
            for _, row in group.iterrows():
                j = str(row["Journee"])
                res_j = df_res[df_res["Journee"].astype(str) == j]
                cotes_j = get_cotes(j)
                
                if not res_j.empty:
                    r_row = res_j.iloc[0]
                    bons = 0
                    pts_gagnes_j = 0
                    for m in MATCH_NAMES:
                        if row[m] == r_row[m]:
                            bons += 1
                            pts_gagnes_j += cotes_j[m][0] if r_row[m] == "St-Nolff" else cotes_j[m][1]
                    
                    pts_matchs += pts_gagnes_j
                    if bons == 8: bonus_8 += 100
                    if str(row["ScoreFinalProno"]) == str(r_row["ScoreFinalReel"]): bonus_score += 100
            
            total = pts_matchs + bonus_8 + bonus_score
            participants.append({
                "Joueur": joueur,
                "Grilles": grilles,
                "Pts Matchs": pts_matchs,
                "Bonus 8/8 (+100)": bonus_8,
                "Bonus Score Exact (+100)": bonus_score,
                "Total Points": total
            })
            
        df_part = pd.DataFrame(participants).sort_values(by="Total Points", ascending=False).reset_index(drop=True)
        st.table(df_part.set_index("Joueur"))

# 4. ADMINISTRATION
with tab_admin:
    st.subheader("🛠️ Administration")
    if st.text_input("Code Administrateur", type="password") == st.secrets.get("ADMIN_PASSWORD", "2003"):
        t1, t_cotes, t2 = st.tabs(["Valider Journée", "Définir Cotes", "Annonce & Config"])
        
        # Validation des résultats
        with t1:
            st.write(f"Résultats réels pour **{current_j}** :")
            reels, res_n, res_a = {}, 0, 0
            for m in MATCH_NAMES:
                choice = st.selectbox(m, ["St-Nolff", "Adversaire"], key=f"adm_{m}")
                reels[m] = choice
                if choice == "St-Nolff": res_n += 1
                else: res_a += 1
            
            score_reel = f"{res_n}-{res_a}"
            st.info(f"Score calculé : {score_reel}")
            
            if st.button("Calculer & Enregistrer les résultats"):
                df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                df_gen = load_sheet("classement", ["Joueur", "Points", "AncienRang"])
                df_res = load_sheet("resultats", ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
                cotes_j = get_cotes(current_j)
                
                votes_c = df_v[df_v["Journee"].astype(str) == str(current_j)] if not df_v.empty else pd.DataFrame()
                
                if not votes_c.empty:
                    if not df_gen.empty:
                        df_gen = df_gen.sort_values(by="Points", ascending=False).reset_index(drop=True)
                        df_gen["AncienRang"] = df_gen.index + 1
                    
                    for _, row in votes_c.iterrows():
                        j_nom = row['Joueur']
                        bons = 0
                        pts_jour = 0
                        for m in MATCH_NAMES:
                            if row[m] == reels[m]:
                                bons += 1
                                pts_jour += cotes_j[m][0] if reels[m] == "St-Nolff" else cotes_j[m][1]
                        
                        if bons == 8: pts_jour += 100
                        if str(row.get('ScoreFinalProno')) == score_reel: pts_jour += 100
                        
                        mask = df_gen['Joueur'].astype(str).str.lower() == j_nom.lower()
                        if mask.any(): 
                            df_gen.loc[mask, 'Points'] = df_gen.loc[mask, 'Points'].astype(int) + pts_jour
                        else: 
                            df_gen = pd.concat([df_gen, pd.DataFrame([{"Joueur": j_nom, "Points": pts_jour, "AncienRang": 0}])], ignore_index=True)
                    
                    res_row = {"Journee": current_j, "ScoreFinalReel": score_reel}
                    res_row.update(reels)
                    df_res = pd.concat([df_res[df_res["Journee"].astype(str) != str(current_j)], pd.DataFrame([res_row])], ignore_index=True)
                    
                    save_sheet("classement", df_gen)
                    save_sheet("resultats", df_res)
                    st.success("Résultats et classement sauvegardés !")
                    st.rerun()

        # Définition des cotes
        with t_cotes:
            st.subheader(f"Définir les cotes pour {current_j}")
            st.caption("Ajuste les chances de victoire de St-Nolff sur 100 points.")
            
            df_c = load_sheet("cotes", ["Journee", "Match", "CoteNolff", "CoteAdv"])
            anciennes_cotes = get_cotes(current_j)
            
            nouvelles_cotes = []
            for m in MATCH_NAMES:
                c_nolff = st.slider(f"Chances de St-Nolff ({m})", 5, 95, anciennes_cotes[m][0], step=5, key=f"cote_{m}")
                c_adv = 100 - c_nolff
                st.caption(f"👉 **St-Nolff :** {c_nolff} pts | **Adversaire :** {c_adv} pts")
                st.divider()
                nouvelles_cotes.append({"Journee": current_j, "Match": m, "CoteNolff": c_nolff, "CoteAdv": c_adv})
            
            if st.button("Enregistrer les Cotes sur Google Sheets"):
                if not df_c.empty:
                    df_c = df_c[df_c["Journee"].astype(str) != str(current_j)]
                df_c = pd.concat([df_c, pd.DataFrame(nouvelles_cotes)], ignore_index=True)
                save_sheet("cotes", df_c)
                st.success("Cotes enregistrées !")
                st.rerun()

        # Config de la journée (J1, J2, J3...)
        with t2:
            msg = st.text_area("Message d'annonce", msg_admin)
            if st.button("Sauvegarder Message"): 
                save_config(current_j, lock_status, msg)
                st.success("Message mis à jour !")
                st.rerun()
            
            st.divider()
            c1, c2 = st.columns(2)
            nj = c1.text_input("Journée (ex: J1, J2, J3...)", current_j)
            nl = c2.radio("Votes", ["unlocked", "locked"], index=0 if lock_status == "unlocked" else 1)
            if st.button("Sauvegarder Configuration Journée"): 
                save_config(nj, nl, msg_admin)
                st.success("Journée et verrouillage sauvegardés !")
                st.rerun()
