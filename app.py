import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Cand.merc.-linjematch", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "DATA.xlsx"


@st.cache_data
def load_line_data(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path)
    headers = raw.iloc[0].tolist()
    df = raw.iloc[1:].copy()
    df.columns = headers
    df = df.reset_index(drop=True)

    numeric_cols = [c for c in df.columns if c != "Linje"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Ledighed" in df.columns:
        df["Jobsikkerhed"] = 1 - df["Ledighed"]

    return df


LINE_DF = load_line_data(DATA_PATH)

# -------------------------
# SPØRGESKEMA
# -------------------------
GROUPS = {
    "Arbejdsmarked": {
        "Løn": {
            "question": "Hvor vigtigt er det for dig at tjene mere end gennemsnittet for cand.merc.-kandidater?",
            "anchor": "Den gennemsnitlige startløn ligger omkring XX kr., men svar ud fra din egen opfattelse.",
            "column": "Løn",
        },
        "Jobsikkerhed": {
            "question": "Hvor vigtigt er det for dig at have jobsikkerhed i dit fremtidige job?",
            "anchor": "Jobsikkerhed kan forstås som lav risiko for ledighed efter endt uddannelse.",
            "column": "Jobsikkerhed",
        },
        "karakter_avg": {
            "question": "Hvor vigtigt er det for dig at opnå gode faglige resultater på studiet?",
            "anchor": "Fx karakterer over gennemsnittet eller generelt fagligt niveau.",
            "column": "karakter_avg",
        },
    }
}

GROUP_SUBTITLES = {
    "Arbejdsmarked": "Spørgsmål vedrørende arbejdsmarkedsfaktorer"
}

GROUP_ORDER = list(GROUPS.keys())


# -------------------------
# DESIGN (NYT)
# -------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #6fb7e9 0%, #84c3ef 50%, #a2d4f5 100%);
}

/* TOP */
.top-title {
    color: #eef3f8;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 1.5rem;
}

.top-subtitle {
    color: #eef3f8;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

/* PROGRESS BAR */
.stProgress > div > div {
    background: rgba(255,255,255,0.1);
}
.stProgress > div > div > div > div {
    background: rgba(255,255,255,0.7);
}

/* SPØRGSMÅL BOX */
.question-box {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 18px;
    padding: 1rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(4px);
}

/* TEKST */
.question-number {
    color: #e4edf5;
    font-size: 0.9rem;
    font-weight: 700;
}

.question-text {
    color: #f0f6fb;
    font-size: 1.05rem;
    font-weight: 700;
}

.anchor-text {
    color: #e4edf5;
    font-size: 0.95rem;
    font-style: italic;
    margin-bottom: 0.4rem;
}

/* RADIO */
div[role="radiogroup"] > label {
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.3);
}

div[role="radiogroup"] span {
    color: #eef3f8 !important;
}

/* GENEREL TEXT */
.stMarkdown, .stText {
    color: #eef3f8 !important;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# STATE
# -------------------------
if "step" not in st.session_state:
    st.session_state.step = 0


# -------------------------
# UI
# -------------------------
group = GROUP_ORDER[st.session_state.step]

st.markdown('<div class="top-title">Kandidatesten - Cand.merc.</div>', unsafe_allow_html=True)
st.markdown(f'<div class="top-subtitle">{GROUP_SUBTITLES[group]}</div>', unsafe_allow_html=True)

st.progress((st.session_state.step + 1) / len(GROUP_ORDER))

st.markdown("**Profilspørgsmål**")
st.caption("1 = Slet ikke · 2 = I lav grad · 3 = I nogen grad · 4 = I høj grad · 5 = I meget høj grad")

# -------------------------
# SPØRGSMÅL LOOP
# -------------------------
for i, (key, spec) in enumerate(GROUPS[group].items(), start=1):
    st.markdown('<div class="question-box">', unsafe_allow_html=True)

    st.markdown(f'<div class="question-number">Q{i:02d}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-text">{spec["question"]}</div>', unsafe_allow_html=True)

    if spec.get("anchor"):
        st.markdown(f'<div class="anchor-text">{spec["anchor"]}</div>', unsafe_allow_html=True)

    st.radio(
        "",
        options=[1,2,3,4,5],
        horizontal=True,
        key=f"q_{key}",
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)
