import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(page_title="MPP AOBD", page_icon="🏸", layout="centered")

MATCH_NAMES = [
    "Simple Homme 1", "Simple Homme 2", 
    "Simple Dame 1", "Simple Dame 2", 
    "Double Homme", "Double Dame", 
    "Mixte 1", "Mixte 2"
]

JOURNEES_LISTE = [f"J{i}" for i in range(1, 11)]  # J1 à J10

# ---------------------------------------------------------
# CONNEXION ET GESTION GOOGLE SHEETS
# ---------------------------------------------------------
@st.cache_resource
def get_gspread_client():
    creds_dict = json.loads(st.secrets["gcp_json_credentials"], strict=False)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc.open_by_url(st.secrets["SPREADSHEET_URL"])

@st.cache_data(ttl=60)
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
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur de sauvegarde dans Google Sheets ({sheet_name}) : {e}")

def load_config_sheet():
    try:
        sh = get_gspread_client()
        worksheet = sh.worksheet("config")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame(columns=["Parametre", "Valeur"])

# ---------------------------------------------------------
# CONFIGURATION ET COTES
# ---------------------------------------------------------
def get_config():
    df = load_config_sheet()
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

# ---------------------------------------------------------
# SYNCHRONISATION
# ---------------------------------------------------------
current_j, lock_status, msg_admin = get_config()

if "current_j" not in st.session_state:
    st.session_state["current_j"] = current_j

current_j = st.session_state["current_j"]

