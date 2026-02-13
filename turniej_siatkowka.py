import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(
    page_title="Mistrzostwa Polski Juniorów - Siatkówka",
    page_icon="🏐",
    layout="wide"
)

# Inicjalizacja session state
if 'groups' not in st.session_state:
    st.session_state.groups = {
        'A': pd.DataFrame({
            'Drużyna': ['Drużyna A1', 'Drużyna A2', 'Drużyna A3', 'Drużyna A4'],
            'Mecze': [0, 0, 0, 0],
            'Wygrane': [0, 0, 0, 0],
            'Przegrane': [0, 0, 0, 0],
            'Sety+': [0, 0, 0, 0],
            'Sety-': [0, 0, 0, 0],
            'Punkty': [0, 0, 0, 0]
        }),
        'B': pd.DataFrame({
            'Drużyna': ['Drużyna B1', 'Drużyna B2', 'Drużyna B3', 'Drużyna B4'],
            'Mecze': [0, 0, 0, 0],
            'Wygrane': [0, 0, 0, 0],
            'Przegrane': [0, 0, 0, 0],
            'Sety+': [0, 0, 0, 0],
            'Sety-': [0, 0, 0, 0],
            'Punkty': [0, 0, 0, 0]
        })
    }

def calculate_points(row):
    """Oblicza punkty: 3 za wygraną, 0 za przegraną"""
    return row['Wygrane'] * 3

def sort_group(df):
    """Sortuje grupę według punktów, potem stosunku setów"""
    df['Punkty'] = df.apply(calculate_points, axis=1)
    df['Stosunek'] = df.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    df = df.sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    df = df.reset_index(drop=True)
    return df

def get_position_color(pos):
    """Zwraca kolor tła dla pozycji w tabeli"""
    if pos == 0:
        return 'background-color: #d4edda'  # zielony dla 1. miejsca
    elif pos == 1:
        return 'background-color: #d1ecf1'  # niebieski dla 2. miejsca
    else:
        return ''

# Nagłówek
st.title("🏐 Mistrzostwa Polski Juniorów - Siatkówka")
st.subheader("Faza grupowa - System playoff")

