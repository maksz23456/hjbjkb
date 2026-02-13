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
    """Punkty: 3:0/3:1 -> 3 pkt, 3:2 -> 2 pkt zwycięzca, 1 pkt przegrany"""
    if row['Wygrane'] == 3 and row['Przegrane'] <= 1:
        return 3
    elif row['Wygrane'] == 3 and row['Przegrane'] == 2:
        return 2
    elif row['Wygrane'] == 2 and row['Przegrane'] == 3:
        return 1
    return 0

def sort_group(df):
    temp_df = df.copy()
    temp_df['Punkty'] = df.apply(calculate_points, axis=1)
    temp_df['Stosunek'] = df.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    temp_df = temp_df.sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    return temp_df.reset_index(drop=True)

def style_top3(df):
    """
    Kolorowanie wierszy:
    1 i 2 miejsce → niebieski, pasek niebieski obok nazwy
    3 miejsce → pomarańczowy, pasek pomarańczowy obok nazwy
    """
    colors = ['#a8c4e2', '#a8c4e2', '#f7c27b']  # top1/top2 niebieski, top3 pomarańcz
    bars = ['linear-gradient(90deg, #2196f3 15%, transparent 15%)',
            'linear-gradient(90deg, #2196f3 15%, transparent 15%)',
            'linear-gradient(90deg, #ff9800 15%, transparent 15%)']

    styler = df.style
    for i in range(len(df)):
        if i < 3:
            styler = styler.set_properties(subset=['Drużyna'], **{
                'background': bars[i],
                'padding-left': '5px'
            }).set_properties(subset=df.columns, **{
                'background-color': colors[i]
            })
    return styler

# --- INICJALIZACJA DANYCH ---
group_labels = get_group_labels()

if 'groups' not in st.session_state:
    st.session_state.groups = {}
    for g in group_labels:
        # 2 podgrupy po 3 zespoły = 6 zespołów
        st.session_state.groups[g] = pd.DataFrame({
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
st.markdown("8 grup, każda podzielona na 2 podgrupy po 3 zespoły. "
            "System punktowy: 3:0/3:1 → 3 pkt, 3:2 → 2/1 pkt.")

# --- TABY ---
tab1, tab2, tab3 = st.tabs(["📊 Wszystkie Grupy", "✏️ Edycja Ręczna", "🏆 Drabinka"])

# TAB1 – wyświetlanie grup
with tab1:
    for row in range(0, 8, 2):
        col1, col2 = st.columns(2)
        for i, col in enumerate([col1, col2]):
            current_g = group_labels[row + i]
            with col:
                st.markdown(f"### Grupa {current_g}")
                df_sorted = sort_group(st.session_state.groups[current_g])
                df_display = df_sorted.copy()
                df_display.insert(0, 'Poz', range(1, len(df_display)+1))
                st.dataframe(
                    style_top3(df_display),
                    hide_index=True,
                    use_container_width=True
                )

# TAB2 – edycja ręczna
with tab2:
    st.markdown("### ✏️ Panel Administratora")
    selected_g = st.selectbox("Wybierz grupę do edycji:", group_labels)
    edited_df = st.data_editor(
        st.session_state.groups[selected_g],
        num_rows="fixed",
        use_container_width=True
    )
    if st.button(f"💾 Zapisz zmiany dla Grupy {selected_g}"):
        st.session_state.groups[selected_g] = edited_df
        st.toast("Zmiany zapisane!")

# TAB3 – symulacja drabinki
with tab3:
    st.markdown("### 🏆 Symulacja Fazy Pucharowej")
    st.info("Top 2 z każdej grupy do drabinki pucharowej.")
    leaders = {g: sort_group(st.session_state.groups[g]).iloc[0]['Drużyna'] for g in group_labels}
    runners_up = {g: sort_group(st.session_state.groups[g]).iloc[1]['Drużyna'] for g in group_labels}

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.code(f"{leaders['A']} vs {runners_up['B']}")
    with c2: st.code(f"{leaders['C']} vs {runners_up['D']}")
    with c3: st.code(f"{leaders['E']} vs {runners_up['F']}")
    with c4: st.code(f"{leaders['G']} vs {runners_up['H']}")

st.divider()
st.caption("Mistrzostwa Polski Juniorów 2026 | Dane wprowadzane ręcznie")
