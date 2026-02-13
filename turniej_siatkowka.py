import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Livescore MP - Naprawiony", layout="wide")

# --- 2. INICJALIZACJA I NAPRAWA STRUKTURY ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

# Funkcja sprawdzająca, czy tabela ma wszystkie kolumny
def ensure_match_columns():
    required = ['Grupa', 'Gospodarz', 'Gość', 'S1_H', 'S1_G', 'S2_H', 'S2_G', 'S3_H', 'S3_G', 'S4_H', 'S4_G', 'S5_H', 'S5_G']
    if 'matches' not in st.session_state or not isinstance(st.session_state.matches, pd.DataFrame):
        st.session_state.matches = pd.DataFrame(columns=required)
    else:
        # Jeśli brakuje jakiejś kolumny, dodaj ją
        for col in required:
            if col not in st.session_state.matches.columns:
                st.session_state.matches[col] = 0

if 'groups' not in st.session_state:
    st.session_state.groups = {g: pd.DataFrame({
        'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)], 
        'Podgrupa_ID': [1,1,1,2,2,2],
        'Mecze': 0, 'Punkty': 0, 'Wygrane': 0, 'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
    }) for g in get_group_labels()}
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

# Uruchom naprawę kolumn
ensure_match_columns()

# --- 3. SILNIK OBLICZEŃ (Z ZABEZPIECZENIEM PRZED BŁĘDAMI) ---
def recalculate_everything():
    for g in get_group_labels():
        df = st.session_state.groups[g]
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        
        matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        
        for _, m in matches.iterrows():
            sh, sg = 0, 0
            ph_total, pg_total = 0, 0
            
            # Przeliczanie setów
            for i in range(1, 6):
                try:
                    h = int(m[f'S{i}_H'])
                    g_pts = int(m[f'S{i}_G'])
                    ph_total += h
                    pg_total += g_pts
                    if h > g_pts: sh += 1
                    elif g_pts > h: sg += 1
                except: continue # Ignoruj błędy w pojedynczych polach
            
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
                        df.at[i, 'Pkt+'] += ph_total if role == 'H' else pg_total
                        df.at[i, 'Pkt-'] += pg_total if role == 'H' else ph_total

# --- 4. INTERFEJS ---
recalculate_everything()
tab1, tab2 = st.tabs(["📊 Tabele", "⚙️ Zarządzanie"])

with tab1:
    for g in get_group_labels():
        st.header(st.session_state.group_names[g])
        c1, c2 = st.columns(2)
        for p_id, col in enumerate([c1, c2]):
            with col:
                st.subheader(f"Podgrupa {p_id+1}")
                sub_df = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id+1].copy()
                sub_df['S_Ratio'] = sub_df['Sety+'] / sub_df['Sety-'].replace(0, 0.1)
                sub_df = sub_df.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                st.dataframe(sub_df.drop(columns=['S_Ratio', 'Podgrupa_ID']), hide_index=True, use_container_width=True)

with tab2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())
    
    # Zarządzanie drużynami
    with st.expander("Edytuj Nazwy Drużyn"):
        edited_teams = st.data_editor(st.session_state.groups[sel_g], column_config={"Drużyna": st.column_config.TextColumn(width="large")}, hide_index=True, key=f"t_ed_{sel_g}")
        if st.button("Zapisz Drużyny"):
            st.session_state.groups[sel_g] = edited_teams
            st.rerun()
        
    st.divider()
    
    # Dodawanie meczu
    st.subheader("➕ Dodaj Wynik")
    with st.form(key=f"new_m_{sel_g}"):
        teams = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        h_team = c1.selectbox("Gospodarz", teams)
        a_team = c2.selectbox("Gość", [t for t in teams if t != h_team])
        
        p_cols = st.columns(5)
        m_scores = []
        for j in range(5):
            with p_cols[j]:
                s_h = st.number_input(f"S{j+1}-H", 0, 45, 0, key=f"h_{j}_{sel_g}")
                s_g = st.number_input(f"S{j+1}-G", 0, 45, 0, key=f"g_{j}_{sel_g}")
                m_scores.extend([s_h, s_g])
        
        if st.form_submit_button("Zatwierdź mecz"):
            new_match = pd.DataFrame([[sel_g, h_team, a_team] + m_scores], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_match], ignore_index=True)
            st.rerun()

    st.divider()
    st.subheader("📝 Popraw mecze")
    # Pokazujemy mecze tylko z wybranej grupy do edycji
    current_matches = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    edited_m = st.data_editor(current_matches, num_rows="dynamic", key=f"m_ed_{sel_g}")
    
    if st.button("Zapisz poprawki"):
        # Usuwamy stare mecze z tej grupy i dodajemy te po poprawkach
        other_matches = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([other_matches, edited_m], ignore_index=True)
        st.rerun()

    if st.button("🚨 TOTALNY RESET (CZYŚCI WSZYSTKO)"):
        st.session_state.clear()
        st.rerun()
