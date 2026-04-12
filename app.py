import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
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
    },
    "Studieform": {
        "Skriftlig": {
            "question": "Jeg foretrækker eksamener, hvor jeg skriver opgaver frem for mundtlige eksamener",
            "anchor": "Fx hjemmeopgaver eller skriftlige afleveringer frem for mundtlige prøver.",
            "column": "Skriftlig",
        },
        "Individuel": {
            "question": "Jeg foretrækker at arbejde individuelt frem for i grupper",
            "anchor": "Fx selvstændige opgaver frem for gruppearbejde og projekter.",
            "column": "Individuel",
        },
        "timer_ects": {
            "question": "Jeg foretrækker studier med meget undervisning frem for selvstudie",
            "anchor": "Fx mange undervisningstimer frem for selvstændig læsning.",
            "column": "timer_ects",
        },
    },
    "Arbejdsstil – kognitiv/performance": {
        "Adaptability": {
            "question": "Jeg trives med opgaver, hvor krav og rammer ofte ændrer sig",
            "anchor": "Fx opgaver uden faste strukturer eller med løbende ændringer.",
            "column": "Adaptability",
        },
        "AttentiontoDetail": {
            "question": "Jeg foretrækker opgaver, hvor præcision er vigtigere end tempo",
            "anchor": "Fx opgaver hvor det er vigtigere at undgå fejl end at blive hurtigt færdig.",
            "column": "AttentiontoDetail",
        },
        "Initiative": {
            "question": "Jeg tager initiativ til nye opgaver uden at blive bedt om det",
            "anchor": "Fx selv at opsøge opgaver i studie- eller arbejdssammenhænge.",
            "column": "Initiative",
        },
    },
    "Arbejdsstil – social/ledelse": {
        "Integrity": {
            "question": "Jeg foretrækker arbejde med klare regler og faste rammer",
            "anchor": "Fx tydelige krav, procedurer og forventninger.",
            "column": "Integrity",
        },
        "Empathy": {
            "question": "Jeg inddrager andres perspektiver, før jeg træffer beslutninger",
            "anchor": "Fx at diskutere løsninger med andre før du beslutter dig.",
            "column": "Empathy",
        },
        "LeadershipOrientation": {
            "question": "Jeg motiveres af at have ansvar for at lede og koordinere andre",
            "anchor": "Fx at fordele opgaver eller tage ansvar i grupper.",
            "column": "LeadershipOrientation",
        },
    },
    "Faglige interesser": {
        "LawandGovernment": {
            "question": "Jeg interesserer mig for jura og regulering",
            "anchor": "Fx regler, lovgivning og offentlige systemer.",
            "column": "LawandGovernment",
        },
        "Mathematics": {
            "question": "Jeg interesserer mig for matematik og talbaserede analyser",
            "anchor": "Fx dataanalyse, statistik eller økonomiske beregninger.",
            "column": "Mathematics",
        },
        "SalesandMarketing": {
            "question": "Jeg interesserer mig for marketing og forbrugeradfærd",
            "anchor": "Fx branding, reklame og kundeadfærd.",
            "column": "SalesandMarketing",
        },
    },
}

GROUP_SUBTITLES = {
    "Arbejdsmarked": "Spørgsmål vedrørende arbejdsmarkedsfaktorer",
    "Studieform": "Spørgsmål vedrørende studieform",
    "Arbejdsstil – kognitiv/performance": "Spørgsmål vedrørende kognitiv arbejdsstil og performance",
    "Arbejdsstil – social/ledelse": "Spørgsmål vedrørende social arbejdsstil og ledelse",
    "Faglige interesser": "Spørgsmål vedrørende faglige interesser",
}

WEIGHT_QUESTIONS = {
    "Arbejdsmarked": "Hvor stor betydning har arbejdsmarked og karrieremuligheder for dit valg af kandidatlinje?",
    "Studieform": "I hvor høj grad prioriterer du, at studieformen passer til dine præferencer?",
    "Arbejdsstil – kognitiv/performance": "Hvor vigtigt er det for dig, at uddannelsen matcher din måde at arbejde på?",
    "Arbejdsstil – social/ledelse": "Hvor vigtigt er det for dig, at uddannelsen matcher din sociale arbejdsstil?",
    "Faglige interesser": "Hvor vigtigt er det for dig, at uddannelsen matcher dine faglige interesser?",
}

