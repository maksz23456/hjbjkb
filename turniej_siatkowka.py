import streamlit as st
import pandas as pd

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="MP Juniorów - Oficjalne Wyniki", layout="wide")

# -------------------------------------------------
# MODERN SPORT DESIGN (DARK MODE OPTIMIZED)
# -------------------------------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    h1 { font-size: 42px !important; font-weight: 800 !important; color: white !important; text-align: center; margin-bottom: 30px; }
    h3 { color: #e2e8f0 !important; font-weight: 600; margin-top: 20px; }
    [data-testid="stDataFrame"] { background-color: #1e293b; border-radius: 14px; padding: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 10px 10px 0px 0px; color: #cbd5e1; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #2563eb, #06b6d4) !important; color: white !important; }
    .stButton>button { background: linear-gradient(90deg, #2563eb, #06b6d4); color: white; border-radius: 10px; width: 100%; border: none; }
    .info-box { background: linear-gradient(90deg, #2563eb, #06b6d4); padding: 10px; border-radius: 12px; color: white; font-weight: 600; text-align: center; margin-bottom: 15px; }
    .match-result { background-color: rgba(255,255,255,0.05); padding: 8px; border-radius: 8px; margin-bottom: 5px; color: #cbd5e1; border-left: 4px solid #2563eb; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# DATA INIT
# -------------------------------------------------
def get_group_labels():
    return [chr(i) for i in range(65, 73)]

if 'groups' not in st.session_state:
    st.session_state.groups = {
        g: pd.DataFrame({
            'Drużyna': [f'Zespół {g}{i}' for i in range(1,7)],
            'Podgrupa_ID': [1,1,1,2,2,2],
            'Mecze': 0, 'Punkty': 0, 'Wygrane': 0, 'Sety+': 0, 'Sety-': 0, 'Pkt+': 0, 'Pkt-': 0
        }) for g in get_group_labels()
    }
    st.session_state.group_names = {g: f"Grupa {g}" for g in get_group_labels()}

if 'matches' not in st.session_state:
    st.session_state.matches = pd.DataFrame(columns=[
        'Grupa', 'Gospodarz', 'Gość', 'S1_H','S1_G','S2_H','S2_G','S3_H','S3_G','S4_H','S4_G','S5_H','S5_G'
    ])

# -------------------------------------------------
# CALCULATION ENGINE
# -------------------------------------------------
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
                    h, v = int(m[f'S{i}_H']), int(m[f'S{i}_G'])
                    if h == 0 and v == 0: continue
                    ph_t += h; pg_t += v
                    if h > v: sh += 1
                    elif v > h: sg += 1
                except: continue
            if sh == 3 or sg == 3:
                p_h, p_g = ((3, 0) if sg < 2 else (2, 1)) if sh == 3 else ((1, 2) if sh == 2 else (0, 3))
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
    if row['Miejsce'] == 1: return ['background: linear-gradient(90deg,#16a34a,#22c55e); color: white; font-weight:700']*len(row)
    if row['Miejsce'] == 2: return ['background: linear-gradient(90deg,#2563eb,#38bdf8); color:white; font-weight:600']*len(row)
    return ['background-color:#1e293b; color:#cbd5e1']*len(row)

recalculate_everything()

# -------------------------------------------------
# UI
# -------------------------------------------------
st.markdown("<h1>🏐 Mistrzostwa Polski Juniorów</h1>", unsafe_allow_html=True)
t1, t2 = st.tabs(["📊 TABELE I WYNIKI", "⚙️ PANEL ADMINA"])

with t1:
    for g in get_group_labels():
        st.markdown(f"### {st.session_state.group_names[g]}")
        group_matches = st.session_state.matches[st.session_state.matches['Grupa']==g]
        st.markdown(f"<div class='info-box'>Rozegrane mecze: {len(group_matches)}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        for p_id in [1,2]:
            with (c1 if p_id == 1 else c2):
                st.markdown(f"**Podgrupa {p_id}**")
                sub = st.session_state.groups[g][st.session_state.groups[g]['Podgrupa_ID']==p_id].copy()
                sub['S_Ratio'] = sub['Sety+'] / sub['Sety-'].replace(0,0.1)
                sub = sub.sort_values(['Punkty','Wygrane','S_Ratio'], ascending=False)
                sub.insert(0,'Miejsce', range(1, len(sub)+1))
                st.dataframe(sub.drop(columns=['S_Ratio','Podgrupa_ID']).style.apply(apply_final_style, axis=1), hide_index=True, use_container_width=True)

        # NOWA SEKCJA: WYNIKI MECZÓW POD TABELAMI
        if not group_matches.empty:
            with st.expander(f"📑 Historia meczów - {st.session_state.group_names[g]}", expanded=True):
                for _, m in group_matches.iterrows():
                    # Obliczanie setów dla wyświetlania
                    sh, sg = 0, 0
                    sets_detail = []
                    for i in range(1, 6):
                        h, g_pts = m[f'S{i}_H'], m[f'S{i}_G']
                        if h > 0 or g_pts > 0:
                            sets_detail.append(f"{h}:{g_pts}")
                            if h > g_pts: sh += 1
                            elif g_pts > h: sg += 1
                    
                    res_str = f"**{m['Gospodarz']} {sh}:{sg} {m['Gość']}**"
                    sets_str = f" <span style='color: #94a3b8;'>({', '.join(sets_detail)})</span>"
                    st.markdown(f"<div class='match-result'>{res_str}{sets_str}</div>", unsafe_allow_html=True)
        st.divider()

with t2:
    sel_g = st.selectbox("Wybierz grupę:", get_group_labels())
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.session_state.group_names[sel_g] = st.text_input("Nazwa grupy:", value=st.session_state.group_names[sel_g])
    with col_cfg2:
        edited_teams = st.data_editor(st.session_state.groups[sel_g][['Drużyna']], hide_index=True, use_container_width=True)
        if st.button("Zapisz zmiany"):
            st.session_state.groups[sel_g]['Drużyna'] = edited_teams['Drużyna'].values
            st.rerun()

    st.markdown("### ➕ Dodaj mecz")
    with st.form(f"f_{sel_g}"):
        t_l = st.session_state.groups[sel_g]['Drużyna'].tolist()
        c_a, c_b = st.columns(2)
        h_t, a_t = c_a.selectbox("Gospodarz", t_l), c_b.selectbox("Gość", [t for t in t_l if t != h_t])
        res = []
        for j in range(5):
            cA, cB = st.columns(2)
            res.extend([cA.number_input(f"S{j+1} - {h_t}", 0, 45, 0, key=f"h{sel_g}{j}"), cB.number_input(f"S{j+1} - {a_t}", 0, 45, 0, key=f"g{sel_g}{j}")])
        if st.form_submit_button("DODAJ MECZ"):
            new_m = pd.DataFrame([[sel_g, h_t, a_t] + res], columns=st.session_state.matches.columns)
            st.session_state.matches = pd.concat([st.session_state.matches, new_m], ignore_index=True)
            recalculate_everything()
            st.rerun()

    st.markdown("### 🛠️ Edycja")
    curr_m = st.session_state.matches[st.session_state.matches['Grupa'] == sel_g]
    if not curr_m.empty:
        e_m = st.data_editor(curr_m, use_container_width=True, num_rows="dynamic")
        if st.button("Zapisz zmiany w historii"):
            st.session_state.matches = pd.concat([st.session_state.matches[st.session_state.matches['Grupa'] != sel_g], e_m], ignore_index=True)
            recalculate_everything()
            st.rerun()
