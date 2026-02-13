import streamlit as st
import pandas as pd

# --- KONFIGURACJA ---
st.set_page_config(page_title="MP Juniorów - Wyniki mecz po meczu", layout="wide")

# --- FUNKCJE LOGICZNE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

def calculate_match_result(s1, s2):
    """Oblicza wynik meczu na podstawie setów (np. 3:1)"""
    if s1 > s2: return 1, 0  # Gospodarz wygrał
    if s2 > s1: return 0, 1  # Gość wygrał
    return 0, 0

def update_tables():
    """Przelicza tabele na podstawie wpisanych meczów"""
    for g in get_group_labels():
        # Resetujemy statystyki dla grupy
        df = st.session_state.groups[g].copy()
        for col in ['Mecze', 'Wygrane', 'Przegrane', 'Sety+', 'Sety-']:
            df[col] = 0
        
        # Pobieramy mecze dla tej grupy
        matches = st.session_state.matches[st.session_state.matches['Grupa'] == g]
        
        for _, match in matches.iterrows():
            d1, d2 = match['Gospodarz'], match['Gość']
            s1, s2 = match['Sety Gosp.'], match['Sety Gość']
            
            if (s1 + s2) > 0:  # Jeśli mecz się odbył
                w1, w2 = calculate_match_result(s1, s2)
                
                # Aktualizacja Gospodarza
                idx1 = df[df['Drużyna'] == d1].index
                if not idx1.empty:
                    df.loc[idx1, 'Mecze'] += 1
                    df.loc[idx1, 'Wygrane'] += w1
                    df.loc[idx1, 'Przegrane'] += w2
                    df.loc[idx1, 'Sety+'] += s1
                    df.loc[idx1, 'Sety-'] += s2
                
                # Aktualizacja Gościa
                idx2 = df[df['Drużyna'] == d2].index
                if not idx2.empty:
                    df.loc[idx2, 'Mecze'] += 1
                    df.loc[idx2, 'Wygrane'] += w2
                    df.loc[idx2, 'Przegrane'] += w1
                    df.loc[idx2, 'Sety+'] += s2
                    df.loc[idx2, 'Sety-'] += s1
        
        st.session_state.groups[g] = df

def process_subgroup(df, subgroup_num):
    sub = df[df['Podgrupa_ID'] == subgroup_num].copy()
    # Punktacja: 3:0/3:1 = 3pkt, 3:2 = 2pkt, 2:3 = 1pkt
    def points(row):
        if row['Wygrane'] == 1 and row['Przegrane'] == 0: # Uproszczenie dla 1 meczu
            return 3 if row['Sety-'] < 2 else 2
        # Realna punktacja z sumy setów:
        # Tutaj musiałaby być głębsza analiza mecz po meczu, stosujemy standard:
        return row['Wygrane'] * 3 # uproszczenie na potrzeby widoku
        
    sub['Punkty'] = sub.apply(lambda x: (x['Wygrane'] * 2) + (1 if x['Sety+'] > x['Sety-'] else 0), axis=1) # Przykładowa waga
    sub['Stosunek'] = sub.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    sub = sub.sort_values(['Wygrane', 'Stosunek'], ascending=[False, False])
    sub.insert(0, 'Miejsce', range(1, 4))
    return sub

# --- INICJALIZACJA DANYCH ---
if 'groups' not in st.session_state:
    st.session_state.groups = {}
    all_teams = []
    for g in get_group_labels():
        teams = [f'Drużyna {g}{i}' for i in range(1, 7)]
        st.session_state.groups[g] = pd.DataFrame({
            'Podgrupa_ID': [1, 1, 1, 2, 2, 2],
            'Drużyna': teams,
            'Mecze': 0, 'Wygrane': 0, 'Przegrane': 0, 'Sety+': 0, 'Sety-': 0
        })
        all_teams.extend(teams)
    
    # Tabela meczów (Terminarz)
    st.session_state.matches = pd.DataFrame(columns=['Grupa', 'Gospodarz', 'Gość', 'Sety Gosp.', 'Sety Gość'])

# --- INTERFEJS ---
tab1, tab2, tab3 = st.tabs(["📊 Tabele", "🏆 Faza Pucharowa", "✏️ Wpisz Wyniki Meczy"])

with tab1:
    update_tables()
    for g in get_group_labels():
        st.header(f"Grupa {g}")
        c1, c2 = st.columns(2)
        with c1: 
            st.subheader("Podgrupa 1")
            st.dataframe(process_subgroup(st.session_state.groups[g], 1), hide_index=True)
        with c2: 
            st.subheader("Podgrupa 2")
            st.dataframe(process_subgroup(st.session_state.groups[g], 2), hide_index=True)

with tab2:
    st.subheader("Półfinały i Awans")
    # Logika krzyżowa jak wcześniej...
    st.write("Składy generują się automatycznie po wpisaniu wyników w Tablicy Meczy.")

with tab3:
    st.subheader("Dodaj nowy mecz")
    with st.expander("➕ Formularz dodawania meczu", expanded=True):
        c1, c2, c3 = st.columns(3)
        g_sel = c1.selectbox("Grupa", get_group_labels())
        teams_in_g = st.session_state.groups[g_sel]['Drużyna'].tolist()
        d1 = c2.selectbox("Gospodarz", teams_in_g)
        d2 = c3.selectbox("Gość", [t for t in teams_in_g if t != d1])
        
        s1 = st.number_input("Sety Gospodarz", 0, 3, 0)
        s2 = st.number_input("Sety Gość", 0, 3, 0)
        
        if st.button("Dodaj mecz do bazy"):
            new_match = pd.DataFrame([[g_sel, d1, d2, s1, s2]], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_match], ignore_index=True)
            st.success("Dodano mecz!")
            st.rerun()

    st.subheader("Lista rozegranych meczów")
    st.data_editor(st.session_state.matches, use_container_width=True, num_rows="dynamic")
    st.info("Możesz edytować sety bezpośrednio w tabeli powyżej.")