GROUP_ORDER = list(GROUPS.keys())

SCALE_LABELS = {
    "Slet ikke": 1,
    "I lav grad": 2,
    "I nogen grad": 3,
    "I høj grad": 4,
    "I meget høj grad": 5,
}


def response_to_zero_one(value) -> float:
    if isinstance(value, str):
        value = SCALE_LABELS[value]
    return (value - 1) / 4


def normalize_weights(raw_weights: dict) -> dict:
    total = sum(raw_weights.values())
    if total == 0:
        return {k: 1 / len(raw_weights) for k in raw_weights}
    return {k: v / total for k, v in raw_weights.items()}


def get_unique_group_columns(group_name: str) -> list[str]:
    seen = set()
    cols = []
    for spec in GROUPS[group_name].values():
        col = spec["column"]
        if col not in seen:
            seen.add(col)
            cols.append(col)
    return cols


def compute_group_match(user_profile: dict, line_row: pd.Series, group_name: str) -> float:
    cols = get_unique_group_columns(group_name)
    scores = []

    for col in cols:
        if col in user_profile and col in line_row.index and pd.notna(line_row[col]):
            scores.append(1 - abs(user_profile[col] - float(line_row[col])))

    return sum(scores) / len(scores) if scores else 0.0


def compute_all_scores(user_profile: dict, group_weights: dict, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        group_matches = {group: compute_group_match(user_profile, row, group) for group in GROUPS}
        total_score = sum(group_weights[g] * group_matches[g] for g in GROUPS)

        out = {
            "Linje": row["Linje"],
            "Score": total_score,
        }

        for group in GROUPS:
            out[f"Match_{group}"] = group_matches[group]

        rows.append(out)

    return pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)


def radar_figure(user_profile: dict, line_row: pd.Series) -> go.Figure:
    axis_labels = list(GROUPS.keys())
    user_vals = []
    line_vals = []

    for group in axis_labels:
        cols = get_unique_group_columns(group)
        valid_user_vals = [user_profile[c] for c in cols if c in user_profile]
        valid_line_vals = [float(line_row[c]) for c in cols if c in line_row.index and pd.notna(line_row[c])]

        user_vals.append(sum(valid_user_vals) / len(valid_user_vals) if valid_user_vals else 0)
        line_vals.append(sum(valid_line_vals) / len(valid_line_vals) if valid_line_vals else 0)

    user_vals.append(user_vals[0])
    line_vals.append(line_vals[0])
    labels = axis_labels + [axis_labels[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=user_vals,
        theta=labels,
        fill="toself",
        name="Din profil",
        line=dict(color="#0f2d52", width=3),
        fillcolor="rgba(15, 45, 82, 0.18)"
    ))

    fig.add_trace(go.Scatterpolar(
        r=line_vals,
        theta=labels,
        fill="toself",
        name=str(line_row["Linje"]),
        line=dict(color="#1f5fa8", width=3),
        fillcolor="rgba(31, 95, 168, 0.16)"
    ))

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        polar=dict(
            bgcolor="white",
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor="#d7e6f7",
                linecolor="#b9d1ee",
                tickfont=dict(color="#0f2d52")
            ),
            angularaxis=dict(
                gridcolor="#d7e6f7",
                linecolor="#b9d1ee",
                tickfont=dict(color="#0f2d52")
            )
        ),
        legend=dict(font=dict(color="#0f2d52")),
        showlegend=True,
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "intro"
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "weights" not in st.session_state:
        st.session_state.weights = {}
    if "raw_answers" not in st.session_state:
        st.session_state.raw_answers = {}


def scroll_to_top():
    components.html(
        """
        <script>
        const scrollNow = () => {
            window.parent.scrollTo(0, 0);

            const app = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
            if (app) {
                app.scrollTo(0, 0);
            }

            const main = window.parent.document.querySelector('section.main');
            if (main) {
                main.scrollTo(0, 0);
            }
        };

        scrollNow();
        setTimeout(scrollNow, 50);
        setTimeout(scrollNow, 150);
        setTimeout(scrollNow, 300);
        </script>
        """,
        height=0,
    )