# ---------------------------------------------------------
# STYLES VISUELS (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #31333F !important; }
    .header-box { background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 20px; border-radius: 0 0 15px 15px; text-align: center; margin: -60px -20px 10px -20px; }
    .header-box h1 { color: white !important; margin: 0; }
    .header-box p { color: #ffeb3b !important; margin-top: 5px; font-weight: bold; }
    .admin-msg { background-color: #f0f2f6 !important; padding: 12px; border-radius: 10px; text-align: center; font-weight: 700; margin: 15px 0; }
    .match-header { background-color: #f0f2f6 !important; padding: 6px 10px; font-weight: 700; border-radius: 6px; margin-top: 8px; }
    
    /* Styles spécifiques aux Statistiques (Thème React) */
    .card-box { background-color: #ffffff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .badge-win { background-color: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }
    .badge-loss { background-color: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }
    .box-piege { background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 12px; }
    .box-banque { background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# BANNIÈRE D'EN-TÊTE ET MESSAGE D'ANNONCE
st.markdown('<div class="header-box"><h1>Le MPP de l\'AOBD</h1><p>Cotes sur 100pts • +100pts si 8/8 • +100pts si Score Exact</p></div>', unsafe_allow_html=True)
if msg_admin:
    st.markdown(f'<div class="admin-msg">📢 {msg_admin}</div>', unsafe_allow_html=True)

# ONGLETS DE NAVIGATION
tab_prono, tab_class, tab_stats, tab_admin = st.tabs([
    "🎯 Pronostiquer", 
    "🏆 Classement", 
    "📊 Statistiques Saison",
    "🛠️ Administration"
])

# ---------------------------------------------------------
# 1. PRONOSTIQUER
# ---------------------------------------------------------
with tab_prono:
    st.subheader("🎯 Pronostics")
    
    idx_defaut = JOURNEES_LISTE.index(current_j) if current_j in JOURNEES_LISTE else 0
    j_prono = st.selectbox("Sélectionne la journée à consulter ou parier :", JOURNEES_LISTE, index=idx_defaut, key="select_j_prono")
    
    if j_prono != current_j:
        st.warning(f"🔒 Seule la **{current_j}** est actuellement ouverte aux votes. Tu peux consulter les cotes de la {j_prono}, mais tu ne peux pas parier dessus.")
    elif lock_status == "locked":
        st.warning(f"🔒 Les votes sont actuellement clos pour la {j_prono}.")
    else:
        st.success(f"🟢 Les votes sont ouverts pour la **{j_prono}** !")
        cotes_actuelles = get_cotes(j_prono)
        
        with st.form(key=f"form_pronostics_{j_prono}"):
            nom_input = st.text_input("Ton Prénom & Nom", key=f"input_nom_{j_prono}").strip()
            pronos = {}
            for m in MATCH_NAMES:
                cN, cA = cotes_actuelles[m]
                st.markdown(f'<div class="match-header">{m}</div>', unsafe_allow_html=True)
                pronos[m] = st.radio(
                    f"Vainqueur {m}", 
                    [f"St-Nolff 🐺 ({cN} pts)", f"Adversaire ({cA} pts)"], 
                    key=f"radio_{m}_{j_prono}", horizontal=True, label_visibility="collapsed"
                )
            
            submit = st.form_submit_button("🚀 VALIDER MA GRILLE")
            
            if submit:
                if not nom_input:
                    st.error("⚠️ Renseigne ton nom.")
                else:
                    df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                    
                    deja_vote = False
                    if not df_v.empty:
                        votes_j = df_v[df_v["Journee"].astype(str) == str(j_prono)]
                        deja_vote = (votes_j["Joueur"].astype(str).str.lower() == nom_input.lower()).any()

                    if deja_vote:
                        st.warning(f"⚠️ Ton vote pour la {j_prono} est déjà enregistré !")
                    else:
                        nolff = sum(1 for v in pronos.values() if "St-Nolff" in v)
                        score_p = f"{nolff}-{len(MATCH_NAMES) - nolff}"
                        nv = {"Journee": str(j_prono), "Joueur": nom_input, "ScoreFinalProno": score_p}
                        for k, v in pronos.items(): 
                            nv[k] = "St-Nolff" if "St-Nolff" in v else "Adversaire"
                        
                        df_v = pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True)
                        save_sheet("votes", df_v)
                        st.success(f"Vote enregistré avec succès pour la {j_prono} ! Score pronostiqué : {score_p}")
                        st.balloons()

# ---------------------------------------------------------
# 2. CLASSEMENT GÉNÉRAL
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 3. STATISTIQUES SAISON (ADAPTÉ DU COMPOSANT REACT)
# ---------------------------------------------------------
with tab_stats:
    df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
    df_res = load_sheet("resultats", ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])

    if df_res.empty or df_v.empty:
        st.info("Les statistiques apparaîtront dès la première journée validée.")
    else:
        j_validees = df_res["Journee"].astype(str).unique().tolist()
        df_v_valid = df_v[df_v["Journee"].astype(str).isin(j_validees)]

        # --- SECTION 1 : Pronostics vs Réalité par Match ---
        st.markdown("""
        <div class="card-box">
            <h3 style="margin:0; font-weight:bold;">📊 1. Pronostics vs Réalité par Match (Saint-Nolff)</h3>
            <p style="font-size: 13px; color: #6b7280; font-style: italic; margin-top:2px;">Mise à jour progressive au fil des journées.</p>
        </div>
        """, unsafe_allow_html=True)

        matches_stats = []
        for m in MATCH_NAMES:
            total_votes_m = 0
            votes_nolff_m = 0
            victoires_reelles_nolff = 0
            total_matchs_joues = len(j_validees)

            for j in j_validees:
                res_j = df_res[df_res["Journee"].astype(str) == str(j)]
                v_j = df_v_valid[df_v_valid["Journee"].astype(str) == str(j)]

                if not res_j.empty and res_j.iloc[0][m] == "St-Nolff":
                    victoires_reelles_nolff += 1

                if not v_j.empty:
                    total_votes_m += len(v_j)
                    votes_nolff_m += sum(1 for v in v_j[m] if v == "St-Nolff")

            pct_prono = round((votes_nolff_m / total_votes_m) * 100) if total_votes_m > 0 else 0
            pct_reel = round((victoires_reelles_nolff / total_matchs_joues) * 100) if total_matchs_joues > 0 else 0

            # Calcul du taux de succès global des joueurs sur ce match (pour la section imprévisibilité)
            bons_pronos = 0
            for j in j_validees:
                res_j = df_res[df_res["Journee"].astype(str) == str(j)]
                v_j = df_v_valid[df_v_valid["Journee"].astype(str) == str(j)]
                if not res_j.empty and not v_j.empty:
                    vrai = res_j.iloc[0][m]
                    bons_pronos += sum(1 for v in v_j[m] if v == vrai)

            acc_rate = round((bons_pronos / total_votes_m) * 100) if total_votes_m > 0 else 0

            matches_stats.append({
                "match": m,
                "prono": pct_prono,
                "reel": pct_reel,
                "accuracy": acc_rate
            })

        df_m_display = pd.DataFrame(matches_stats)
        df_m_display["Prono St-Nolff (%)"] = df_m_display["prono"].apply(lambda x: f"{x} %")
        df_m_display["Victoire Réelle St-Nolff (%)"] = df_m_display["reel"].apply(lambda x: f"{x} %")
        st.table(df_m_display[["match", "Prono St-Nolff (%)", "Victoire Réelle St-Nolff (%)"]].set_index("match"))

        # --- SECTION 2 : Classement au Taux de Réussite ---
        st.markdown("""
        <div class="card-box">
            <h3 style="margin:0; font-weight:bold;">🎯 2. Classement au Taux de Réussite (Précision)</h3>
            <p style="font-size: 13px; color: #6b7280; font-style: italic; margin-top:2px;">Mise à jour progressive au fil des journées.</p>
        </div>
        """, unsafe_allow_html=True)

        player_stats = []
        joueurs_uniques = df_v_valid["Joueur"].unique()
        
        # Nombre total de matchs joués jusqu'à présent dans la saison
        total_matchs_saison = len(j_validees) * len(MATCH_NAMES)

        for player in joueurs_uniques:
            df_p = df_v_valid[df_v_valid["Joueur"] == player]
            correct = 0

            for _, row in df_p.iterrows():
                j = str(row["Journee"])
                res_j = df_res[df_res["Journee"].astype(str) == j]
                if not res_j.empty:
                    for m in MATCH_NAMES:
                        if row[m] == res_j.iloc[0][m]:
                            correct += 1

            if total_matchs_saison > 0:
                rate_val = (correct / total_matchs_saison) * 100
                player_stats.append({
                    "player": player,
                    "correct": correct,
                    "total": total_matchs_saison,
                    "rate_num": rate_val,
                    "rate": f"{rate_val:.1f} %".replace(".", ",")
                })

        df_p_rank = pd.DataFrame(player_stats)
        if not df_p_rank.empty:
            df_p_rank = df_p_rank.sort_values(by="rate_num", ascending=False).reset_index(drop=True)
            
            medals = ['🥇', '🥈', '🥉']
            df_p_rank["Rang"] = [medals[i] if i < 3 else str(i + 1) for i in range(len(df_p_rank))]

            st.table(df_p_rank[["Rang", "player", "correct", "total", "rate"]].rename(columns={
                "player": "Joueur",
                "correct": "Bonnes réponses",
                "total": "Total Matchs Joués",
                "rate": "Taux de Réussite"
            }).set_index("Rang"))

        # --- SECTION 3 : Analyse d'Imprévisibilité ---
        st.markdown("""
        <div class="card-box">
            <h3 style="margin:0; font-weight:bold;">🔮 3. Analyse d'Imprévisibilité des Matchs</h3>
            <p style="font-size: 13px; color: #6b7280; font-style: italic; margin-top:2px;">Basé sur le taux de réussite global des pronostics.</p>
        </div>
        """, unsafe_allow_html=True)

        if matches_stats:
            sorted_by_acc = sorted(matches_stats, key=lambda x: x["accuracy"])
            hardest = sorted_by_acc[0]
            easiest = sorted_by_acc[-1]

            st.markdown(f"""
            <div class="box-piege">
                <h4 style="margin:0; color:#92400e; font-weight:bold;">🌀 Le Match le plus Imprévisible</h4>
                <p style="font-size: 16px; font-weight: bold; color: #b45309; margin: 4px 0;">{hardest['match']}</p>
                <p style="margin:0; color:#78350f; font-size:14px;">
                    🎯 <b>Seulement {hardest['accuracy']} %</b> des joueurs ont trouvé les bons résultats sur ce type de match.
                </p>
            </div>

            <div class="box-banque">
                <h4 style="margin:0; color:#1e40af; font-weight:bold;">🔒 Le Match le plus Prévisible</h4>
                <p style="font-size: 16px; font-weight: bold; color: #1d4ed8; margin: 4px 0;">{easiest['match']}</p>
                <p style="margin:0; color:#1e3a8a; font-size:14px;">
                    🎯 <b>{easiest['accuracy']} %</b> des pronostics ont vu juste sur ce match !
                </p>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. ADMINISTRATION
# ---------------------------------------------------------
with tab_admin:
    st.subheader("🛠️ Administration")
    if st.text_input("Code Administrateur", type="password") == st.secrets.get("ADMIN_PASSWORD", "2003"):
        
        st.markdown("### 🔓 Journée Ouverte aux Joueurs")
        st.info(f"Seule **une seule journée** est accessible aux votes à la fois. Actuellement : **{current_j}**")
        
        idx_actuel = JOURNEES_LISTE.index(current_j) if current_j in JOURNEES_LISTE else 0
        
        with st.form("form_change_journee"):
            j_selectionnee = st.selectbox("Choisir la journée unique à OUVRIR aux votes :", JOURNEES_LISTE, index=idx_actuel)
            btn_ouvrir = st.form_submit_button(f"📌 Ouvrir la {j_selectionnee} aux votes")
            
            if btn_ouvrir:
                save_config(j_selectionnee, "unlocked", f"Les votes sont ouverts pour la {j_selectionnee} !")
                st.session_state["current_j"] = j_selectionnee
                st.success(f"Succès ! Seule la {j_selectionnee} est désormais ouverte aux votes.")
                st.rerun()

        st.divider()

        t1, t_votes, t_cotes, t_annonce = st.tabs([
            "Valider les Résultats", 
            "👁️ Voir les Votes", 
            "Définir Cotes", 
            "📢 Message d'Annonce"
        ])
        
        # TAB 1 : VALIDER LES RÉSULTATS
        with t1:
            j_admin = st.session_state["current_j"]
            df_res = load_sheet("resultats", ["Journee"] + MATCH_NAMES + ["ScoreFinalReel"])
            deja_validee = not df_res.empty and (df_res["Journee"].astype(str) == str(j_admin)).any()

            if deja_validee:
                st.warning(f"⚠️ La {j_admin} a déjà été validée. Tu peux réenregistrer les scores réels ci-dessous si besoin.")

            st.write(f"Saisir les résultats réels pour la **{j_admin}** :")
            reels, res_n, res_a = {}, 0, 0
            for m in MATCH_NAMES:
                choice = st.selectbox(m, ["St-Nolff", "Adversaire"], key=f"adm_select_{m}_{j_admin}")
                reels[m] = choice
                if choice == "St-Nolff": res_n += 1
                else: res_a += 1
            
            score_reel = f"{res_n}-{res_a}"
            st.info(f"Score calculé : {score_reel}")
            
            if st.button(f"Calculer & Enregistrer les points pour la {j_admin}"):
                df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
                df_gen = load_sheet("classement", ["Joueur", "Points", "AncienRang"])
                cotes_j = get_cotes(j_admin)
                
                votes_c = df_v[df_v["Journee"].astype(str) == str(j_admin)] if not df_v.empty else pd.DataFrame()
                
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
                    
                    save_sheet("classement", df_gen)

                res_row = {"Journee": str(j_admin), "ScoreFinalReel": score_reel}
                res_row.update(reels)
                df_res = pd.concat([df_res[df_res["Journee"].astype(str) != str(j_admin)], pd.DataFrame([res_row])], ignore_index=True)
                save_sheet("resultats", df_res)

                idx_act = JOURNEES_LISTE.index(j_admin) if j_admin in JOURNEES_LISTE else 0
                idx_suiv = idx_act + 1
                next_j = JOURNEES_LISTE[idx_suiv] if idx_suiv < len(JOURNEES_LISTE) else j_admin

                df_c = load_sheet("cotes", ["Journee", "Match", "CoteNolff", "CoteAdv"])
                if df_c.empty or (df_c["Journee"].astype(str) != str(next_j)).all():
                    nouvelles_cotes_defaut = [{"Journee": str(next_j), "Match": m, "CoteNolff": 50, "CoteAdv": 50} for m in MATCH_NAMES]
                    df_c = pd.concat([df_c, pd.DataFrame(nouvelles_cotes_defaut)], ignore_index=True)
                    save_sheet("cotes", df_c)

                save_config(next_j, "unlocked", f"Les votes sont ouverts pour la {next_j} !")
                st.session_state["current_j"] = next_j

                st.success(f"✅ Journée {j_admin} validée ! L'application est maintenant ouverte **uniquement pour la {next_j}**.")
                st.rerun()

        # TAB 2 : CONSULTER LES VOTES
        with t_votes:
            st.subheader("📋 Pronostics enregistrés")
            j_consultee = st.selectbox("Choisir la journée à consulter :", JOURNEES_LISTE, index=idx_actuel)
            df_v = load_sheet("votes", ["Journee", "Joueur"] + MATCH_NAMES + ["ScoreFinalProno"])
            
            if df_v.empty:
                st.info("Aucun pronostic n'a encore été enregistré.")
            else:
                df_filtered = df_v[df_v["Journee"].astype(str) == str(j_consultee)]
                st.write(f"**Total votes enregistrés pour {j_consultee} :** {len(df_filtered)}")
                if not df_filtered.empty:
                    st.dataframe(df_filtered.set_index("Joueur"))
                else:
                    st.info(f"Aucun vote enregistré pour {j_consultee}.")

        # TAB 3 : DÉFINIR COTES
        with t_cotes:
            j_admin = st.session_state["current_j"]
            st.subheader(f"Définir les cotes pour la {j_admin}")
            st.caption("Ajuste les chances de victoire de St-Nolff sur 100 points.")
            
            df_c = load_sheet("cotes", ["Journee", "Match", "CoteNolff", "CoteAdv"])
            anciennes_cotes = get_cotes(j_admin)
            
            nouvelles_cotes = []
            for m in MATCH_NAMES:
                c_nolff = st.slider(f"Chances de St-Nolff ({m})", 5, 95, anciennes_cotes[m][0], step=5, key=f"slider_cote_{m}_{j_admin}")
                c_adv = 100 - c_nolff
                st.caption(f"👉 **St-Nolff :** {c_nolff} pts | **Adversaire :** {c_adv} pts")
                st.divider()
                nouvelles_cotes.append({"Journee": str(j_admin), "Match": m, "CoteNolff": c_nolff, "CoteAdv": c_adv})
            
            if st.button("Enregistrer les Cotes"):
                if not df_c.empty:
                    df_c = df_c[df_c["Journee"].astype(str) != str(j_admin)]
                df_c = pd.concat([df_c, pd.DataFrame(nouvelles_cotes)], ignore_index=True)
                save_sheet("cotes", df_c)
                st.success(f"Cotes enregistrées pour la {j_admin} !")
                st.rerun()

        # TAB 4 : ANNONCE & STATUT
        with t_annonce:
            st.subheader("📢 Message d'Annonce Général")
            msg = st.text_area("Rédiger / Modifier l'annonce :", msg_admin)
            
            st.subheader("🔒 Verrouillage Global des Votes")
            lock = st.radio("Autoriser les votes sur la journée ouverte ?", ["unlocked", "locked"], index=0 if lock_status == "unlocked" else 1)
            
            if st.button("Sauvegarder l'Annonce et le Statut"): 
                j_admin = st.session_state["current_j"]
                save_config(j_admin, lock, msg)
                st.success(f"Configuration sauvegardée pour {j_admin} !")
                st.rerun()
