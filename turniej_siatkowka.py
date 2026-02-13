import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - Wyniki Szczegółowe", layout="wide")

# --- 2. FUNKCJE LOGICZNE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # A-H

def calculate_match_from_points(m):
    """Liczy wynik w setach na podstawie małych punktów z rzędu meczu"""
    s1_total, s2_total = 0, 0
    for i in range(1, 6):
        p1 = m[f'S{i}_P1']
        p2 = m[f'S{i}_P2']
        if p1 > p2: s1_total += 1
        elif p2 > p1: s2_total += 1
    return s1_total, s2_total

def update_tables():
    """Przelicza statystyki grup na podstawie wpisanych meczów"""
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        # Resetujemy statystyki
        for col in ['Mecze', 'Wygrane', 'Przegrane', 'Sety+', 'Sety-', 'Punkty']:
            df[col] = 0
        
        # Filtrujemy mecze dla grupy
        group_matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        
        for _, m in group_matches.iterrows():
            s1, s2 = calculate_match_from_points(m)
            
            if s1 == 3 or s2 == 3:
                # Punktacja siatkarska: 3:0/3:1=3pkt, 3:2=2pkt, 2:3=1pkt
                p1, p2 = (3, 0) if s1 == 3 and s2 < 2 else ((2, 1) if s1 == 3 and s2 == 2 else ((1, 2) if s2 == 3 and s1 == 2 else (0, 3)))
                
                for team, s_plus, s_minus, pts, win in [(m['Gospodarz'], s1, s2, p1, s1>s2), (m['Gość'], s2, s1, p2, s2>s1)]:
                    idx = df[df['Drużyna'] == team].index
                    if not idx.empty:
                        df.loc[idx, 'Mecze'] += 1
                        df.loc[idx, 'Wygrane'] += 1 if win else 0
                        df.loc[idx, 'Przegrane'] += 0 if win else 1
                        df.loc[idx, 'Sety+'] += s_plus
                        df.loc[idx, 'Sety-'] += s_minus
                        df.loc[idx, 'Punkty'] += pts
        st.session_state.groups[g] = df

# --- 3. INICJALIZACJA DANYCH (Z SAMONAPRAWĄ) ---
expected_columns = ['Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2']

if 'matches' not in st.session_state or list(st.session_state.matches.columns) != expected_columns:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
        'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
        'Mecze': 0, 'Wygrane': 0, 'Przegrane': 0, 'Sety+': 0, 'Sety-': 0, 'Punkty': 0
    }) for g in get_group_labels()}
    st.session_state.matches = pd.DataFrame(columns=expected_columns)

# --- 4. STYLE ---
def style_table(row):
    color = '#a8c4e2' if row['Miejsce'] <= 2 else '#f7c27b'
    return [f'background-color: {color}; color: black; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else '' for col in row.index]

# --- 5. INTERFEJS ---
st.title("🏐 System Wyników MP Juniorów")
update_tables()

t1, t2, t3 = st.tabs(["📊 Tabele i Wyniki", "🏆 Faza Pucharowa", "✏️ Zarządzanie Meczami"])

with t1:
    for g in get_group_labels():
        st.header(f"GRUPA {g}")
        cols = st.columns(2)
        for i, col in enumerate(cols):
            p_id = i + 1
            sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id].copy()
            # Sortowanie: Punkty -> Wygrane -> Stosunek Setów
            sub['Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 1)
            sub = sub.sort_values(['Punkty', 'Wygrane', 'Ratio'], ascending=False)
            sub.insert(0, 'Miejsce', range(1, 4))
            
            with col:
                st.subheader(f"Podgrupa {g}{p_id}")
                st.dataframe(sub.style.apply(style_table, axis=1), hide_index=True, use_container_width=True)
                
                # Wyniki meczów pod tabelą
                teams_in_sub = sub['Drużyna'].tolist()
                sub_m = st.session_state.matches[(st.session_state.matches['Grupa'] == g) & (st.session_state.matches['Gospodarz'].isin(teams_in_sub))]
                if not sub_m.empty:
                    for _, m in sub_m.iterrows():
                        r1, r2 = calculate_match_from_points(m)
                        st.write(f"🏐 {m['Gospodarz']} **{r1}:{r2}** {m['Gość']}")
        st.divider()

with t2:
    st.header("🏁 Awans do 1/2 Mistrzostw Polski")
    for g in get_group_labels():
        with st.expander(f"Drabinka Grupy {g}"):
            s1 = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == 1].sort_values(['Punkty', 'Wygrane'], ascending=False)
            s2 = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == 2].sort_values(['Punkty', 'Wygrane'], ascending=False)
            t1_1, t1_2, t1_3 = s1.iloc[0]['Drużyna'], s1.iloc[1]['Drużyna'], s1.iloc[2]['Drużyna']
            t2_1, t2_2, t2_3 = s2.iloc[0]['Drużyna'], s2.iloc[1]['Drużyna'], s2.iloc[2]['Drużyna']
            
            c1, c2 = st.columns(2)
            c1.error(f"PF1: {t1_1} vs {t2_2}")
            c1.error(f"PF2: {t2_1} vs {t1_2}")
            c2.warning(f"O 5. miejsce: {t1_3} vs {t2_3}")
            c2.success("ZWYCIĘZCY PF1 i PF2 AWANSUJĄ DO 1/2 MP")

with t3:
    st.subheader("Wpisz nowy mecz")
    with st.form("match_form"):
        c1, c2, c3 = st.columns([1, 2, 2])
        g_sel = c1.selectbox("Grupa", get_group_labels())
        teams = st.session_state.groups[g_sel]['Drużyna'].tolist()
        d1 = c2.selectbox("Gospodarz", teams)
        d2 = c3.selectbox("Gość", [t for t in teams if t != d1])
        
        st.write("Punkty w setach:")
        pts_cols = st.columns(5)
        points_input = []
        for j in range(5):
            with pts_cols[j]:
                p1 = st.number_input(f"Set {j+1} - G", 0, 40, 0, key=f"s{j}p1")
                p2 = st.number_input(f"Set {j+1} - H", 0, 40, 0, key=f"s{j}p2")
                points_input.extend([p1, p2])
        
        if st.form_submit_button("Zatwierdź mecz"):
            new_match = [g_sel, d1, d2] + points_input
            st.session_state.matches.loc[len(st.session_state.matches)] = new_match
            st.rerun()

    st.subheader("Lista meczów (edytuj lub usuń)")
    st.session_state.matches = st.data_editor(st.session_state.matches, use_container_width=True, num_rows="dynamic")
    if st.button("🔴 WYCZYŚĆ WSZYSTKIE DANE"):
        st.session_state.clear()
        st.rerun()
