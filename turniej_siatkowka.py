import streamlit as st
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - Livescore", layout="wide")

# --- 2. INICJALIZACJA DANYCH ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

if 'group_names' not in st.session_state:
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

if 'groups' not in st.session_state:
    st.session_state.groups = {g: pd.DataFrame({
        'Podgrupa_ID': [1,1,1,2,2,2], 
        'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)], 
        'Mecze':0, 'Punkty':0, 'Wygrane':0, 'Sety+':0, 'Sety-':0, 'Pkt+':0, 'Pkt-':0
    }) for g in get_group_labels()}

if 'matches' not in st.session_state:
    st.session_state.matches = pd.DataFrame(columns=['Grupa', 'Gospodarz', 'Gość', 'S1_P1', 'S1_P2', 'S2_P1', 'S2_P2', 'S3_P1', 'S3_P2', 'S4_P1', 'S4_P2', 'S5_P1', 'S5_P2'])

# --- 3. FUNKCJE POMOCNICZE ---
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
                # Punktacja: 3:0/3:1 = 3pkt, 3:2 = 2pkt, 2:3 = 1pkt, 1:3/0:3 = 0pkt
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

def get_sorted_subgroup(gid, pid):
    temp = st.session_state.groups[gid][st.session_state.groups[gid]['Podgrupa_ID'] == pid].copy()
    temp['S_Ratio'] = temp['Sety+'] / temp['Sety-'].replace(0, 0.1)
    temp['P_Ratio'] = temp['Pkt+'] / temp['Pkt-'].replace(0, 0.1)
    return temp.sort_values(['Punkty', 'Wygrane', 'S_Ratio', 'P_Ratio'], ascending=False)

def style_row(row):
    color = '#a8c4e2' if row['Miejsce'] <= 2 else '#f7c27b'
    return [f'background-color: {color}; color: black; font-weight: bold' if col in ['Miejsce', 'Drużyna'] else '' for col in row.index]

# --- 4. INTERFEJS ---
st.title("🏐 Panel Wyników MP Juniorów")
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
                st.dataframe(sub_display.style.apply(style_row, axis=1), hide_index=True, use_container_width=True)
        st.divider()

with tab3:
    st.subheader("⚙️ Zarządzanie Drużynami")
    sel_g = st.selectbox("Wybierz grupę do edycji:", get_group_labels(), key="group_editor_select")
    
    # Zmiana nazwy grupy
    current_g_name = st.session_state.group_names[sel_g]
    new_g_name = st.text_input(f"Zmień nazwę dla Grupy {sel_g}:", value=current_g_name)
    if st.button(f"Zatwierdź nazwę grupy {sel_g}"):
        st.session_state.group_names[sel_g] = new_g_name
        st.rerun()

    st.divider()

    st.info("Wpisz nazwy drużyn. Kolumna 'Drużyna' jest teraz maksymalnie szeroka.")
    
    column_configuration = {
        "Drużyna": st.column_config.TextColumn("Pełna Nazwa Drużyny", width="extra-large", required=True),
        "Podgrupa_ID": st.column_config.NumberColumn("Podgrupa", disabled=True)
    }
    
    edited_df = st.data_editor(
        st.session_state.groups[sel_g],
        column_config=column_configuration,
        hide_index=True,
        use_container_width=True,
        height=260,
        key=f"editor_final_{sel_g}",
        disabled=("Mecze", "Punkty", "Wygrane", "Sety+", "Sety-", "Pkt+", "Pkt-")
    )

    if st.button(f"✅ ZAPISZ DRUŻYNY DLA GRUPY {sel_g}"):
        st.session_state.groups[sel_g] = edited_df
        st.rerun()

    st.divider()
    st.subheader("📝 Dodaj Wynik Meczu")
    with st.form(f"form_v4_{sel_g}"):
        current_teams = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        d1 = c1.selectbox("Gospodarz (H)", current_teams)
        d2 = c2.selectbox("Gość (G)", [t for t in current_teams if t != d1])
        
        st.write("**Wyniki w setach:**")
        p_cols = st.columns(5)
        scores = []
        for j in range(5):
            with p_cols[j]:
                label = f"S{j+1}" if j < 4 else "S5 (do 15)"
                # Ustawienie max_value na 45, aby pozwolić na grę na przewagi
                s_h = st.number_input(f"{label}-H", 0, 45, 0, key=f"v4_h_{j}_{sel_g}")
                s_g = st.number_input(f"{label}-G", 0, 45, 0, key=f"v4_g_{j}_{sel_g}")
                scores.extend([s_h, s_g])
                
        if st.form_submit_button("Dodaj Wynik Meczu"):
            # Obliczanie setów, żeby sprawdzić czy mecz się zakończył (3 wygrane)
            s_h_total = 0
            s_g_total = 0
            for i in range(0, 10, 2):
                if scores[i] > scores[i+1]: s_h_total += 1
                elif scores[i+1] > scores[i]: s_g_total += 1
            
            if s_h_total == 3 or s_g_total == 3:
                st.session_state.matches.loc[len(st.session_state.matches)] = [sel_g, d1, d2] + scores
                st.success(f"Mecz dodany! Wynik: {s_h_total}:{s_g_total}")
                st.rerun()
            else:
                st.error("Mecz musi zakończyć się wynikiem 3:X lub X:3 (wygrane 3 sety).")

    if st.button("🚨 TOTALNY RESET"):
        st.session_state.clear()
        st.rerun()
