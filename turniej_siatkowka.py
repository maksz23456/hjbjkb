import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Livescore MP - Auto-Refresh", layout="wide")

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

# --- 3. SILNIK OBLICZEŃ (WYMUSZONE ODŚWIEŻANIE) ---
def recalculate_everything():
    for g in get_group_labels():
        # Pobieramy czysty szablon drużyn
        df = st.session_state.groups[g].copy()
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        
        # Filtrujemy mecze
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
        
        # Nadpisujemy zaktualizowany DataFrame
        st.session_state.groups[g] = df

# --- 4. STYLOWANIE I WIDOK ---
def apply_style(row):
    color = 'background-color: #d1e7ff' if row['Miejsce'] <= 2 else 'background-color: #fff3cd'
    return [color if col in ['Miejsce', 'Drużyna'] else '' for col in row.index]

# WYWOŁANIE OBLICZEŃ NA SAMYM POCZĄTKU
recalculate_everything()

tab1, tab2 = st.tabs(["📊 Tabele", "⚙️ Zarządzanie"])

with tab1:
    for g in get_group_labels():
        st.header(st.session_state.group_names[g])
        c1, c2 = st.columns(2)
        for p_id, col in enumerate([c1, c2]):
            with col:
                st.subheader(f"Podgrupa {p_id+1}")
                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id+1].copy()
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 0.1)
                sub = sub.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                sub.insert(0, 'Miejsce', range(1, 4))
                st.dataframe(sub.drop(columns=['S_Ratio', 'Podgrupa_ID']).style.apply(apply_style, axis=1), hide_index=True, use_container_width=True)

with tab2:
    sel_g = st.selectbox("Wybierz grupę do edycji:", get_group_labels())
    
    # Edycja drużyn
    with st.expander("✏️ Edytuj Drużyny"):
        e_teams = st.data_editor(st.session_state.groups[sel_g], column_config={"Drużyna": st.column_config.TextColumn(width="large")}, hide_index=True)
        if st.button("Zapisz zmiany w drużynach"):
            st.session_state.groups[sel_g] = e_teams
            st.rerun()

    st.divider()

    # Dodawanie wyniku
    st.subheader("➕ Dodaj mecz")
    with st.form(f"add_m_{sel_g}"):
        teams = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        h, a = c1.selectbox("Gospodarz", teams), c2.selectbox("Gość", [t for t in teams if t != h])
        p_cols = st.columns(5)
        sc = []
        for j in range(5):
            with p_cols[j]:
                sc.extend([st.number_input(f"S{j+1}-H", 0, 45, 0), st.number_input(f"S{j+1}-G", 0, 45, 0)])
        
        if st.form_submit_button("Zatwierdź wynik"):
            new_m = pd.DataFrame([[sel_g, h, a] + sc], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_m], ignore_index=True)
            recalculate_everything() # Wymuszenie przeliczenia od razu
            st.rerun()

    st.divider()
    
    # Edycja meczów - TU DODANO WYMUSZENIE ODŚWIEŻANIA
    st.subheader("📝 Popraw wyniki")
    cur_m = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    edited_m = st.data_editor(cur_m, num_rows="dynamic", key=f"edit_{sel_g}")
    
    if st.button("💾 ZAPISZ I PRZELICZ TABELĘ"):
        # Podmieniamy mecze tylko dla tej grupy
        other_m = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([other_m, edited_m], ignore_index=True)
        recalculate_everything() # Kluczowy moment
        st.success("Tabela została zaktualizowana!")
        st.rerun()

    if st.button("🚨 RESET DANYCH"):
        st.session_state.clear()
        st.rerun()
