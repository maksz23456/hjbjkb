import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="MP Juniorów - Oficjalne Wyniki", layout="wide")

# --- MODERN SPORT DESIGN ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

h1 {
    font-size: 42px !important;
    font-weight: 800 !important;
    color: white !important;
    text-align: center;
    margin-bottom: 30px;
}

h3 {
    color: #e2e8f0 !important;
    font-weight: 600;
}

[data-testid="stDataFrame"] {
    background-color: #1e293b;
    border-radius: 14px;
    padding: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

.stTabs [data-baseweb="tab"] {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 10px 20px;
    color: #cbd5e1;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    color: white !important;
}

.stButton>button {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    color: white;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    transition: 0.3s;
}

.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 14px rgba(37,99,235,0.5);
}
</style>
""", unsafe_allow_html=True)


# --- DATA INIT ---
def get_group_labels():
    return [chr(i) for i in range(65, 73)]  # A-H


if 'groups' not in st.session_state:
    st.session_state.groups = {
        g: pd.DataFrame({
            'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)],
            'Podgrupa_ID': [1,1,1,2,2,2],
            'Mecze': 0, 'Punkty': 0, 'Wygrane': 0,
            'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
        }) for g in get_group_labels()
    }
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

if 'matches' not in st.session_state:
    st.session_state.matches = pd.DataFrame(columns=[
        'Grupa', 'Gospodarz', 'Gość',
        'S1_H','S1_G','S2_H','S2_G','S3_H','S3_G','S4_H','S4_G','S5_H','S5_G'
    ])


# --- CALC ENGINE ---
def recalculate_everything():
    for g in get_group_labels():
        df = st.session_state.groups[g].copy()
        for col in ['Mecze','Punkty','Wygrane','Sety+','Sety-','Pkt+','Pkt-']:
            df[col] = 0

        m_group = st.session_state.matches[st.session_state.matches['Grupa'] == g]

        for _, m in m_group.iterrows():
            sh, sg, ph_t, pg_t = 0, 0, 0, 0
            for i in range(1, 6):
                try:
                    h, gp = int(m[f'S{i}_H']), int(m[f'S{i}_G'])
                    ph_t += h
                    pg_t += gp
                    if h > gp:
                        sh += 1
                    elif gp > h:
                        sg += 1
                except:
                    continue

            if sh == 3 or sg == 3:
                if sh == 3 and sg < 2:
                    p_h, p_g = 3, 0
                elif sh == 3 and sg == 2:
                    p_h, p_g = 2, 1
                elif sg == 3 and sh == 2:
                    p_h, p_g = 1, 2
                else:
                    p_h, p_g = 0, 3

                for team, role in [(m['Gospodarz'], 'H'), (m['Gość'], 'G')]:
                    idx = df[df['Drużyna'] == team].index
                    if not idx.empty:
                        i = idx[0]
                        df.at[i,'Mecze'] += 1
                        df.at[i,'Punkty'] += p_h if role == 'H' else p_g
                        df.at[i,'Wygrane'] += 1 if (role == 'H' and sh > sg) or (role == 'G' and sg > sh) else 0
                        df.at[i,'Sety+'] += sh if role == 'H' else sg
                        df.at[i,'Sety-'] += sg if role == 'H' else sh
                        df.at[i,'Pkt+'] += ph_t if role == 'H' else pg_t
                        df.at[i,'Pkt-'] += pg_t if role == 'H' else ph_t

        st.session_state.groups[g] = df


def apply_final_style(row):
    if row['Miejsce'] == 1:
        return ['background: linear-gradient(90deg,#16a34a,#22c55e); color: white; font-weight:700']*len(row)
    elif row['Miejsce'] == 2:
        return ['background: linear-gradient(90deg,#2563eb,#38bdf8); color:white; font-weight:600']*len(row)
    else:
        return ['background-color:#1e293b; color:#cbd5e1']*len(row)


recalculate_everything()

# --- UI ---
st.markdown("<h1>🏐 Mistrzostwa Polski Juniorów</h1>", unsafe_allow_html=True)

t1, t2 = st.tabs(["📊 TABELE", "⚙️ ADMIN"])

with t1:
    for g in get_group_labels():
        st.markdown(f"### {st.session_state.group_names[g]}")

        total_matches = len(st.session_state.matches[st.session_state.matches['Grupa']==g])
        st.markdown(f"""
        <div style='background:linear-gradient(90deg,#2563eb,#06b6d4);
        padding:10px;border-radius:12px;color:white;font-weight:600;text-align:center;margin-bottom:15px;'>
        Rozegrane mecze: {total_matches}
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        for p_id in [1,2]:
            with (c1 if p_id == 1 else c2):
                st.write(f"Podgrupa {p_id}")
                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID']==p_id].copy()
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0,0.1)
                sub = sub.sort_values(['Punkty','Wygrane','S_Ratio'], ascending=False)
                sub.insert(0,'Miejsce', range(1,4))

                st.dataframe(
                    sub.drop(columns=['S_Ratio','Podgrupa_ID']).style.apply(apply_final_style, axis=1),
                    hide_index=True,
                    use_container_width=True
                )
        st.divider()


with t2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())

    st.markdown("### ➕ Dodaj wynik meczu")

    with st.form(key=f"form_{sel_g}"):
        t_list = st.session_state.groups[sel_g]['Drużyna'].tolist()
        col1, col2 = st.columns(2)
        h_team = col1.selectbox("Gospodarz", t_list)
        a_team = col2.selectbox("Gość", [t for t in t_list if t != h_team])

        res = []
        for j in range(5):
            colA, colB = st.columns(2)
            with colA:
                s_h = st.number_input(f"Set {j+1} - Gospodarz", 0, 45, 0)
            with colB:
                s_g = st.number_input(f"Set {j+1} - Gość", 0, 45, 0)
            res.extend([s_h, s_g])

        if st.form_submit_button("DODAJ MECZ"):
            new_row = pd.DataFrame([[sel_g, h_team, a_team] + res],
                columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_row], ignore_index=True)
            recalculate_everything()
            st.rerun()

    if st.button("🚨 WYCZYŚĆ WSZYSTKIE DANE"):
        st.session_state.clear()
        st.rerun()
