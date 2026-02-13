import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - Wyniki Szczegółowe", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

def calculate_match_from_points(sets_data):
    """Liczy wynik w setach na podstawie małych punktów"""
    s1_total, s2_total = 0, 0
    for p1, p2 in sets_data:
        if p1 > p2: s1_total += 1
        elif p2 > p1: s2_total += 1
    return s1_total, s2_total

def update_tables():
    """Przelicza tabele na podstawie historii meczów"""
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        for col in ['Mecze', 'Wygrane', 'Przegrane', 'Sety+', 'Sety-', 'Punkty']:
            df[col] = 0
        
        m_list = st.session_state.matches
        group_matches = m_list[m_list['Grupa'] == g]
        
        for _, m in group_matches.iterrows():
            sets = [(m['S1_P1'], m['S1_P2']), (m['S2_P1'], m['S2_P2']), 
                    (m['S3_P1'], m['S3_P2']), (m['S4_P1'], m['S4_P2']), (m['S5_P1'], m['S5_P2'])]
            s1, s2 = calculate_match_from_points(sets)
            
            if s1 == 3 or s2 == 3:
                # Punktacja siatkarska
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

# --- INICJALIZACJA ---
if 'matches' not in st.session_state:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
        'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
        'Mecze': 0, 'Wygrane': 0, 'Przegrane': 0, 'Sety+': 0, 'Sety-': 0, 'Punkty': 0
    }) for g in get_group_labels()}
    st.session_state.matches = pd.DataFrame(columns=[
        'Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2'
    ])

# --- INTERFEJS ---
st.title("🏐 System Wyników MP Juniorów")
update_tables()

t1, t2, t3 = st.tabs(["📊 Tabele i Wyniki", "🏆 Faza Pucharowa", "✏️ Wprowadź Mecz"])

with t1:
    for g in get_group_labels():
        st.header(f"GRUPA {g}")
        cols = st.columns(2)
        for i, col in enumerate(cols):
            p_id = i + 1
            sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id].copy()
            sub = sub.sort_values(['Punkty', 'Sety+'], ascending=False)
            sub.insert(0, 'Miejsce', range(1, 4))
            
            with col:
                st.subheader(f"Podgrupa {g}{p_id}")
                st.dataframe(sub, hide_index=True, use_container_width=True)
                
                # Wyświetlanie meczów tylko dla tej podgrupy
                teams_in_sub = sub['Drużyna'].tolist()
                sub_matches = st.session_state.matches[
                    (st.session_state.matches['Grupa'] == g) & 
                    (st.session_state.matches['Gospodarz'].isin(teams_in_sub))
                ]
                if not sub_matches.empty:
                    st.caption("Ostatnie mecze:")
                    for _, m in sub_matches.iterrows():
                        res1, res2 = calculate_match_from_points([(m['S1_P1'], m['S1_P2']), (m['S2_P1'], m['S2_P2']), (m['S3_P1'], m['S3_P2']), (m['S4_P1'], m['S4_P2']), (m['S5_P1'], m['S5_P2'])])
                        st.write(f"🔹 {m['Gospodarz']} **{res1}:{res2}** {m['Gość']}")
        st.divider()

with t3:
    st.subheader("Wpisz punkty w setach")
    with st.form("match_form"):
        c1, c2, c3 = st.columns([1, 2, 2])
        g_sel = c1.selectbox("Grupa", get_group_labels())
        teams = st.session_state.groups[g_sel]['Drużyna'].tolist()
        d1 = c2.selectbox("Gospodarz", teams)
        d2 = c3.selectbox("Gość", [t for t in teams if t != d1])
        
        st.write("Punkty w setach (np. 25:20):")
        s_cols = st.columns(5)
        res_sets = []
        for j in range(5):
            with s_cols[j]:
                p1 = st.number_input(f"Set {j+1} - Gosp.", 0, 50, 0, key=f"s{j}p1")
                p2 = st.number_input(f"Set {j+1} - Gość", 0, 50, 0, key=f"s{j}p2")
                res_sets.extend([p1, p2])
        
        if st.form_submit_button("Zapisz mecz"):
            new_row = [g_sel, d1, d2] + res_sets
            st.session_state.matches.loc[len(st.session_state.matches)] = new_row
            st.rerun()

    st.subheader("Historia wszystkich meczów")
    st.session_state.matches = st.data_editor(st.session_state.matches, use_container_width=True)
    if st.button("RESETUJ WSZYSTKO"):
        st.session_state.clear()
        st.rerun()

with t2:
    st.write("Automatyczna drabinka pucharowa (jak w poprzednim kodzie)...")
