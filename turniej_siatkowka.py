import streamlit as st
import pandas as pd

# --- KONFIGURACJA ---
st.set_page_config(
    page_title="MP Juniorów - Wyniki Live",
    page_icon="🏐",
    layout="wide"
)

# --- FUNKCJE ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # A-H

def calculate_points(row):
    """Punkty: 3:0/3:1 -> 3 pkt, 3:2 -> 2 pkt, 2:3 -> 1 pkt"""
    if row['Wygrane'] == 3 and row['Przegrane'] <= 1:
        return 3
    elif row['Wygrane'] == 3 and row['Przegrane'] == 2:
        return 2
    elif row['Wygrane'] == 2 and row['Przegrane'] == 3:
        return 1
    return 0

def sort_group_by_subgroups(df):
    """Sortuje każdą podgrupę osobno i łączy je"""
    df['Punkty'] = df.apply(calculate_points, axis=1)
    df['Stosunek'] = df.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    
    # Sortujemy wewnątrz podgrup
    sub1 = df[df['Podgrupa'] == 1].sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    sub2 = df[df['Podgrupa'] == 2].sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    
    # Dodajemy pozycję wewnątrz podgrupy (1, 2, 3)
    sub1['Poz_w_podgrupie'] = range(1, 4)
    sub2['Poz_w_podgrupie'] = range(1, 4)
    
    return pd.concat([sub1, sub2]).reset_index(drop=True)

def style_subgroups(styler):
    """
    Koloruje komórki na podstawie pozycji Wewnątrz podgrupy.
    """
    def apply_color(row):
        # Miejsca 1-2 w podgrupie na niebiesko, 3 na pomarańczowo
        color = '#a8c4e2' if row['Poz_w_podgrupie'] <= 2 else '#f7c27b'
        return [f'background-color: {color}' if col in ['Poz_w_podgrupie', 'Drużyna'] else '' for col in row.index]

    return styler.apply(apply_color, axis=1)

# --- INICJALIZACJA DANYCH ---
group_labels = get_group_labels()

if 'groups' not in st.session_state:
    st.session_state.groups = {}
    for g in group_labels:
        # Tworzymy 8 grup, każda ma 2 podgrupy po 3 zespoły
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

# --- INTERFEJS ---
st.title("🏐 Mistrzostwa Polski Juniorów - Siatkówka")
st.info("System: 8 grup głównych. Każda grupa posiada 2 podgrupy. Miejsca 1-2 (Awans) są niebieskie, miejsce 3 jest pomarańczowe.")

tab1, tab2 = st.tabs(["📊 Tabele Grup", "✏️ Edycja Wyników"])

with tab1:
    # Wyświetlamy po 2 grupy w rzędzie dla lepszej czytelności
    for i in range(0, len(group_labels), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(group_labels):
                g = group_labels[i + j]
                with cols[j]:
                    st.subheader(f"Grupa {g}")
                    df_sorted = sort_group_by_subgroups(st.session_state.groups[g])
                    
                    # Stylizacja
                    styled_df = df_sorted.style.pipe(style_subgroups)
                    
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        column_order=("Podgrupa", "Poz_w_podgrupie", "Drużyna", "Mecze", "Wygrane", "Przegrane", "Sety+", "Sety-", "Punkty")
                    )

with tab2:
    st.subheader("✏️ Panel Administratora")
    selected_g = st.selectbox("Wybierz grupę do edycji:", group_labels)
    
    # Edytor danych
    edited_df = st.data_editor(
        st.session_state.groups[selected_g],
        num_rows="fixed",
        use_container_width=True
    )
    
    if st.button(f"💾 Zapisz zmiany dla Grupy {selected_g}"):
        st.session_state.groups[selected_g] = edited_df
        st.success(f"Zapisano wyniki dla Grupy {selected_g}!")
        st.rerun()
