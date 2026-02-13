import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="MP Juniorów - System Wyników", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # A-H

def calculate_points_from_score(s1, s2):
    """Zwraca punkty dla (Gospodarza, Gościa) na podstawie wyniku w setach"""
    if s1 == 3 and (s2 == 0 or s2 == 1): return 3, 0
    if s1 == 3 and s2 == 2: return 2, 1
    if s2 == 3 and s1 == 2: return 1, 2
    if s2 == 3 and (s1 == 0 or s1 == 1): return 0, 3
    return 0, 0

def update_tables():
    """Przelicza statystyki w grupach na podstawie wpisanych meczów"""
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        # Zerujemy statystyki przed ponownym przeliczeniem
        for col in ['Mecze', 'Wygrane', 'Przegrane', 'Sety+', 'Sety-', 'Punkty']:
            df[col] = 0
        
        # Filtrujemy mecze dla danej grupy
        m_list = st.session_state.matches
        group_matches = m_list[m_list['Grupa'] == g]
        
        for _, match in group_matches.iterrows():
            d1, d2 = match['Gospodarz'], match['Gość']
            s1, s2 = int(match['S1']), int(match['S2'])
            
            if (s1 == 3 or s2 == 3):  # Liczymy tylko zakończone mecze
                p1, p2 = calculate_points_from_score(s1, s2)
                
                # Statystyki Gospodarza
                idx1 = df[df['Drużyna'] == d1].index
                if not idx1.empty:
                    df.loc[idx1, 'Mecze'] += 1
                    df.loc[idx1, 'Wygrane'] += (1 if s1 > s2 else 0)
                    df.loc[idx1, 'Przegrane'] += (1 if s2 > s1 else 0)
                    df.loc[idx1, 'Sety+'] += s1
                    df.loc[idx1, 'Sety-'] += s2
                    df.loc[idx1, 'Punkty'] += p1
                
                # Statystyki Gościa
                idx2 = df[df['Drużyna'] == d2].index
                if not idx2.empty:
                    df.loc[idx2, 'Mecze'] += 1
                    df.loc[idx2, 'Wygrane'] += (1 if s2 > s1 else 0)
                    df.loc[idx2, 'Przegrane'] += (1 if s1 > s2 else 0)
                    df.loc[idx2, 'Sety+'] += s2
                    df.loc[idx2, 'Sety-'] += s1
                    df.loc[idx2, 'Punkty'] += p2
        
        st.session_state.groups[g] = df

# --- INICJALIZACJA DANYCH (ZABEZPIECZENIE) ---
if 'matches' not in st.session_state or 'groups' not in st.session_state:
    st.session_state.groups = {}
    for g in get_group_labels():
        st.session_state.groups[g] = pd.DataFrame({
            'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
            'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
            'Mecze': 0, 'Wygrane': 0, 'Przegrane': 0, 'Sety+': 0, 'Sety-': 0, 'Punkty': 0
        })
    st.session_state.matches = pd.DataFrame(columns=['Grupa', 'Gospodarz', 'Gość', 'S1', 'S2'])

# --- STYLE ---
def style_table(styler):
    def apply_row_color(row):
        blue = 'background-color: #a8c4e2; color: black;'
        orange = 'background-color: #f7c27b; color: black;'
        return [blue if row['Miejsce'] <= 2 else orange for _ in row.index]
    return styler.apply(apply_row_color, axis=1)

# --- INTERFEJS ---
st.title("🏐 MP Juniorów - System Wyników")
update_tables()

tab1, tab2, tab3 = st.tabs(["📊 Tabele", "🏆 Faza Pucharowa", "✏️ Wpisz Wynik Meczu"])

with tab1:
    for g in get_group_labels():
        st.subheader(f"GRUPA {g}")
        c1, c2 = st.columns(2)
        for i, col in enumerate([c1, c2]):
            sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == (i+1)].copy()
            sub['Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0, 1)
            sub = sub.sort_values(['Punkty', 'Ratio'], ascending=False)
            sub.insert(0, 'Miejsce', range(1, 4))
            col.write(f"**Podgrupa {i+1}**")
            col.dataframe(sub.style.pipe(style_table), hide_index=True, use_container_width=True)
        st.divider()

with tab2:
    st.info("Zwycięzcy półfinałów awansują do 1/2 MP!")
    for g in get_group_labels():
        with st.expander(f"Drabinka Grupy {g}"):
            # Sortowanie podgrup do drabinki
            s1 = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == 1].copy()
            s1 = s1.sort_values(['Punkty', 'Wygrane'], ascending=False)
            s2 = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID'] == 2].copy()
            s2 = s2.sort_values(['Punkty', 'Wygrane'], ascending=False)
            
            t1_1, t1_2, t1_3 = s1.iloc[0]['Drużyna'], s1.iloc[1]['Drużyna'], s1.iloc[2]['Drużyna']
            t2_1, t2_2, t2_3 = s2.iloc[0]['Drużyna'], s2.iloc[1]['Drużyna'], s2.iloc[2]['Drużyna']
            
            cc1, cc2 = st.columns(2)
            cc1.error(f"PF1: {t1_1} vs {t2_2}")
            cc1.error(f"PF2: {t2_1} vs {t1_2}")
            cc2.warning(f"O 5. miejsce: {t1_3} vs {t2_3}")
            cc2.success("Finał: Zwycięzcy PF1 i PF2 (AWANS)")

with tab3:
    st.subheader("Dodaj wynik meczu")
    c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 2])
    g_sel = c1.selectbox("Grupa", get_group_labels())
    teams = st.session_state.groups[g_sel]['Drużyna'].tolist()
    d1 = c2.selectbox("Gospodarz", teams, key="d1")
    s1 = c3.number_input("Sety Gosp.", 0, 3, 0)
    s2 = c4.number_input("Sety Gość", 0, 3, 0)
    d2 = c5.selectbox("Gość", [t for t in teams if t != d1], key="d2")
    
    if st.button("Zatwierdź mecz"):
        new_m = pd.DataFrame([[g_sel, d1, d2, s1, s2]], columns=['Grupa', 'Gospodarz', 'Gość', 'S1', 'S2'])
        st.session_state.matches = pd.concat([st.session_state.matches, new_m], ignore_index=True)
        st.rerun()

    st.subheader("Lista rozegranych meczów (możesz tu edytować)")
    st.session_state.matches = st.data_editor(st.session_state.matches, num_rows="dynamic", use_container_width=True)
    if st.button("Wyczyść wszystkie dane"):
        st.session_state.clear()
        st.rerun()