def go_to_intro():
    st.session_state.page = "intro"
    st.session_state.step = 0


def go_to_test():
    st.session_state.page = "test"
    st.session_state.step = 0


def next_step():
    if st.session_state.step < len(GROUP_ORDER) - 1:
        st.session_state.step += 1
    else:
        st.session_state.page = "result"


def prev_step():
    if st.session_state.step > 0:
        st.session_state.step -= 1
    else:
        st.session_state.page = "intro"


def go_to_last_step():
    st.session_state.page = "test"
    st.session_state.step = len(GROUP_ORDER) - 1


def reset_test():
    for key in list(st.session_state.keys()):
        if key.startswith("widget_profile_") or key.startswith("widget_weight_"):
            del st.session_state[key]

    st.session_state.answers = {}
    st.session_state.raw_answers = {}
    st.session_state.weights = {}
    st.session_state.page = "intro"
    st.session_state.step = 0


def save_current_group_answers(group_name: str):
    items = GROUPS[group_name]

    for key in items.keys():
        widget_key = f"widget_profile_{key}"
        answer = st.session_state.get(widget_key)
        if answer is not None:
            st.session_state.raw_answers[widget_key] = answer

    for key, spec in items.items():
        widget_key = f"widget_profile_{key}"
        answer = st.session_state.get(widget_key)
        if answer is not None:
            st.session_state.answers[spec["column"]] = response_to_zero_one(answer)

    weight_widget_key = f"widget_weight_{group_name}"
    weight_answer = st.session_state.get(weight_widget_key)
    if weight_answer is not None:
        st.session_state.weights[group_name] = SCALE_LABELS[weight_answer]


def load_current_group_defaults(group_name: str):
    items = GROUPS[group_name]
    for key in items.keys():
        widget_key = f"widget_profile_{key}"
        if widget_key not in st.session_state and widget_key in st.session_state.raw_answers:
            st.session_state[widget_key] = st.session_state.raw_answers[widget_key]

    weight_widget_key = f"widget_weight_{group_name}"
    if weight_widget_key not in st.session_state and group_name in st.session_state.weights:
        reverse_map = {v: k for k, v in SCALE_LABELS.items()}
        st.session_state[weight_widget_key] = reverse_map[st.session_state.weights[group_name]]


def is_group_answered(group_name: str) -> bool:
    items = GROUPS[group_name]
    profile_ok = all(st.session_state.get(f"widget_profile_{key}") is not None for key in items.keys())
    weight_ok = st.session_state.get(f"widget_weight_{group_name}") is not None
    return profile_ok and weight_ok


def all_profile_columns_present(user_profile: dict) -> bool:
    required_cols = []
    seen = set()
    for group in GROUPS.values():
        for spec in group.values():
            col = spec["column"]
            if col not in seen:
                seen.add(col)
                required_cols.append(col)
    return all(col in user_profile for col in required_cols)


