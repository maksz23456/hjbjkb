import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA I STYLIZACJA (NAPRAWIONA) ---
st.set_page_config(page_title="MP Juniorów - Livescore", layout="wide")

# Poprawiony CSS - teraz bez błędów i w lepszej kolorystyce
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #1e293b; font-weight: 800; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        font-weight: 600; 
        font-size: 18px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICJALIZACJA ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

if 'groups' not in st.session_state:
    st.session_state.groups = {g: pd.DataFrame({
        'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)], 
        'Podgrupa_ID': [1,1,1,2,2,2],
        'Mecze': 0, 'Punkty': 0, 'Wygrane': 0, 'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
    }) for g in get_group_labels()}
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

if 'matches' not in st.session_state:
    st.session_state.matches = pd.DataFrame(columns=['Grupa', 'Gospodarz', 'Gość', 'S1_H', 'S1_G', 'S2_H', 'S2_G', 'S3_H', 'S3_G', 'S4_H', 'S4_G', 'S5_H', 'S5_G'])

# --- 3. SILNIK OBLICZEŃ ---
def recalculate_everything():
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        
        m_group = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        for _, m in m_group.iterrows():
            sh, sg, ph_t, pg_t = 0, 0, 0, 0
            for i in range(1, 6):
                try:
                    h, gp = int(m[f'S{i}_H']), int(m[f'S{i}_G'])
                    ph_t += h; pg_t += gp
                    if h > gp: sh += 1
                    elif gp > h: sg += 1
                except: continue
            
            if sh == 3 or sg == 3:
                p_h, p_g = (3, 0) if sh == 3 and sg < 2 else ((2, 1) if sh == 3 and sg == 2 else ((1, 2) if sg == 3 and sh == 2 else (0, 3)))
                for team, role in [(m['Gospodarz'], 'H'), (m['Gość'], 'G')]:
                    idx = df[df['Drużyna'] == team].index
                    if not idx.empty:
                        i = idx[0]
                        df.at[i, 'Mecze'] += 1
                        df.at[i, 'Punkty'] += p_h if role == 'H' else p_g
                        df.at[i, 'Wygrane'] += 1 if (role == 'H' and sh > sg) or (role == 'G' and sg > sh) else 0
                        df.at[i, 'Sety+'] += sh if role == 'H' else sg
                        df.at[i, 'Sety-'] += sg if role == 'H' else sh
                        df.at[i, 'Pkt+'] += ph_t if role == 'H' else pg_t
                        df.at[i, 'Pkt-'] += pg_t if role == 'H' else ph_t
        st.session_state.groups[g] = df

# --- 4. NOWE STYLOWANIE (CZYSTE I SPORTOWE) ---
def apply_clean_style(row):
    # Miejsce 1-2: Świeży zielony (awans)
    # Miejsce 3: Neutralny biały/szary
    if row['Miejsce'] <= 2:
        return ['background-color: #dcfce7; color: #166534; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else 'background-color: #f0fdf4' for col in row.index]
    return ['background-color: #ffffff; color: #1e293b' for _ in row.index]

recalculate_everything()

# --- 5. INTERFEJS ---
st.title("🏐 Panel Wyników MP Juniorów")

t1, t2 = st.tabs(["📊 TABELE", "⚙️ EDYCJA"])

with t1:
    for g in get_group_labels():
        st.subheader(f"🏆 {st.session_state.group_names[g]}")
        c1, c2 = st.columns(2)
        for p_id, col in enumerate([c1, c2]):
            with col:
                st.caption(f"Podgrupa {p_id+1}")
                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id+1].copy()
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 0.1)
                sub = sub.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                sub.insert(0, 'Miejsce', range(1, 4))
                
                st.dataframe(
                    sub.drop(columns=['S_Ratio', 'Podgrupa_ID']).style.apply(apply_clean_style, axis=1),
                    hide_index=True,
                    use_container_width=True
                )
        st.divider()

with t2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())
    
    # Zarządzanie drużynami
    with st.expander("📝 Zmień nazwy drużyn i grupy"):
        g_name = st.text_input("Nazwa grupy:", value=st.session_state.group_names[sel_g])
        if st.button("Zapisz nazwę grupy"):
            st.session_state.group_names[sel_g] = g_name
            st.rerun()
        
        teams_df = st.data_editor(st.session_state.groups[sel_g][['Drużyna']], hide_index=True, use_container_width=True)
        if st.button("Zapisz nazwy drużyn"):
            st.session_state.groups[sel_g]['Drużyna'] = teams_df['Drużyna'].values
            st.rerun()

    st.divider()

    # Dodawanie meczu
    st.markdown("### ➕ Dodaj nowy mecz")
    with st.form(key=f"fm_v6_{sel_g}"):
        t_list = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        h_team = c1.selectbox("Gospodarz", t_list)
        a_team = c2.selectbox("Gość", [t for t in t_list if t != h_team])
        
        st.write("Punkty w setach (S5 do 15):")
        p_cols = st.columns(5)
        res = []
        for j in range(5):
            with p_cols[j]:
                s_h = st.number_input(f"S{j+1}-H", 0, 45, 0, key=f"v6h_{j}_{sel_g}")
                s_g = st.number_input(f"S{j+1}-G", 0, 45, 0, key=f"v6g_{j}_{sel_g}")
                res.extend([s_h, s_g])
        
        if st.form_submit_button("DODAJ MECZ"):
            new_row = pd.DataFrame([[sel_g, h_team, a_team] + res], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_row], ignore_index=True)
            recalculate_everything()
            st.rerun()

    st.divider()
    st.markdown("### 🛠️ Lista meczów i korekta")
    curr_matches = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    edited_matches = st.data_editor(curr_matches, num_rows="dynamic", use_container_width=True)
    
    if st.button("ZAPISZ KOREKTY MECZÓW"):
        other_matches = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([other_matches, edited_matches], ignore_index=True)
        recalculate_everything()
        st.rerun()

    if st.button("🚨 CAŁKOWITY RESET"):
        st.session_state.clear()
        st.rerun()
