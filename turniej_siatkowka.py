import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="MP Juniorów - Wyniki Live",
    page_icon="🏐",
    layout="wide"
)

# --- FUNKCJE LOGICZNE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # Grupy A-H

def calculate_points(row):
    """System punktowy: 3:0/3:1 -> 3 pkt, 3:2 -> 2 pkt, 2:3 -> 1 pkt, reszta 0"""
    if row['Wygrane'] == 3 and row['Przegrane'] <= 1:
        return 3
    elif row['Wygrane'] == 3 and row['Przegrane'] == 2:
        return 2
    elif row['Wygrane'] == 2 and row['Przegrane'] == 3:
        return 1
    return 0

def process_subgroup(df, subgroup_num):
    """Przygotowuje, punktuje i sortuje konkretną podgrupę do wyświetlenia"""
    # Filtrowanie danych dla konkretnej podgrupy
    sub = df[df['Podgrupa'] == subgroup_num].copy()
    
    # Obliczenia
    sub['Punkty'] = sub.apply(calculate_points, axis=1)
    sub['Stosunek'] = sub.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    
    # Sortowanie: 1. Punkty, 2. Stosunek setów
    sub = sub.sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    
    # Dodanie kolumny z miejscem (1, 2, 3)
    sub.insert(0, 'Miejsce', range(1, 4))
    return sub

def style_subgroup_table(styler):
    """Kolorowanie komórek: Top 2 -> Niebieski, 3 -> Pomarańczowy"""
    def apply_style(row):
        blue = 'background-color: #a8c4e2; color: black; font-weight: bold;'
        orange = 'background-color: #f7c27b; color: black; font-weight: bold;'
        
        # Wybór koloru na podstawie wyliczonego miejsca
        color = blue if row['Miejsce'] <= 2 else orange
        
        # Nakładamy kolor na kolumny 'Miejsce' oraz 'Drużyna'
        return [color if col in ['Miejsce', 'Drużyna'] else '' for col in row.index]

    return styler.apply(apply_style, axis=1)

# --- INICJALIZACJA DANYCH ---
group_labels = get_group_labels()

# Automatyczna naprawa struktury danych w razie zmian w kodzie
if 'groups' not in st.session_state or 'Podgrupa' not in st.session_state.groups['A'].columns:
    st.session_state.groups = {}
    for g in group_labels:
        st.session_state.groups[g] = pd.DataFrame({
            'Podgrupa': [1, 1, 1, 2, 2, 2],
            'Drużyna': [f'{g}1 Team', f'{g}2 Team', f'{g}3 Team',
                        f'{g}4 Team', f'{g}5 Team', f'{g}6 Team'],
            'Mecze': [0]*6,
            'Wygrane': [0]*6,
            'Przegrane': [0]*6,
            'Sety+': [0]*6,
            'Sety-': [0]*6
        })

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🏐 MP Juniorów - System Wyników")
st.markdown("---")

tab1, tab2 = st.tabs(["📊 Tabele Wyników", "✏️ Panel Administratora"])

with tab1:
    for g in group_labels:
        with st.container():
            st.subheader(f"🏆 GRUPA {g}")
            col1, col2 = st.columns(2)
            
            # Wyświetlanie Podgrupy 1
            with col1:
                st.caption(f"Podgrupa {g}1")
                df_sub1 = process_subgroup(st.session_state.groups[g], 1)
                st.dataframe(
                    df_sub1.style.pipe(style_subgroup_table),
                    hide_index=True,
                    use_container_width=True,
                    column_order=("Miejsce", "Drużyna", "Mecze", "Wygrane", "Przegrane", "Sety+", "Sety-", "Punkty")
                )
            
            # Wyświetlanie Podgrupy 2
            with col2:
                st.caption(f"Podgrupa {g}2")
                df_sub2 = process_subgroup(st.session_state.groups[g], 2)
                st.dataframe(
                    df_sub2.style.pipe(style_subgroup_table),
                    hide_index=True,
                    use_container_width=True,
                    column_order=("Miejsce", "Drużyna", "Mecze", "Wygrane", "Przegrane", "Sety+", "Sety-", "Punkty")
                )
            st.markdown("<br>", unsafe_allow_html=True) # Odstęp między grupami głównymi

with tab2:
    st.info("Wprowadź wyniki poniżej. Tabele w zakładce obok zaktualizują się i posortują automatycznie.")
    selected_g = st.selectbox("Wybierz grupę główną do edycji:", group_labels)
    
    # Edytor całej grupy głównej (6 zespołów)
    edited_df = st.data_editor(
        st.session_state.groups[selected_g],
        num_rows="fixed",
        use_container_width=True,
        hide_index=True
    )
    
    col_save, col_reset = st.columns([1, 4])
    with col_save:
        if st.button(f"💾 Zapisz Grupę {selected_g}"):
            st.session_state.groups[selected_g] = edited_df
            st.success("Dane zapisane pomyślnie!")
            st.rerun()
            
    with col_reset:
        if st.button("🔄 Resetuj wszystkie tabele do zera"):
            st.session_state.clear()
            st.rerun()

st.divider()
st.caption("Faza Grupowa Mistrzostw Polski Juniorów | Podział na podgrupy 1-2")
