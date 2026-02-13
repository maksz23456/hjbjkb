import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - System Wyników", layout="wide")

# --- 2. FUNKCJE POMOCNICZE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

def calculate_match_details(m):
    s1, s2, p1_t, p2_t = 0, 0, 0, 0
    res = []
    for i in range(1, 6):
        try:
            p1, p2 = int(m[f'S{i}_P1']), int(m[f'S{i}_P2'])
            if p1 > 0 or p2 > 0:
                p1_t += p1; p2_t += p2
                res.append(f"{p1}:{p2}")
                if p1 > p2: s1 += 1
                elif p2 > p1: s2 += 1
        except: continue
    return s1, s2, p1_t, p2_t, ", ".join(res)

def update_tables():
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

# --- 3. INICJALIZACJA DANYCH ---
if 'group_names' not in st.session_state:
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

expected_cols = ['Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2']
if 'matches' not in st.session_state or list(st.session_state.matches.columns) != expected_cols:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1,1,1,2,2,2], 
        'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)], 
        'Mecze':0, 'Punkty':0, 'Wygrane':0, 'Sety+':0, 'Sety-':0, 'Pkt+':0, 'Pkt-':0
    }) for g in get_group_labels()}
    st.session_state.matches = pd.DataFrame(columns=expected_cols)

def get_sorted_subgroup(gid, pid):
    temp = st.session_state.groups[gid][st.session_state.groups[gid]['Podgrupa_ID'] == pid].copy()
    temp['S_Ratio'] = temp['Sety+'] / temp['Sety-'].replace(0, 0.1)
    temp['P_Ratio'] = temp['Pkt+'] / temp['Pkt-'].replace(0, 0.1)
    return temp.sort_values(['Punkty', 'Wygrane', 'S_Ratio', 'P_Ratio'], ascending=False)

# --- 4. INTERFEJS ---
st.title("🏐 System MP Juniorów")
update_tables()

tab1, tab2, tab3 = st.tabs(["📊 Tabele i Wyniki", "🏆 Faza Pucharowa", "✏️ Zarządzanie"])

with tab1:
    for g in get_group_labels():
        st.header(st.session_state.group_names[g])
        cols = st.columns(2)
        for i, col in enumerate(cols):
            sub = get_sorted_subgroup(g, i+1)
            sub_display = sub.drop(columns=['S_Ratio', 'P_Ratio', 'Podgrupa_ID']).copy()
            sub_display.insert(0, 'Miejsce', range(1, 4))
            with col:
                st.subheader(f"Podgrupa {i+1}")
                st.dataframe(sub_display, hide_index=True, use_container_width=True)
                teams_in_sub = sub['Drużyna'].tolist()
                sub_m = st.session_state.matches[(st.session_state.matches['Grupa'] == g) & (st.session_state.matches['Gospodarz'].isin(teams_in_sub))]
                for _, m in sub_m.iterrows():
                    s1, s2, _, _, det = calculate_match_details(m)
                    if s1+s2 > 0: st.write(f"🔹 {m['Gospodarz']} **{s1}:{s2}** {m['Gość']} _({det})_")
        st.divider()

with tab2:
    st.header("🏁 Drabinki Pucharowe")
    for g in get_group_labels():
        with st.expander(f"Zestawienie: {st.session_state.group_names[g]}"):
            sub1, sub2 = get_sorted_subgroup(g, 1), get_sorted_subgroup(g, 2)
            t1_1, t1_2, t1_3 = sub1.iloc[0]['Drużyna'], sub1.iloc[1]['Drużyna'], sub1.iloc[2]['Drużyna']
            t2_1, t2_2, t2_3 = sub2.iloc[0]['Drużyna'], sub2.iloc[1]['Drużyna'], sub2.iloc[2]['Drużyna']
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ⚔️ Półfinały")
                w1 = st.selectbox(f"Zwycięzca PF1: {t1_1} vs {t2_2}", ["-", t1_1, t2_2], key=f"w1_{g}")
                w2 = st.selectbox(f"Zwycięzca PF2: {t2_1} vs {t1_2}", ["-", t2_1, t1_2], key=f"w2_{g}")
            
            with c2:
                st.markdown("#### 🏆 Finały")
                st.write(f"**O 5 MIEJSCE:** {t1_3} vs {t2_3}")
                st.write(f"**FINAŁ GRUPY:** {w1} vs {w2}")
                st.text_input("Wynik Finału (tekstowo)", key=f"f_res_{g}")

with tab3:
    st.subheader("Ustawienia Grup i Drużyn")
    sel_g = st.selectbox("Wybierz grupę do edycji:", get_group_labels())
    
    # Zmiana nazwy grupy
    new_group_name = st.text_input("Nazwa grupy (np. Grupa Młodziczek):", st.session_state.group_names[sel_g])
    st.session_state.group_names[sel_g] = new_group_name
    
    # Edycja drużyn
    st.write("Edytuj nazwy drużyn w tabeli poniżej (zespoły 1-3 to Podgrupa 1, 4-6 to Podgrupa 2):")
    edited_df = st.data_editor(st.session_state.groups[sel_g], hide_index=True, use_container_width=True)
    st.session_state.groups[sel_g] = edited_df

    st.divider()
    st.subheader("Wpisz wynik meczu grupowego")
    with st.form("m_form"):
        teams_list = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        d1 = c1.selectbox("Gospodarz", teams_list)
        d2 = c2.selectbox("Gość", [t for t in teams_list if t != d1])
        p_cols = st.columns(5)
        pts = []
        for j in range(5):
            with p_cols[j]:
                pts.extend([st.number_input(f"S{j+1}-G",0,45,0,key=f"p1{j}{sel_g}"), st.number_input(f"S{j+1}-H",0,45,0,key=f"p2{j}{sel_g}")])
        if st.form_submit_button("Zapisz Mecz"):
            st.session_state.matches.loc[len(st.session_state.matches)] = [sel_g, d1, d2] + pts
            st.rerun()

    if st.button("🔴 RESET WSZYSTKIEGO"):
        st.session_state.clear()
        st.rerun()
