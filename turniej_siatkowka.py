import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - System Wyników", layout="wide")

# --- 2. FUNKCJE LOGICZNE ---
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
    return s1_total, s2_total, p1_total, p2_total, ", ".join(set_results)

def update_tables():
    """Przelicza statystyki grup"""
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        for col in ['Mecze', 'Punkty', 'Wygrane', 'Sety+', 'Sety-', 'Pkt+', 'Pkt-']:
            df[col] = 0
        group_matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        for _, m in group_matches.iterrows():
            s1, s2, p1_m, p2_m, _ = calculate_match_details(m)
            if s1 == 3 or s2 == 3:
                pts1, pts2 = (3, 0) if s1 == 3 and s2 < 2 else ((2, 1) if s1 == 3 and s2 == 2 else ((1, 2) if s2 == 3 and s1 == 2 else (0, 3)))
                for t, sp, sm, pp, pm, p_pts, win in [(m['Gospodarz'], s1, s2, p1_m, p2_m, pts1, s1>s2), (m['Gość'], s2, s1, p2_m, p1_m, pts2, s2>s1)]:
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

# --- 3. INICJALIZACJA ---
expected_cols = ['Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2']

if 'matches' not in st.session_state or list(st.session_state.matches.columns) != expected_cols:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
        'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
        'Mecze': 0, 'Punkty': 0, 'Wygrane': 0, 'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
    }) for g in get_group_labels()}
    st.session_state.matches = pd.DataFrame(columns=expected_cols)

def get_sorted_subgroup(gid, pid):
    temp = st.session_state.groups[gid][st.session_state.groups[gid]['Podgrupa_ID'] == pid].copy()
    temp['S_Ratio'] = temp['Sety+'] / temp['Sety-'].replace(0, 0.1)
    temp['P_Ratio'] = temp['Pkt+'] / temp['Pkt-'].replace(0, 0.1)
    return temp.sort_values(['Punkty', 'Wygrane', 'S_Ratio', 'P_Ratio'], ascending=False)

# --- 4. INTERFEJS ---
st.title("🏐 MP Juniorów - System Turniejowy")
update_tables()

tab1, tab2, tab3 = st.tabs(["📊 Tabele i Wyniki", "🏆 Faza Pucharowa", "✏️ Wprowadź Wynik"])

with tab1:
    for g in get_group_labels():
        st.header(f"GRUPA {g}")
        cols = st.columns(2)
        for i, col in enumerate(cols):
            p_id = i + 1
            sub = get_sorted_subgroup(g, p_id)
            sub_display = sub.drop(columns=['S_Ratio', 'P_Ratio', 'Podgrupa_ID']).copy()
            sub_display.insert(0, 'Miejsce', range(1, 4))
            with col:
                st.subheader(f"Podgrupa {g}{p_id}")
                st.dataframe(sub_display, hide_index=True, use_container_width=True)
                # Wyniki pod tabelą
                teams_in_sub = sub['Drużyna'].tolist()
                sub_m = st.session_state.matches[(st.session_state.matches['Grupa'] == g) & (st.session_state.matches['Gospodarz'].isin(teams_in_sub))]
                for _, m in sub_m.iterrows():
                    s1, s2, _, _, detailed = calculate_match_details(m)
                    if s1 > 0 or s2 > 0:
                        st.write(f"🔹 {m['Gospodarz']} **{s1}:{s2}** {m['Gość']} _({detailed})_")
        st.divider()

with tab2:
    st.header("🏁 Drabinka Pucharowa - Mecze o Miejsca i Awans")
    st.success("🚀 Zwycięzcy Półfinałów uzyskują AWANS do 1/2 Mistrzostw Polski!")
    
    for g in get_group_labels():
        with st.expander(f"ZOBACZ ROZPISKĘ DLA GRUPY {g}", expanded=True):
            # Pobieramy posegregowane drużyny
            sub1 = get_sorted_subgroup(g, 1)
            sub2 = get_sorted_subgroup(g, 2)
            
            t1_1, t1_2, t1_3 = sub1.iloc[0]['Drużyna'], sub1.iloc[1]['Drużyna'], sub1.iloc[2]['Drużyna']
            t2_1, t2_2, t2_3 = sub2.iloc[0]['Drużyna'], sub2.iloc[1]['Drużyna'], sub2.iloc[2]['Drużyna']
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("### 🔥 Półfinały (Krzyże)")
                st.error(f"**PF1:** {t1_1} vs {t2_2}")
                st.error(f"**PF2:** {t2_1} vs {t1_2}")
                st.caption("Wygrani z tych meczów grają w 1/2 MP")
                
            with col_b:
                st.markdown("### 🏐 O 5. miejsce")
                st.warning(f"**Mecz o 5:** {t1_3} vs {t2_3}")
                st.write("")
                st.markdown("### 🥈 O 3. miejsce")
                st.write("Przegrany PF1 vs Przegrany PF2")

            with col_c:
                st.markdown("### 🏆 FINAŁ GRUPY")
                st.success("Wygrany PF1 vs Wygrany PF2")
                st.write("")
                st.info("Obaj finaliści mają zapewniony AWANS.")

with tab3:
    st.subheader("Dodaj wynik meczu")
    with st.form("new_match", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 2])
        g_sel = c1.selectbox("Grupa", get_group_labels())
        teams = st.session_state.groups[g_sel]['Drużyna'].tolist()
        d1 = c2.selectbox("Gospodarz", teams)
        d2 = c3.selectbox("Gość", [t for t in teams if t != d1])
        st.write("Punkty w setach:")
        p_cols = st.columns(5)
        pts = []
        for j in range(5):
            with p_cols[j]:
                p1 = st.number_input(f"S{j+1}-G", 0, 40, 0, key=f"p1_{j}")
                p2 = st.number_input(f"S{j+1}-H", 0, 40, 0, key=f"p2_{j}")
                pts.extend([p1, p2])
        if st.form_submit_button("Zatwierdź"):
            st.session_state.matches.loc[len(st.session_state.matches)] = [g_sel, d1, d2] + pts
            st.rerun()

    st.subheader("Edycja meczów")
    st.session_state.matches = st.data_editor(st.session_state.matches, use_container_width=True, num_rows="dynamic")
    if st.button("🔴 RESETUJ WSZYSTKO"):
        st.session_state.clear()
        st.rerun()