# Tabs dla różnych sekcji
tab1, tab2, tab3 = st.tabs(["📊 Tabele grup", "✏️ Edycja wyników", "🏆 Faza pucharowa"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔵 Grupa A")
        df_a = sort_group(st.session_state.groups['A'].copy())
        
        # Dodaj pozycje
        df_a.insert(0, 'Poz', range(1, len(df_a) + 1))
        
        # Wyświetl tabelę z kolorami
        st.dataframe(
            df_a.style.apply(lambda x: [get_position_color(i) for i in range(len(x))], axis=0),
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("🥇 1. miejsce → Półfinał  \n🥈 2. miejsce → Półfinał")
    
    with col2:
        st.markdown("### 🟢 Grupa B")
        df_b = sort_group(st.session_state.groups['B'].copy())
        
        # Dodaj pozycje
        df_b.insert(0, 'Poz', range(1, len(df_b) + 1))
        
        st.dataframe(
            df_b.style.apply(lambda x: [get_position_color(i) for i in range(len(x))], axis=0),
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("🥇 1. miejsce → Półfinał  \n🥈 2. miejsce → Półfinał")

with tab2:
    st.markdown("### ✏️ Edytuj wyniki drużyn")
    
    group_choice = st.selectbox("Wybierz grupę:", ["A", "B"])
    
    df_edit = st.session_state.groups[group_choice].copy()
    team_choice = st.selectbox("Wybierz drużynę:", df_edit['Drużyna'].tolist())
    
    team_idx = df_edit[df_edit['Drużyna'] == team_choice].index[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_name = st.text_input("Nazwa drużyny:", value=team_choice)
        matches = st.number_input("Liczba meczów:", min_value=0, value=int(df_edit.loc[team_idx, 'Mecze']), step=1)
        wins = st.number_input("Wygrane:", min_value=0, max_value=matches, value=int(df_edit.loc[team_idx, 'Wygrane']), step=1)
    
    with col2:
        losses = st.number_input("Przegrane:", min_value=0, max_value=matches, value=int(df_edit.loc[team_idx, 'Przegrane']), step=1)
        sets_won = st.number_input("Sety wygrane:", min_value=0, value=int(df_edit.loc[team_idx, 'Sety+']), step=1)
    
    with col3:
        sets_lost = st.number_input("Sety przegrane:", min_value=0, value=int(df_edit.loc[team_idx, 'Sety-']), step=1)
    
    if st.button("💾 Zapisz zmiany", type="primary"):
        st.session_state.groups[group_choice].loc[team_idx, 'Drużyna'] = new_name
        st.session_state.groups[group_choice].loc[team_idx, 'Mecze'] = matches
        st.session_state.groups[group_choice].loc[team_idx, 'Wygrane'] = wins
        st.session_state.groups[group_choice].loc[team_idx, 'Przegrane'] = losses
        st.session_state.groups[group_choice].loc[team_idx, 'Sety+'] = sets_won
        st.session_state.groups[group_choice].loc[team_idx, 'Sety-'] = sets_lost
        st.success(f"✅ Zapisano zmiany dla {new_name}!")
        st.rerun()

with tab3:
    st.markdown("### 🏆 Drabinka Playoff")
    
    # Posortuj grupy
    df_a_sorted = sort_group(st.session_state.groups['A'].copy())
    df_b_sorted = sort_group(st.session_state.groups['B'].copy())
    
    # Pobierz drużyny
    a1 = df_a_sorted.iloc[0]['Drużyna']
    a2 = df_a_sorted.iloc[1]['Drużyna']
    b1 = df_b_sorted.iloc[0]['Drużyna']
    b2 = df_b_sorted.iloc[1]['Drużyna']
    
    # Półfinały
    st.markdown("#### 🎯 Półfinały (system na skos)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Półfinał 1**
        
        🥇 {a1} (1. Grupa A)
        
        **VS**
        
        🥈 {b2} (2. Grupa B)
        """)
    
    with col2:
        st.info(f"""
        **Półfinał 2**
        
        🥇 {b1} (1. Grupa B)
        
        **VS**
        
        🥈 {a2} (2. Grupa A)
        """)
    
    # Finały
    st.markdown("#### 🏅 Dalsze mecze")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("""
        **🥇 FINAŁ**
        
        Zwycięzcy Półfinału 1 vs Półfinału 2
        """)
        
        st.warning("""
        **🥉 Mecz o 3. miejsce**
        
        Przegrani Półfinału 1 vs Półfinału 2
        """)
    
    with col2:
        if len(df_a_sorted) >= 3 and len(df_b_sorted) >= 3:
            a3 = df_a_sorted.iloc[2]['Drużyna']
            b3 = df_b_sorted.iloc[2]['Drużyna']
            st.info(f"""
            **📍 Mecz o 5. miejsce**
            
            {a3} (3. Grupa A)
            
            **VS**
            
            {b3} (3. Grupa B)
            """)
        
        if len(df_a_sorted) >= 4 and len(df_b_sorted) >= 4:
            a4 = df_a_sorted.iloc[3]['Drużyna']
            b4 = df_b_sorted.iloc[3]['Drużyna']
            st.info(f"""
            **📍 Mecz o 7. miejsce**
            
            {a4} (4. Grupa A)
            
            **VS**
            
            {b4} (4. Grupa B)
            """)
    
    # Legenda
    st.markdown("---")
    st.markdown("""
    ### 📋 System awansu:
    
    - ✅ **1. miejsca** z grup grają w półfinałach na skos (A1 vs B2, B1 vs A2)
    - ✅ **2. miejsca** z grup również awansują do półfinałów
    - 🏆 Zwycięzcy półfinałów grają w **FINALE**
    - 🥉 Przegrani półfinałów grają o **3. miejsce**
    - 📍 3. miejsca z grup grają o **5. miejsce**
    - 📍 4. miejsca z grup grają o **7. miejsce**
    """)

# Stopka
st.markdown("---")
st.markdown("*Aplikacja do zarządzania turniejem siatkarskim - Mistrzostwa Polski Juniorów* 🏐")
