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
st.title("🏐 Oficjalny Panel MP")
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
                
                # WYŚWIETLANIE LISTY MECZÓW POD TABELĄ
                teams_in_sub = sub['Drużyna'].tolist()
                sub_m = st.session_state.matches[(st.session_state.matches['Grupa'] == g) & (st.session_state.matches['Gospodarz'].isin(teams_in_sub))]
                for _, m in sub_m.iterrows():
                    s1, s2, _, _, det = calculate_match_details(m)
                    if s1+s2 > 0: st.write(f"🔹 {m['Gospodarz']} **{s1}:{s2}** {m['Gość']} _({det})_")
        st.divider()

with tab3:
    st.subheader("⚙️ Ustawienia")
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels(), key="sel_g_main")
    
    # Edycja nazw drużyn
    config = {"Drużyna": st.column_config.TextColumn("Nazwa Drużyny", width="extra-large")}
    edited_df = st.data_editor(st.session_state.groups[sel_g], column_config=config, hide_index=True, key=f"ed_{sel_g}")
    if st.button(f"Zapisz zmiany drużyn dla {sel_g}"):
        st.session_state.groups[sel_g] = edited_df
        st.rerun()

    st.divider()
    st.subheader("📝 Dodaj Nowy Mecz")
    
    # Formularz z unikalnym ID opartym na liczbie meczów (żeby się czyścił)
    form_id = f"match_form_{sel_g}_{len(st.session_state.matches)}"
    
    with st.form(key=form_id):
        teams = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c1, c2 = st.columns(2)
        d1 = c1.selectbox("Gospodarz", teams, key=f"h_{form_id}")
        d2 = c2.selectbox("Gość", [t for t in teams if t != d1], key=f"a_{form_id}")
        
        st.write("Punkty w setach (Tie-break do 15):")
        p_cols = st.columns(5)
        scores = []
        for j in range(5):
            with p_cols[j]:
                label = f"S{j+1}" if j < 4 else "S5"
                s_h = st.number_input(f"{label}-H", 0, 45, 0, key=f"sh_{j}_{form_id}")
                s_g = st.number_input(f"{label}-G", 0, 45, 0, key=f"sg_{j}_{form_id}")
                scores.extend([s_h, s_g])
        
        if st.form_submit_button("Zatwierdź wynik"):
            # Sprawdzenie wyniku (czy jest 3:X)
            s1_t, s2_t = 0, 0
            for i in range(0, 10, 2):
                if scores[i] > scores[i+1]: s1_t += 1
                elif scores[i+1] > scores[i]: s2_t += 1
            
            if s1_t == 3 or s2_t == 3:
                # Dodanie nowego wiersza bez nadpisywania
                new_match = pd.DataFrame([[sel_g, d1, d2] + scores], columns=st.session_state.matches.columns)
                st.session_state.matches = pd.concat([st.session_state.matches, new_match], ignore_index=True)
                st.success(f"Dodano mecz: {d1} {s1_t}:{s2_t} {d2}")
                st.rerun()
            else:
                st.error("Błąd: Jeden z zespołów musi wygrać 3 sety!")

    if st.button("🚨 CZYŚĆ WSZYSTKO"):
        st.session_state.clear()
        st.rerun()
