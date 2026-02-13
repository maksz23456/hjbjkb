import streamlit as st
import pandas as pd
import requests

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="MP Juniorów - Wyniki Live",
    page_icon="🏐",
    layout="wide"
)

# --- FUNKCJE LOGICZNE ---
def get_group_labels():
    """Zwraca listę grup ['A', 'B', ..., 'H']"""
    return [chr(i) for i in range(65, 73)]

def fetch_live_data():
    """Pobiera dane tabelaryczne ze strony VolleyStation"""
    url = "https://juniorzymmp.volleystation.com/en/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(response.text)  # pandas odczyta wszystkie tabele z HTML
        return tables
    except Exception as e:
        st.error(f"Nie udało się pobrać danych automatycznie: {e}")
        return None

def calculate_points(row):
    """Zasady punktacji: 3 pkt za wygraną"""
    return row['Wygrane'] * 3

def sort_group(df):
    """Sortowanie grupy po punktach i stosunku setów"""
    temp_df = df.copy()
    temp_df['Punkty'] = temp_df.apply(calculate_points, axis=1)
    temp_df['Stosunek'] = temp_df.apply(lambda x: x['Sety+'] / max(x['Sety-'], 1), axis=1)
    temp_df = temp_df.sort_values(['Punkty', 'Stosunek'], ascending=[False, False])
    return temp_df.reset_index(drop=True)

def get_position_color(pos):
    """Kolorowanie pierwszych dwóch miejsc w tabeli"""
    if pos == 0: return 'background-color: #d4edda'  # Zielony
    if pos == 1: return 'background-color: #d1ecf1'  # Niebieski
    return ''

# --- INICJALIZACJA DANYCH ---
group_labels = get_group_labels()

if 'groups' not in st.session_state:
    st.session_state.groups = {}
    for g in group_labels:
        st.session_state.groups[g] = pd.DataFrame({
            'Drużyna': [f'Zespół {g}{i}' for i in range(1, 7)],
            'Mecze': [0]*6,
            'Wygrane': [0]*6,
            'Przegrane': [0]*6,
            'Sety+': [0]*6,
            'Sety-': [0]*6
        })

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🏐 Mistrzostwa Polski Juniorów - Siatkówka")
st.markdown("System obsługujący **8 grup po 6 zespołów** z aktualizacją live.")

# --- PASEK BOCZNY ---
with st.sidebar:
    st.header("Ustawienia Live")
    if st.button("🔄 Pobierz wyniki z VolleyStation", use_container_width=True):
        data = fetch_live_data()
        if data:
            for i, label in enumerate(group_labels):
                if i < len(data):
                    st.session_state.groups[label] = data[i].iloc[:6, :6]
            st.success("Zaktualizowano dane!")

# --- TABY ---
tab1, tab2, tab3 = st.tabs(["📊 Wszystkie Grupy (A-H)", "✏️ Edycja Ręczna", "🏆 Drabinka"])

# --- TAB 1: Wyświetlanie wszystkich grup ---
with tab1:
    for row in range(0, 8, 2):
        col1, col2 = st.columns(2)
        for i, col in enumerate([col1, col2]):
            current_g = group_labels[row + i]
            with col:
                st.markdown(f"### Grupa {current_g}")
                df_sorted = sort_group(st.session_state.groups[current_g])
                df_display = df_sorted.copy()
                df_display.insert(0, 'Poz', range(1, len(df_display) + 1))
                st.dataframe(
                    df_display.style.apply(
                        lambda x: [get_position_color(i) for i in range(len(x))],
                        axis=0,
                        subset=['Poz', 'Drużyna']
                    ),
                    hide_index=True,
                    use_container_width=True
                )

# --- TAB 2: Edycja ręczna ---
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

# --- TAB 3: Symulacja fazy pucharowej ---
with tab3:
    st.markdown("### 🏆 Symulacja Fazy Pucharowej")
    st.info("Automatyczne parowanie zwycięzców grup (Top 2 z każdej grupy).")
    leaders = {g: sort_group(st.session_state.groups[g]).iloc[0]['Drużyna'] for g in group_labels}
    runners_up = {g: sort_group(st.session_state.groups[g]).iloc[1]['Drużyna'] for g in group_labels}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**Para 1**")
        st.code(f"{leaders['A']} vs {runners_up['B']}")
    with c2:
        st.markdown("**Para 2**")
        st.code(f"{leaders['C']} vs {runners_up['D']}")
    with c3:
        st.markdown("**Para 3**")
        st.code(f"{leaders['E']} vs {runners_up['F']}")
    with c4:
        st.markdown("**Para 4**")
        st.code(f"{leaders['G']} vs {runners_up['H']}")

st.divider()
st.caption("Mistrzostwa Polski Juniorów 2026 | Dane pobierane z juniorzymmp.volleystation.com")
