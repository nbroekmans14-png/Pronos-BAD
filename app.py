import streamlit as st
import pandas as pd

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA SESSION STATE
# ------------------------------------------------------------------------------
if "announcement" not in st.session_state:
    st.session_state["announcement"] = "Bienvenue sur la plateforme de pronostics !"

# Structure d'exemple des journées (statut: 'pending' ou 'validated')
if "journees" not in st.session_state:
    st.session_state["journees"] = {
        "Journée 1": {"status": "pending", "matches": [("Équipe A", "Équipe B")]},
        "Journée 2": {"status": "pending", "matches": [("Équipe C", "Équipe D")]},
        "Journée 3": {"status": "pending", "matches": [("Équipe E", "Équipe F")]},
    }

# Pronostics et scores réels de test
if "user_predictions" not in st.session_state:
    st.session_state["user_predictions"] = {
        "Alice": {"Journée 1": {"match_1": (2, 1)}, "Journée 2": {"match_1": (1, 1)}},
        "Bob": {"Journée 1": {"match_1": (0, 3)}, "Journée 2": {"match_1": (2, 0)}}
    }

if "actual_results" not in st.session_state:
    st.session_state["actual_results"] = {
        "Journée 1": {"match_1": (2, 1)}, # Exemple: Score réel (2-1)
        "Journée 2": {"match_1": (0, 0)}
    }

# ------------------------------------------------------------------------------
# 2. CALCUL RIGOUREUX DES POINTS
# ------------------------------------------------------------------------------
def calculate_user_points(user, actual_results, user_predictions, journees):
    total_points = 0
    
    for j_name, j_data in journees.items():
        # Calculer uniquement pour les journées validées
        if j_data["status"] == "validated":
            if j_name in actual_results and j_name in user_predictions.get(user, {}):
                for match_key, real_score in actual_results[j_name].items():
                    pred_score = user_predictions[user][j_name].get(match_key)
                    
                    if pred_score and real_score:
                        r_h, r_a = real_score
                        p_h, p_a = pred_score
                        
                        # 1. Score Exact -> 3 points
                        if r_h == p_h and r_a == p_a:
                            total_points += 3
                        # 2. Bon vainqueur ou Match Nul -> 1 point
                        elif (r_h > r_a and p_h > p_a) or (r_h < r_a and p_h < p_a) or (r_h == r_a and p_h == p_a):
                            total_points += 1
                            
    return total_points

# ------------------------------------------------------------------------------
# 3. INTERFACE UTILISATEUR & ANNONCE
# ------------------------------------------------------------------------------
st.title("🏆 Plateforme de Pronostics")

# Affichage du message d'annonce s'il existe
if st.session_state["announcement"]:
    st.info(f"📢 **Annonce importante :** {st.session_state['announcement']}")

# ------------------------------------------------------------------------------
# 4. GESTION AUTOMATIQUE DE LA JOURNÉE COURANTE
# ------------------------------------------------------------------------------
def get_current_journee():
    for j_name, j_data in st.session_state["journees"].items():
        if j_data["status"] == "pending":
            return j_name
    return None # Toutes les journées sont validées

current_j = get_current_journee()

st.subheader("📝 Pronostics de la Journée")

if current_j:
    st.markdown(f"### En cours : **{current_j}**")
    st.write(f"Veuillez saisir vos pronostics pour la {current_j}.")
    
    # Formulaire de saisie pour la journée courante
    with st.form("form_pronos"):
        # Exemple simple d'inputs
        h_score = st.number_input("Score Équipe Domicile", min_value=0, max_value=20, value=0)
        a_score = st.number_input("Score Équipe Extérieur", min_value=0, max_value=20, value=0)
        
        submit = st.form_submit_button("Enregistrer mes pronostics")
        if submit:
            st.success(f"Pronostics enregistrés pour la {current_j} !")
else:
    st.success("🎉 Toutes les journées ont été validées et clôturées !")

# ------------------------------------------------------------------------------
# 5. CLASSEMENT ET POINTS GÉNÉRAUX
# ------------------------------------------------------------------------------
st.divider()
st.subheader("📊 Classement Général")

leaderboard = []
for user in st.session_state["user_predictions"].keys():
    pts = calculate_user_points(
        user, 
        st.session_state["actual_results"], 
        st.session_state["user_predictions"], 
        st.session_state["journees"]
    )
    leaderboard.append({"Participant": user, "Points": pts})

df_leaderboard = pd.DataFrame(leaderboard).sort_values(by="Points", ascending=False)
st.dataframe(df_leaderboard, use_container_width=True)

# ------------------------------------------------------------------------------
# 6. PANNEAU ADMIN
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ Panneau Admin")

# A. Section Message d'Annonce
st.sidebar.subheader("📢 Message d'Annonce")
new_announcement = st.sidebar.text_area("Rédiger / Modifier l'annonce :", st.session_state["announcement"])
if st.sidebar.button("Publier l'annonce"):
    st.session_state["announcement"] = new_announcement
    st.sidebar.success("Annonce mise à jour !")
    st.rerun()

st.sidebar.divider()

# B. Validation automatique des Journées
st.sidebar.subheader("✅ Validation de la Journée Courante")
if current_j:
    st.sidebar.write(f"Journée active : **{current_j}**")
    if st.sidebar.button(f"Valider et Clôturer {current_j}"):
        st.session_state["journees"][current_j]["status"] = "validated"
        st.sidebar.success(f"{current_j} validée ! Passage automatique à la suivante.")
        st.rerun()
else:
    st.sidebar.info("Toutes les journées sont déjà validées.")