def render_test_header(step: int, total_steps: int, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="top-wrap">
            <div class="top-title">Kandidattesten - Cand.merc.</div>
            <div class="top-step">Trin {step} af {total_steps}</div>
            <div class="top-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_custom_progress(progress_value: float) -> None:
    st.markdown(
        f"""
        <div class="progress-shell">
            <div class="progress-fill" style="width:{progress_value * 100:.1f}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    :root {
        --blue-dark: #0f2d52;
        --blue-mid: #1f5fa8;
        --blue-soft: #dbeafe;
        --blue-soft-2: #eef5ff;
        --border-blue: #b9d1ee;
        --text-main: #0f2d52;
        --text-soft: #4a678c;
        --white: #ffffff;
    }

    .stApp {
        background: var(--white);
    }

    .block-container {
        max-width: 1460px;
        padding-top: 5.5rem;
        padding-bottom: 3rem;
    }

    .top-wrap {
        margin-bottom: 0.5rem;
    }

    .top-title {
        color: var(--blue-dark);
        font-size: 4.2rem;
        font-weight: 800;
        line-height: 1.05;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
        letter-spacing: -0.03em;
    }

    .top-step {
        color: var(--blue-mid);
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 1.4rem;
    }

    .top-subtitle {
        color: var(--blue-dark);
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1.12;
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
    }

    .progress-shell {
        width: 92%;
        height: 16px;
        border: 1px solid var(--border-blue);
        border-radius: 999px;
        background: var(--blue-soft-2);
        overflow: hidden;
        margin-bottom: 3rem;
    }

    .progress-fill {
        height: 100%;
        background: var(--blue-dark);
        border-radius: 999px;
    }

    .intro-box {
        background: var(--blue-soft-2);
        border: 1px solid var(--border-blue);
        border-radius: 24px;
        padding: 1.9rem 2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        color: var(--text-main);
    }

    .intro-title {
        color: var(--blue-dark);
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }

    .intro-text {
        color: var(--text-main);
        font-size: 1.02rem;
        line-height: 1.75;
        margin-bottom: 1.25rem;
    }

    .section-title {
        color: var(--blue-dark);
        font-size: 1.45rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .section-caption {
        color: var(--text-soft);
        font-size: 0.98rem;
        font-style: italic;
        margin-bottom: 1.4rem;
    }

    .question-number {
        color: var(--blue-mid);
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .question-text {
        color: var(--blue-dark);
        font-size: 1.08rem;
        font-weight: 800;
        line-height: 1.4;
        margin-bottom: 0.35rem;
    }

    .anchor-text {
        color: var(--text-soft);
        font-size: 0.95rem;
        font-style: italic;
        line-height: 1.45;
        margin-bottom: 0.8rem;
    }

    .soft-note {
        color: var(--text-soft);
        font-size: 0.92rem;
        margin-top: 0.7rem;
    }

    div[role="radiogroup"] {
        gap: 0.9rem;
        margin-top: 0.2rem;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
    }

    div[role="radiogroup"] > label {
        border: 1.5px solid var(--border-blue);
        border-radius: 999px;
        padding: 0.65rem 1.15rem;
        background: var(--blue-soft-2);
        min-width: 160px;
        justify-content: center;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    div[role="radiogroup"] > label:hover {
        border-color: var(--blue-mid);
        background: var(--blue-soft);
    }

    div[role="radiogroup"] > label span {
        color: var(--blue-dark) !important;
        font-weight: 700;
        font-size: 0.96rem;
        text-align: center;
    }

    div[role="radiogroup"] > label:has(input:checked) {
        background: var(--blue-dark) !important;
        border-color: var(--blue-dark) !important;
        box-shadow: 0 4px 14px rgba(15,45,82,0.25);
    }

    div[role="radiogroup"] > label:has(input:checked) * {
        color: white !important;
    }

    div[role="radiogroup"] > label:has(input:checked) span {
        color: white !important;
    }

    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px;
        padding: 0.65rem 1.25rem;
        font-weight: 700;
        border: 1.5px solid var(--blue-dark);
    }

    .stButton > button[kind="primary"] {
        background: var(--blue-dark) !important;
        color: white !important;
    }

    .stButton > button[kind="primary"] * {
        color: white !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #133764;
        border-color: #133764;
        color: var(--white);
    }

    .stButton > button:not([kind="primary"]),
    .stDownloadButton > button {
        background: var(--white);
        color: var(--blue-dark);
    }

    .stButton > button:not([kind="primary"]):hover,
    .stDownloadButton > button:hover {
        background: var(--blue-soft-2);
        color: var(--blue-dark);
        border-color: var(--blue-mid);
    }

    div[data-testid="stMetric"] {
        background: var(--blue-soft-2);
        border: 1px solid var(--border-blue);
        border-radius: 18px;
        padding: 0.95rem 1rem;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div {
        color: var(--blue-dark) !important;
    }

    div[data-testid="stDataFrame"] {
        background: var(--white);
        border: 1px solid var(--border-blue);
        border-radius: 18px;
        padding: 0.25rem;
    }

    div[data-testid="stExpander"] {
        background: var(--blue-soft-2);
        border-radius: 18px;
        border: 1px solid var(--border-blue);
    }

    div[data-testid="stExpander"] summary p {
        color: var(--blue-dark) !important;
        font-weight: 700;
    }

    .stMarkdown, .stText, .stSubheader, .stHeader, .stCaption, p, li, label {
        color: var(--text-main) !important;
    }

    h1, h2, h3 {
        color: var(--blue-dark) !important;
        font-weight: 800 !important;
    }

    .stAlert {
        border-radius: 16px;
    }

    .stProgress {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

init_state()

if st.session_state.page == "intro":
    scroll_to_top()
    st.markdown('<div class="top-title">Kandidattesten - Cand.merc.</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="intro-box">
<div class="intro-text">Valg af kandidatlinje kan være svært, fordi flere uddannelser kan virke interessante på papiret. Testen fungerer som et beslutningsstøtteværktøj, der kan gøre dine overvejelser mere konkrete og hjælpe dig med at se, hvilke linjer der matcher dine prioriteringer bedst.</div>

<div class="intro-text">Denne test hjælper dig med at reflektere over, hvilken cand.merc.-linje der passer bedst til dig. Testen sammenholder dine præferencer med data om blandt andet studieform, arbejdsmarked, faglige interesser og arbejdsstil.</div>

<div class="intro-text" style="margin-bottom:0;">Du svarer på spørgsmål i små blokke. Til sidst beregner appen en samlet anbefaling og viser de linjer, der matcher din profil bedst.</div>
</div>
""", unsafe_allow_html=True)

    with st.expander("Se model og metode", expanded=False):
        st.latex(r"Score_j = \sum_k w_k \cdot (1 - |person_k - linje_{jk}|)")
        st.write(
            "Alle profilsvar omregnes fra 1–5 til 0–1. "
            "Hvert spørgsmål måler én dimension, og vægtene normaliseres automatisk, så de samlet summerer til 1."
        )

    st.button("Start testen", type="primary", on_click=go_to_test)

elif st.session_state.page == "test":
    scroll_to_top()
    current_group = GROUP_ORDER[st.session_state.step]
    current_items = GROUPS[current_group]

    load_current_group_defaults(current_group)

    render_test_header(
        step=st.session_state.step + 1,
        total_steps=len(GROUP_ORDER),
        subtitle=GROUP_SUBTITLES[current_group],
    )

    render_custom_progress((st.session_state.step + 1) / len(GROUP_ORDER))

    for i, (key, spec) in enumerate(current_items.items(), start=1):
        st.markdown(f'<div class="question-number">Q{i:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="question-text">{spec["question"]}</div>', unsafe_allow_html=True)

        if spec.get("anchor"):
            st.markdown(f'<div class="anchor-text">{spec["anchor"]}</div>', unsafe_allow_html=True)

        st.radio(
            "",
            options=list(SCALE_LABELS.keys()),
            horizontal=True,
            index=None,
            key=f"widget_profile_{key}",
            label_visibility="collapsed",
        )

    st.markdown(
        '<div class="section-caption">Angiv hvor vigtigt dette område samlet set er for dig i valget af kandidatlinje.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="question-number">Vægt</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-text">{WEIGHT_QUESTIONS[current_group]}</div>', unsafe_allow_html=True)

    st.radio(
        "",
        options=list(SCALE_LABELS.keys()),
        horizontal=True,
        index=None,
        key=f"widget_weight_{current_group}",
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 1.6rem;'></div>", unsafe_allow_html=True)

    left_space, col1, col2, right_space = st.columns([2, 1, 1, 2])

    with col1:
        if st.button("⬅ Tilbage", use_container_width=True):
            save_current_group_answers(current_group)
            prev_step()
            st.rerun()

    with col2:
        if st.button("Videre ➜", type="primary", use_container_width=True):
            if not is_group_answered(current_group):
                st.warning("Du skal besvare alle spørgsmål i denne blok, før du kan gå videre.")
            else:
                save_current_group_answers(current_group)
                next_step()
                st.rerun()

    st.markdown(
        '<div class="soft-note">Dine svar gemmes løbende, så du kan gå frem og tilbage mellem blokkene.</div>',
        unsafe_allow_html=True
    )

elif st.session_state.page == "result":
    scroll_to_top()
    user_profile = st.session_state.answers.copy()
    raw_weights = st.session_state.weights.copy()
    group_weights = normalize_weights(raw_weights)

    st.markdown('<div class="top-title">Kandidattesten - Cand.merc.</div>', unsafe_allow_html=True)

    if not all_profile_columns_present(user_profile):
        st.error("Der mangler et eller flere profilsvar. Gå tilbage og gennemfør alle spørgsmål igen.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅ Tilbage til sidste blok"):
                go_to_last_step()
                st.rerun()
        with c2:
            if st.button("Start forfra"):
                reset_test()
                st.rerun()
        st.stop()

    scores = compute_all_scores(user_profile, group_weights, LINE_DF)

    if scores.empty:
        st.error("Der kunne ikke beregnes et resultat.")
        st.stop()

    top3 = scores.head(3)

    if len(top3) < 3:
        st.error("Der er for få linjer i datasættet til at vise top 3.")
        st.stop()

    best_name = top3.iloc[0]["Linje"]
    best_row = LINE_DF.loc[LINE_DF["Linje"] == best_name].iloc[0]

    st.subheader("Top 3 anbefalinger")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(label="Top 1", value=str(top3.iloc[0]["Linje"]), delta=f"Score: {top3.iloc[0]['Score']:.3f}")
    with c2:
        st.metric(label="Top 2", value=str(top3.iloc[1]["Linje"]), delta=f"Score: {top3.iloc[1]['Score']:.3f}")
    with c3:
        st.metric(label="Top 3", value=str(top3.iloc[2]["Linje"]), delta=f"Score: {top3.iloc[2]['Score']:.3f}")

    st.subheader(f"Bedste samlede match: {best_name}")
    st.plotly_chart(radar_figure(user_profile, best_row), use_container_width=True)

    st.subheader("Kort fortolkning")
    group_matches = {g: top3.iloc[0][f"Match_{g}"] for g in GROUPS}
    sorted_groups = sorted(group_matches.items(), key=lambda x: x[1], reverse=True)
    strengths = ", ".join(g for g, _ in sorted_groups[:2])
    weaker = ", ".join(g for g, _ in sorted_groups[-2:])

    st.write(
        f"Dit bedste match er **{best_name}**. "
        f"Dine stærkeste matches ligger især inden for **{strengths}**, "
        f"mens de relativt svagere matches ligger inden for **{weaker}**."
    )

    st.subheader("Dine vægte")
    weights_df = pd.DataFrame({
        "Dimension": list(group_weights.keys()),
        "Rå score": [raw_weights[g] for g in group_weights],
        "Normaliseret vægt": [round(group_weights[g], 3) for g in group_weights],
    })
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

    st.subheader("Din profil")
    profile_df = pd.DataFrame({
        "Variabel": list(user_profile.keys()),
        "Score (0-1)": [round(v, 3) for v in user_profile.values()],
    })
    st.dataframe(profile_df, use_container_width=True, hide_index=True)

    st.subheader("Alle linjer")
    st.dataframe(scores, use_container_width=True, hide_index=True)

    st.subheader("Eksempel på udfyldt formel på gruppeniveau")
    terms = [f"{group_weights[g]:.3f} × {top3.iloc[0][f'Match_{g}']:.3f}" for g in GROUPS]
    st.code(" + ".join(terms) + f" = {top3.iloc[0]['Score']:.3f}")

    c1, c2, c3 = st.columns([1, 1, 3])

    with c1:
        if st.button("⬅ Tilbage til spørgsmål"):
            go_to_last_step()
            st.rerun()

    with c2:
        if st.button("Start forfra"):
            reset_test()
            st.rerun()

    st.download_button(
        "Download resultater som CSV",
        data=scores.to_csv(index=False).encode("utf-8"),
        file_name="linjematch_resultater.csv",
        mime="text/csv",
    )
