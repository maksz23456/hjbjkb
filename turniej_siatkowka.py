import streamlit as st
import pandas as pd

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="MP Juniorów - Oficjalne Wyniki", layout="wide")

# -------------------------------------------------
# MODERN SPORT DESIGN (DARK MODE OPTIMIZED)
# -------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    h1 {
        font-size: 42px !important;
        font-weight: 800 !important;
        color: white !important;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    h3 {
        color: #e2e8f0 !important;
        font-weight: 600;
        margin-top: 20px;
    }

    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        background-color: #1e293b;
        border-radius: 14px;
        padding: 10px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: #cbd5e1;
        font-weight: 600;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #2563eb, #06b6d4) !important;
        color: white !important;
    }

    /* Buttons Styling */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #06b6d4);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        transition: 0.3s;
        width: 100%;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 14px rgba(37,99,235,0.5);
        color: white;
    }

    .info-box {
        background: linear-gradient(90deg, #2563eb, #06b6d4);
        padding: 10px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        text-align: center;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# DATA INIT
# -------------------------------------------------
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # A-H

if 'groups' not in st.session_state:
    st.session_state.groups = {
        g: pd.DataFrame({
            'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)],
            'Podgrupa_ID': [1,1,1,2,2,2],
            'Mecze': 0, 'Punkty': 0, 'Wygrane': 0,
            'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
        }) for g in get_group_labels()
    }
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

if 'matches' not in st.session_state:
    st.session_state.matches = pd.DataFrame(columns=[
        'Grupa', 'Gospodarz', 'Gość',
        'S1_H','S1_G','S2_H','S2_G','S3_H','S3_G','S4_H','S4_G','S5_H','S5_G'
    ])

# -------------------------------------------------
# CALCULATION ENGINE
# -------------------------------------------------
def recalculate_everything():
    for g in get_group_labels():
        # Reset statystyk do zera przed przeliczeniem
        df = st.session_state.groups[g].copy()
        for col in ['Mecze','Punkty','Wygrane','Sety+','Sety-','Pkt+','Pkt-']:
            df[col] = 0

        m_group = st.session_state.matches[st.session_state.matches['Grupa'] == g]

        for _, m in m_group.iterrows():
            sh, sg, ph_total, pg_total = 0, 0, 0, 0

            # Przeliczanie setów i małych punktów
            for i in range(1, 6):
                try:
                    h = int(m[f'S{i}_H'])
                    v = int(m[f'S{i}_G'])
                    if h == 0 and v == 0: continue
                    
                    ph_total += h
                    pg_total += v
                    if h > v: sh += 1
                    elif v > h: sg += 1
                except:
                    continue

            # Logika punktacji (3:0, 3:1 -> 3 pkt; 3:2 -> 2 pkt; 2:3 -> 1 pkt)
            if sh == 3 or sg == 3:
                if sh == 3:
                    p_h, p_g = (3, 0) if sg < 2 else (2, 1)
                else:
                    p_h, p_g = (1, 2) if sh == 2 else (0, 3)

                # Aktualizacja statystyk gospodarza
                idx_h = df[df['Drużyna'] == m['Gospodarz']].index
                if not idx_h.empty:
                    i = idx_h[0]
                    df.at[i,'Mecze'] += 1
                    df.at[i,'Punkty'] += p_h
                    df.at[i,'Wygrane'] += 1 if sh > sg else 0
                    df.at[i,'Sety+'] += sh
                    df.at[i,'Sety-'] += sg
                    df.at[i,'Pkt+'] += ph_total
                    df.at[i,'Pkt-'] += pg_total

                # Aktualizacja statystyk gościa
                idx_g = df[df['Drużyna'] == m['Gość']].index
                if not idx_g.empty:
                    i = idx_g[0]
                    df.at[i,'Mecze'] += 1
                    df.at[i,'Punkty'] += p_g
                    df.at[i,'Wygrane'] += 1 if sg > sh else 0
                    df.at[i,'Sety+'] += sg
                    df.at[i,'Sety-'] += sh
                    df.at[i,'Pkt+'] += pg_total
                    df.at[i,'Pkt-'] += ph_total

        st.session_state.groups[g] = df

def apply_final_style(row):
    if row['Miejsce'] == 1:
        return ['background: linear-gradient(90deg,#16a34a,#22c55e); color: white; font-weight:700']*len(row)
    elif row['Miejsce'] == 2:
        return ['background: linear-gradient(90deg,#2563eb,#38bdf8); color:white; font-weight:600']*len(row)
    else:
        return ['background-color:#1e293b; color:#cbd5e1']*len(row)

# Uruchomienie przeliczenia przy każdym odświeżeniu
recalculate_everything()

# -------------------------------------------------
# UI - HEADER
# -------------------------------------------------
st.markdown("<h1>🏐 Mistrzostwa Polski Juniorów</h1>", unsafe_allow_html=True)

t1, t2 = st.tabs(["📊 TABELE WYNIKÓW", "⚙️ PANEL ADMINISTRATORA"])

# -------------------------------------------------
# TABELE
# -------------------------------------------------
with t1:
    for g in get_group_labels():
        # Sprawdzamy czy grupa ma jakąś nazwę lub mecze, by nie wyświetlać pustych sekcji (opcjonalnie)
        st.markdown(f"### {st.session_state.group_names[g]}")

        group_matches = st.session_state.matches[st.session_state.matches['Grupa']==g]
        total_matches = len(group_matches)

        st.markdown(f"<div class='info-box'>Rozegrane mecze: {total_matches}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        for p_id in [1,2]:
            with (c1 if p_id == 1 else c2):
                st.markdown(f"**Podgrupa {p_id}**")

                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID']==p_id].copy()

                # Ratio setów (zabezpieczenie przed dzieleniem przez 0)
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0,0.1)

                # Sortowanie: Punkty -> Wygrane mecze -> Ratio setów
                sub = sub.sort_values(['Punkty','Wygrane','S_Ratio'], ascending=False)
                sub.insert(0,'Miejsce', range(1, len(sub)+1))

                st.dataframe(
                    sub.drop(columns=['S_Ratio','Podgrupa_ID'])
                       .style.apply(apply_final_style, axis=1),
                    hide_index=True,
                    use_container_width=True
                )
        st.divider()

# -------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------
with t2:
    sel_g = st.selectbox("Wybierz grupę do edycji:", get_group_labels())

    col_cfg1, col_cfg2 = st.columns([1,1])
    
    with col_cfg1:
        st.markdown("### 📝 Nazwa Grupy")
        new_group_name = st.text_input("Zmień nazwę:", value=st.session_state.group_names[sel_g])
        if st.button("💾 Zapisz nazwę"):
            st.session_state.group_names[sel_g] = new_group_name
            st.rerun()

    with col_cfg2:
        st.markdown("### 🛡️ Zespoły")
        teams_df = st.session_state.groups[sel_g][['Drużyna']].copy()
        edited_teams = st.data_editor(teams_df, hide_index=True, use_container_width=True, num_rows="fixed")
        if st.button("💾 Zapisz zespoły"):
            st.session_state.groups[sel_g]['Drużyna'] = edited_teams['Drużyna'].values
            st.rerun()

    st.divider()

    # DODAWANIE MECZU
    st.markdown("### ➕ Dodaj wynik meczu")
    with st.form(key=f"form_match_{sel_g}"):
        t_list = st.session_state.groups[sel_g]['Drużyna'].tolist()

        c_form1, c_form2 = st.columns(2)
        h_team = c_form1.selectbox("Gospodarz", t_list)
        a_team = c_form2.selectbox("Gość", [t for t in t_list if t != h_team])

        st.write("Punkty w poszczególnych setach:")
        res = []
        for j in range(5):
            cA, cB = st.columns(2)
            with cA:
                s_h = st.number_input(f"Set {j+1} - {h_team}", 0, 45, 0, key=f"in_h_{sel_g}_{j}")
            with cB:
                s_g = st.number_input(f"Set {j+1} - {a_team}", 0, 45, 0, key=f"in_g_{sel_g}_{j}")
            res.extend([s_h, s_g])

        if st.form_submit_button("ZATWIERDŹ I DODAJ MECZ"):
            new_match = pd.DataFrame(
                [[sel_g, h_team, a_team] + res],
                columns=st.session_state.matches.columns
            )
            st.session_state.matches = pd.concat([st.session_state.matches, new_match], ignore_index=True)
            recalculate_everything()
            st.success(f"Dodano mecz: {h_team} vs {a_team}")
            st.rerun()

    st.divider()

    # EDYCJA MECZÓW
    st.markdown("### 🛠️ Lista meczów (Edycja / Usuwanie)")
    curr_matches = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    
    if not curr_matches.empty:
        edited_matches = st.data_editor(curr_matches, use_container_width=True, num_rows="dynamic")
        
        if st.button("💾 Zapisz zmiany w historii meczów"):
            # Zachowaj mecze z innych grup i połącz z edytowanymi
            other_matches = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
            st.session_state.matches = pd.concat([other_matches, edited_matches], ignore_index=True)
            recalculate_everything()
            st.rerun()
    else:
        st.info("Brak meczów w tej grupie.")

    st.divider()
    if st.button("🚨 TOTALNY RESET DANYCH (CZYŚCI WSZYSTKO)"):
        st.session_state.clear()
        st.rerun()
