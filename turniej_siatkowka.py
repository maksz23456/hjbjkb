import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - Livescore", layout="wide")

# --- 2. FUNKCJE POMOCNICZE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

def calculate_match_details(m):
    """Liczy sety i małe punkty dla pojedynczego meczu"""
    s1_total, s2_total = 0, 0
    p1_total, p2_total = 0, 0
    set_results = []
    
    for i in range(1, 6):
        p1 = int(m[f'S{i}_P1'])
        p2 = int(m[f'S{i}_P2'])
        if p1 > 0 or p2 > 0:
            p1_total += p1
            p2_total += p2
            set_results.append(f"{p1}:{p2}")
            if p1 > p2: s1_total += 1
            elif p2 > p1: s2_total += 1
            
    return s1_total, s2_total, p1_total, p2_total, ", ". join(set_results)

def update_tables():
    """Kompleksowe przeliczenie tabel"""
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        # Resetujemy wszystko: mecze, punkty, sety i małe punkty
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        
        group_matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        
        for _, m in group_matches.iterrows():
            s1, s2, p1_m, p2_m, _ = calculate_match_details(m)
            
            if s1 == 3 or s2 == 3:
                # Punktacja siatkarska
                pts1, pts2 = (3, 0) if s1 == 3 and s2 < 2 else ((2, 1) if s1 == 3 and s2 == 2 else ((1, 2) if s2 == 3 and s1 == 2 else (0, 3)))
                
                for t, sp, sm, pp, pm, p_pts, win in [
                    (m['Gospodarz'], s1, s2, p1_m, p2_m, pts1, s1>s2),
                    (m['Gość'], s2, s1, p2_m, p1_m, pts2, s2>s1)
                ]:
                    idx = df[df['Drużyna'] == t].index
                    if not idx.empty:
                        df.loc[idx, 'Mecze'] += 1
                        df.loc[idx, 'Wygrane'] += 1 if win else 0
                        df.loc[idx, 'Sety+'] += sp
                        df.loc[idx, 'Sety-'] += sm
                        df.loc[idx, 'Pkt+'] += pp
                        df.loc[idx, 'Pkt-'] += pm
                        df.loc[idx, 'Punkty'] += p_pts
        st.session_state.groups[g] = df

# --- 3. INICJALIZACJA (Z NOWYMI KOLUMNAMI) ---
expected_cols = ['Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2']

if 'matches' not in st.session_state or list(st.session_state.matches.columns) != expected_cols:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
        'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
        'Mecze': 0, 'Punkty': 0, 'Wygrane': 0, 'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
    }) for g in get_group_labels()}
    st.session_state.matches = pd.DataFrame(columns=expected_cols)

# --- 4. STYLE ---
def style_logic(row):
    color = '#a8c4e2' if row['Miejsce'] <= 2 else '#f7c27b'
    return [f'background-color: {color}; color: black; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else '' for col in row.index]

# --- 5. INTERFEJS ---
st.title("🏐 MP Juniorów - Oficjalne Wyniki")
update_tables()

t1, t2, t3 = st.tabs(["📊 Tabele i Mecze", "🏆 Faza Pucharowa", "✏️ Wprowadź Wynik"])

with t1:
    for g in get_group_labels():
        st.header(f"GRUPA {g}")
        cols = st.columns(2)
        for i, col in enumerate(cols):
            p_id = i + 1
            sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == p_id].copy()
            
            # Zaawansowane sortowanie siatkarskie
            sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 0.1)
            sub['P_Ratio'] = sub['Pkt+'] / sub['Pkt-'].replace(0, 0.1)
            sub = sub.sort_values(['Punkty', 'Wygrane', 'S_Ratio', 'P_Ratio'], ascending=False)
            sub.insert(0, 'Miejsce', range(1, 4))
            
            with col:
                st.subheader(f"Podgrupa {g}{p_id}")
                st.dataframe(sub.drop(columns=['S_Ratio', 'P_Ratio', 'Podgrupa_ID']).style.apply(style_logic, axis=1), hide_index=True, use_container_width=True)
                
                # Wyświetlanie szczegółowych meczów
                teams_in_sub = sub['Drużyna'].tolist()
                sub_m = st.session_state.matches[(st.session_state.matches['Grupa'] == g) & (st.session_state.matches['Gospodarz'].isin(teams_in_sub))]
                
                for _, m in sub_m.iterrows():
                    s1, s2, _, _, detailed = calculate_match_details(m)
                    if s1 > 0 or s2 > 0:
                        st.write(f"📝 {m['Gospodarz']} **{s1}:{s2}** {m['Gość']} _({detailed})_")
        st.divider()

with t2:
    st.header("🏁 Drabinka Finałowa")
    for g in get_group_labels():
        with st.expander(f"Awans z Grupy {g}"):
            # Pobieramy 1 i 2 miejsca z podgrup po posortowaniu
            def get_top(gid, pid):
                temp = st.session_state.groups[gid][st.session_state.groups[gid]['Podgrupa_ID'] == pid].copy()
                temp['R'] = temp['Sety+'] / temp['Sety-'].replace(0, 0.1)
                return temp.sort_values(['Punkty', 'Wygrane', 'R'], ascending=False)

            s1, s2 = get_top(g, 1), get_top(g, 2)
            t1_1, t1_2, t1_3 = s1.iloc[0]['Drużyna'], s1.iloc[1]['Drużyna'], s1.iloc[2]['Drużyna']
            t2_1, t2_2, t2_3 = s2.iloc[0]['Drużyna'], s2.iloc[1]['Drużyna'], s2.iloc[2]['Drużyna']
            
            c1, c2 = st.columns(2)
            c1.error(f"PF1: {t1_1} vs {t2_2}")
            c1.error(f"PF2: {t2_1} vs {t1_2}")
            c2.warning(f"O 5. miejsce: {t1_3} vs {t2_3}")
            c2.success("Wygrani Półfinałów -> Awans do 1/2 MP")

with t3:
    st.subheader("Nowy Mecz")
    with st.form("new_match", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 2])
        g_sel = c1.selectbox("Wybierz Grupę", get_group_labels())
        teams = st.session_state.groups[g_sel]['Drużyna'].tolist()
        d1 = c2.selectbox("Gospodarz", teams)
        d2 = c3.selectbox("Gość", [t for t in teams if t != d1])
        
        st.write("Punkty w setach (zostaw 0:0 jeśli set się nie odbył):")
        p_cols = st.columns(5)
        inputs = []
        for j in range(5):
            with p_cols[j]:
                p1 = st.number_input(f"Set {j+1} - G", 0, 45, 0)
                p2 = st.number_input(f"Set {j+1} - H", 0, 45, 0)
                inputs.extend([p1, p2])
        
        if st.form_submit_button("Zatwierdź Wynik"):
            st.session_state.matches.loc[len(st.session_state.matches)] = [g_sel, d1, d2] + inputs
            st.rerun()

    st.subheader("Edycja Bazy")
    st.session_state.matches = st.data_editor(st.session_state.matches, use_container_width=True, num_rows="dynamic")
    if st.button("🚨 RESET DANYCH"):
        st.session_state.clear()
        st.rerun()
