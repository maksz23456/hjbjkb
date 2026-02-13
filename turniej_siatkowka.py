import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Livescore MP - Statystyki", layout="wide")

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
    st.session_state.matches = pd.DataFrame(columns=['Grupa', 'Gospodarz', 'Gość', 'S1_H', 'S1_G', 'S2_H', 'S2_G', 'S3_H', 'S3_G', 'S4_H', 'S4_G', 'S5_H', 'S5_G'])

# --- 3. SILNIK OBLICZEŃ (NAJDOKŁADNIEJSZY) ---
def recalculate_everything():
    for g in get_group_labels():
        # Resetujemy wszystko do zera
        df = st.session_state.groups[g]
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        
        # Filtrujemy mecze dla tej grupy
        matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        
        for _, m in matches.iterrows():
            sh, sg = 0, 0
            ph_total, pg_total = 0, 0
            
            # Liczymy sety i małe punkty
            for i in range(1, 6):
                h = int(m[f'S{i}_H'])
                g_pts = int(m[f'S{i}_G'])
                if h > 0 or g_pts > 0:
                    ph_total += h
                    pg_total += g_pts
                    if h > g_pts: sh += 1
                    elif g_pts > h: sg += 1
            
            # Jeśli mecz jest zakończony (3 wygrane sety)
            if sh == 3 or sg == 3:
                # Punktacja tabeli
                p_h, p_g = (3, 0) if sh == 3 and sg < 2 else ((2, 1) if sh == 3 and sg == 2 else ((1, 2) if sg == 3 and sh == 2 else (0, 3)))
                
                # Aktualizacja statystyk gospodarza
                idx_h = df[df['Drużyna'] == m['Gospodarz']].index
                if not idx_h.empty:
                    i = idx_h[0]
                    df.at[i, 'Mecze'] += 1
                    df.at[i, 'Punkty'] += p_h
                    df.at[i, 'Wygrane'] += 1 if sh > sg else 0
                    df.at[i, 'Sety+'] += sh
                    df.at[i, 'Sety-'] += sg
                    df.at[i, 'Pkt+'] += ph_total
                    df.at[i, 'Pkt-'] += pg_total
                
                # Aktualizacja statystyk gościa
                idx_g = df[df['Drużyna'] == m['Gość']].index
                if not idx_g.empty:
                    i = idx_g[0]
                    df.at[i, 'Mecze'] += 1
                    df.at[i, 'Punkty'] += p_g
                    df.at[i, 'Wygrane'] += 1 if sg > sh else 0
                    df.at[i, 'Sety+'] += sg
                    df.at[i, 'Sety-'] += sh
                    df.at[i, 'Pkt+'] += pg_total
                    df.at[i, 'Pkt-'] += ph_total

# --- 4. WIDOK ---
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
                # Sortowanie: Punkty > Wygrane > Ratio Sety > Ratio Pkt
                sub_df['S_Ratio'] = sub_df['Sety+'] / sub_df['Sety-'].replace(0, 0.1)
                sub_df = sub_df.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                st.dataframe(sub_df.drop(columns=['S_Ratio', 'Podgrupa_ID']), hide_index=True, use_container_width=True)
                
                # LOG MECZÓW - tu sprawdzisz czy mecz się policzył
                st.caption("Mecze wliczone do statystyk:")
                group_matches = st.session_state.matches[(st.session_state.matches['Grupa'] == g)]
                for _, m in group_matches.iterrows():
                    # Wyświetl mecz tylko jeśli drużyna jest w tej podgrupie
                    if m['Gospodarz'] in sub_df['Drużyna'].values:
                        sh, sg = 0, 0
                        for i in range(1, 6):
                            if int(m[f'S{i}_H']) > int(m[f'S{i}_G']): sh += 1
                            elif int(m[f'S{i}_G']) > int(m[f'S{i}_H']): sg += 1
                        st.write(f"✅ {m['Gospodarz']} {sh}:{sg} {m['Gość']}")

with tab2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())
    
    # Edycja drużyn
    edited_teams = st.data_editor(st.session_state.groups[sel_g], column_config={"Drużyna": st.column_config.TextColumn(width="large")}, hide_index=True)
    if st.button("Zapisz Drużyny"):
        st.session_state.groups[sel_g] = edited_teams
        st.rerun()
        
    st.divider()
    
    # Dodawanie meczu
    with st.form("new_match"):
        teams = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        h = c1.selectbox("Gospodarz", teams)
        a = c2.selectbox("Gość", [t for t in teams if t != h])
        
        p_cols = st.columns(5)
        scores = []
        for j in range(5):
            with p_cols[j]:
                s_h = st.number_input(f"S{j+1}-H", 0, 45, 0)
                s_g = st.number_input(f"S{j+1}-G", 0, 45, 0)
                scores.extend([s_h, s_g])
        
        if st.form_submit_button("Dodaj Wynik"):
            new_m = pd.DataFrame([[sel_g, h, a] + scores], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_m], ignore_index=True)
            st.rerun()

    # EDYTOR MECZÓW - TU MOŻESZ WSZYSTKO POPRAWIĆ
    st.subheader("Popraw mecze (jeśli statystyki kłamią)")
    edited_m = st.data_editor(st.session_state.matches[st.session_state.matches['Grupa'] == sel_g], num_rows="dynamic")
    if st.button("Zapisz poprawki w wynikach"):
        # Usuwamy stare mecze z grupy i wstawiamy nowe z edytora
        st.session_state.matches = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([st.session_state.matches, edited_m], ignore_index=True)
        st.rerun()
