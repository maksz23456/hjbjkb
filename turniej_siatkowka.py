import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="MP Juniorów - System Wyników", layout="wide")

# Wstrzyknięcie własnego CSS dla lepszego wyglądu
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    h1, h2, h3 { color: #1e3a8a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_all_with_markdown=True)

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

# --- 4. STYLOWANIE TABELI (NOWY WYGLĄD) ---
def apply_sport_style(row):
    # Miejsce 1-2: Elegancki błękit (awans)
    # Miejsce 3: Delikatny szary
    if row['Miejsce'] <= 2:
        return ['background-color: #1e3a8a; color: white; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else 'background-color: #ebf2ff; color: black' for col in row.index]
    else:
        return ['background-color: #f1f5f9; color: #475569' for _ in row.index]

recalculate_everything()

# --- 5. INTERFEJS ---
st.title("🏐 Młodzieżowe Mistrzostwa Polski")

tab1, tab2 = st.tabs(["📊 TABELE WYNIKÓW", "⚙️ PANEL ADMINISTRATORA"])

with tab1:
    for g in get_group_labels():
        with st.expander(f"🏆 {st.session_state.group_names[g]}", expanded=True):
            c1, c2 = st.columns(2)
            for p_id, col in enumerate([c1, c2]):
                with col:
                    st.subheader(f"Podgrupa {p_id+1}")
                    sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id+1].copy()
                    sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 0.1)
                    sub = sub.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                    sub.insert(0, 'Miejsce', range(1, 4))
                    
                    st.dataframe(
                        sub.drop(columns=['S_Ratio', 'Podgrupa_ID']).style.apply(apply_sport_style, axis=1),
                        hide_index=True,
                        use_container_width=True,
                        height=145
                    )

with tab2:
    sel_g = st.selectbox("Wybierz grupę do zarządzania:", get_group_labels())
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("### 🏷️ Nazwa")
        new_g_name = st.text_input("Edytuj nazwę grupy:", value=st.session_state.group_names[sel_g])
        if st.button("Aktualizuj nazwę"):
            st.session_state.group_names[sel_g] = new_g_name
            st.rerun()
    
    with col_b:
        st.markdown("### 🛡️ Drużyny")
        e_teams = st.data_editor(st.session_state.groups[sel_g][['Drużyna']], use_container_width=True, hide_index=True)
        if st.button("Zapisz Skład Grupy"):
            st.session_state.groups[sel_g]['Drużyna'] = e_teams['Drużyna'].values
            st.rerun()

    st.divider()

    st.markdown("### 📝 Dodaj Nowy Wynik")
    # FORMULARZ Z POPRAWIONYMI PRZYCISKAMI
    with st.form(f"form_v5_{sel_g}"):
        teams_list = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        host = c1.selectbox("Gospodarz", teams_list)
        visitor = c2.selectbox("Gość", [t for t in teams_list if t != host])
        
        st.write("Punkty w setach:")
        p_cols = st.columns(5)
        set_results = []
        for j in range(5):
            with p_cols[j]:
                s_h = st.number_input(f"S{j+1}-H", 0, 45, 0, key=f"nh_{j}_{sel_g}")
                s_v = st.number_input(f"S{j+1}-G", 0, 45, 0, key=f"nv_{j}_{sel_g}")
                set_results.extend([s_h, s_v])
        
        submit = st.form_submit_button("ZATWIERDŹ I DODAJ MECZ")
        if submit:
            new_m = pd.DataFrame([[sel_g, host, visitor] + set_results], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_m], ignore_index=True)
            recalculate_everything()
            st.rerun()

    st.divider()
    st.markdown("### 🛠️ Korekta meczów")
    cur_m = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    edited_m = st.data_editor(cur_m, num_rows="dynamic", key=f"edit_v5_{sel_g}", use_container_width=True)
    
    if st.button("💾 ZAPISZ KOREKTY"):
        other_m = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([other_m, edited_m], ignore_index=True)
        recalculate_everything()
        st.success("Dane przeliczone!")
        st.rerun()

    if st.button("🚨 RESET SYSTEMU"):
        st.session_state.clear()
        st.rerun()
