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

def sort_group_by_subgroups(df):
    """Sortuje każdą podgrupę (1 i 2) osobno wewnątrz jednej grupy"""
    temp_df = df.copy()
    temp_df['Punkty'] = temp_df.apply(calculate_points, axis=1)
    
    # Obliczanie stosunku setów (unikamy dzielenia przez zero)
    temp_df['Stosunek'] = temp_df.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    
    # Rozdzielenie na podgrupy i sortowanie
    sub1 = temp_df[temp_df['Podgrupa'] == 1].sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    sub2 = temp_df[temp_df['Podgrupa'] == 2].sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    
    # Dodanie pozycji wewnątrz podgrupy (1, 2, 3)
    sub1['Poz_Podgrupa'] = range(1, 4)
    sub2['Poz_Podgrupa'] = range(1, 4)
    
    return pd.concat([sub1, sub2]).reset_index(drop=True)

def style_table(styler):
    """Funkcja kolorująca: Top 2 -> Niebieski, 3 -> Pomarańczowy"""
    def apply_row_style(row):
        # Definicja kolorów
        blue = 'background-color: #a8c4e2; color: black;'
        orange = 'background-color: #f7c27b; color: black;'
        
        # Wybór koloru na podstawie pozycji w podgrupie
        style = blue if row['Poz_Podgrupa'] <= 2 else orange
        
        # Kolorujemy tylko wybrane kolumny dla czytelności
        styles = []
        for col in row.index:
            if col in ['Poz_Podgrupa', 'Drużyna', 'Podgrupa']:
                styles.append(style)
            else:
                styles.append('')
        return styles

    return styler.apply(apply_row_style, axis=1)

# --- INICJALIZACJA DANYCH (ZABEZPIECZENIE PRZED BŁĘDEM KEYERROR) ---
group_labels = get_group_labels()

# Resetujemy session_state jeśli brakuje nowej kolumny 'Podgrupa'
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
st.title("🏐 Mistrzostwa Polski Juniorów")
st.markdown("""
**Zasady kolorowania:**
- 🟦 Miejsca 1 i 2 w podgrupie (Awans)
- 🟧 Miejsce 3 w podgrupie
""")

tab1, tab2 = st.tabs(["📊 Tabele Wyników", "✏️ Panel Administratora (Edycja)"])

with tab1:
    # Wyświetlanie grup w dwóch kolumnach
    for i in range(0, len(group_labels), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(group_labels):
                g = group_labels[i + j]
                with cols[j]:
                    st.subheader(f"Grupa {g}")
                    df_sorted = sort_group_by_subgroups(st.session_state.groups[g])
                    
                    # Aplikacja stylów
                    styled_df = df_sorted.style.pipe(style_table)
                    
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Poz_Podgrupa": "Miejsce",
                            "Podgrupa": "Podgr."
                        }
                    )

with tab2:
    st.info("Tutaj wpisz aktualne wyniki (liczba wygranych/przegranych meczów oraz setów).")
    selected_g = st.selectbox("Wybierz grupę do edycji:", group_labels)
    
    # Edytor danych w czasie rzeczywistym
    edited_df = st.data_editor(
        st.session_state.groups[selected_g],
        num_rows="fixed",
        use_container_width=True
    )
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button(f"💾 Zapisz Grupę {selected_g}"):
            st.session_state.groups[selected_g] = edited_df
            st.success("Dane zapisane!")
            st.rerun()
    with col_btn2:
        if st.button("🔄 Resetuj wszystkie dane (UWAGA)"):
            st.session_state.clear()
            st.rerun()

st.divider()
st.caption("System obsługi turnieju | 2026")
