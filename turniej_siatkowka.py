import streamlit as st
import pandas as pd

# --- 1. USTAWIENIA STRONY I STYLU ---
st.set_page_config(page_title="MP Juniorów - Oficjalne Wyniki", layout="wide")

# Nowoczesny, jasny styl sportowy
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTable { background-color: white; border-radius: 10px; }
    h1, h2, h3 { color: #0f172a; font-family: 'Inter', sans-serif; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICJALIZACJA DANYCH ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)] # A-H

if 'groups' not in st.session_state:
    st.session_state.groups = {g: pd.DataFrame({
        'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)], 
        # Ważne: pierwsze 3 to Podgrupa 1, kolejne 3 to Podgrupa 2
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

# --- 4. STYLOWANIE TABELI ---
def apply_final_style(row):
    # Zielony dla awansu (1-2), biały dla reszty
    if row['Miejsce'] <= 2:
        return ['background-color: #f0fdf4; color: #166534; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else 'background-color: #f0fdf4' for col in row.index]
    return ['background-color: white; color: #64748b' for _ in row.index]

recalculate_everything()

# --- 5. INTERFEJS ---
st.title("🏐 Panel Wyników MP Juniorów")

t1, t2 = st.tabs(["📊 TABELE I WYNIKI", "⚙️ PANEL ADMINISTRATORA"])

with t1:
    for g in get_group_labels():
        st.markdown(f"### 🏆 {st.session_state.group_names[g]}")
        c1, c2 = st.columns(2)
        
        # Filtrowanie podgrup - naprawa błędu z obrazka
        for p_id in [1, 2]:
            with (c1 if p_id == 1 else c2):
                st.write(f"**Podgrupa {p_id}**")
                # Filtrujemy tylko drużyny przypisane do danej podgrupy
                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id].copy()
                
                # Sortowanie sportowe
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 0.1)
                sub = sub.sort_values(['Punkty', 'Wygrane', 'S_Ratio'], ascending=False)
                sub.insert(0, 'Miejsce', range(1, 4))
                
                st.dataframe(
                    sub.drop(columns=['S_Ratio', 'Podgrupa_ID']).style.apply(apply_final_style, axis=1),
                    hide_index=True,
                    use_container_width=True
                )
        st.divider()

with t2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())
    
    # 1. Zarządzanie drużynami
    with st.expander("📝 Konfiguracja Drużyn", expanded=True):
        col_name, col_teams = st.columns([1, 2])
        with col_name:
            st.session_state.group_names[sel_g] = st.text_input("Nazwa grupy:", value=st.session_state.group_names[sel_g])
        with col_teams:
            # Edytujemy tylko kolumnę 'Drużyna', ID podgrupy jest ukryte/sztywne
            edited_teams = st.data_editor(st.session_state.groups[sel_g][['Drużyna']], hide_index=True, use_container_width=True)
            if st.button("ZATWIERDŹ NAZWY"):
                st.session_state.groups[sel_g]['Drużyna'] = edited_teams['Drużyna'].values
                st.rerun()

    st.divider()

    # 2. Dodawanie meczu
    st.markdown("### ➕ Dodaj wynik meczu")
    with st.form(key=f"final_form_{sel_g}"):
        t_list = st.session_state.groups[sel_g]['Drużyna'].tolist()
        col1, col2 = st.columns(2)
        h_team = col1.selectbox("Gospodarz", t_list)
        a_team = col2.selectbox("Gość", [t for t in t_list if t != h_team])
        
        p_cols = st.columns(5)
        res = []
        for j in range(5):
            with p_cols[j]:
                s_h = st.number_input(f"S{j+1}-H", 0, 45, 0)
                s_g = st.number_input(f"S{j+1}-G", 0, 45, 0)
                res.extend([s_h, s_g])
        
        if st.form_submit_button("DODAJ MECZ DO TABELI"):
            new_row = pd.DataFrame([[sel_g, h_team, a_team] + res], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_row], ignore_index=True)
            recalculate_everything()
            st.rerun()

    st.divider()
    # 3. Lista i Usuwanie
    st.markdown("### 🛠️ Korekta / Usuwanie")
    curr_matches = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    edited_matches = st.data_editor(curr_matches, num_rows="dynamic", use_container_width=True)
    
    if st.button("ZAPISZ ZMIANY W MECZACH"):
        other_matches = st.session_state.matches[st.session_state.matches['Grupa'] != sel_g]
        st.session_state.matches = pd.concat([other_matches, edited_matches], ignore_index=True)
        recalculate_everything()
        st.rerun()

    if st.button("🚨 WYCZYŚĆ WSZYSTKIE DANE"):
        st.session_state.clear()
        st.rerun()
