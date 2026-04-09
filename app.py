import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Cand.merc.-linjematch", page_icon="🎓", layout="wide")

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

# ---------------------------------------------------
# SPØRGESKEMA
# Hvert item kan have:
# - question
# - anchor (undertekst)
# - column (hvilken modelvariabel item måler)
# - reverse (om skalaen skal vendes)
#
# Flere items kan pege på samme column.
# I så fald tages gennemsnittet af de omkodede scores.
# ---------------------------------------------------
GROUPS = {
    "Arbejdsmarked": {
        "Løn_main": {
            "question": "Hvor vigtigt er det for dig at tjene mere end gennemsnittet for cand.merc.-kandidater?",
            "anchor": "Den gennemsnitlige startløn for cand.merc.-kandidater ligger omkring XX kr., men du kan svare ud fra din egen opfattelse.",
            "column": "Løn",
            "reverse": False,
        },
        "Løn_reverse": {
            "question": "Hvor uvigtigt er det for dig at tjene mere end gennemsnittet for cand.merc.-kandidater?",
            "anchor": "Den gennemsnitlige startløn for cand.merc.-kandidater ligger omkring XX kr., men du kan svare ud fra din egen opfattelse.",
            "column": "Løn",
            "reverse": True,
        },
        "Jobsikkerhed_main": {
            "question": "Hvor vigtigt er det for dig at have jobsikkerhed i dit fremtidige job?",
            "anchor": "Jobsikkerhed kan fx forstås som lav risiko for ledighed efter endt uddannelse.",
            "column": "Jobsikkerhed",
            "reverse": False,
        },
        "karakter_avg_main": {
            "question": "Hvor vigtigt er det for dig at opnå gode faglige resultater på studiet?",
            "anchor": "Fx at opnå karakterer over gennemsnittet eller klare sig fagligt godt.",
            "column": "karakter_avg",
            "reverse": False,
        },
    },
    "Studieform": {
        "Skriftlig_main": {
            "question": "Jeg foretrækker eksamener, hvor jeg skriver opgaver frem for mundtlige eksamener",
            "anchor": "Fx hjemmeopgaver eller skriftlige afleveringer frem for mundtlige prøver.",
            "column": "Skriftlig",
            "reverse": False,
        },
        "Individuel_main": {
            "question": "Jeg foretrækker at arbejde individuelt frem for i grupper",
            "anchor": "Fx selvstændige opgaver frem for gruppearbejde og projekter.",
            "column": "Individuel",
            "reverse": False,
        },
        "Individuel_reverse": {
            "question": "Jeg foretrækker at arbejde i grupper frem for individuelt",
            "anchor": "Fx gruppearbejde og projekter frem for selvstændige opgaver.",
            "column": "Individuel",
            "reverse": True,
        },
        "timer_ects_main": {
            "question": "Jeg foretrækker studier med meget undervisning frem for selvstudie",
            "anchor": "Fx mange undervisningstimer frem for selvstændig læsning.",
            "column": "timer_ects",
            "reverse": False,
        },
    },
    "Arbejdsstil – kognitiv/performance": {
        "Adaptability_main": {
            "question": "Jeg trives med opgaver, hvor krav og rammer ofte ændrer sig",
            "anchor": "Fx opgaver uden faste strukturer eller med løbende ændringer.",
            "column": "Adaptability",
            "reverse": False,
        },
        "AttentiontoDetail_main": {
            "question": "Jeg foretrækker opgaver, hvor præcision er vigtigere end tempo",
            "anchor": "Fx opgaver hvor det er vigtigere at undgå fejl end at blive hurtigt færdig.",
            "column": "AttentiontoDetail",
            "reverse": False,
        },
        "AttentiontoDetail_reverse": {
            "question": "Jeg foretrækker opgaver, hvor tempo er vigtigere end præcision",
            "anchor": "Fx opgaver hvor det er vigtigere at blive hurtigt færdig end at undgå fejl.",
            "column": "AttentiontoDetail",
            "reverse": True,
        },
        "Initiative_main": {
            "question": "Jeg tager initiativ til nye opgaver uden at blive bedt om det",
            "anchor": "Fx selv at opsøge opgaver i studie- eller arbejdssammenhænge.",
            "column": "Initiative",
            "reverse": False,
        },
    },
    "Arbejdsstil – social/ledelse": {
        "Integrity_main": {
            "question": "Jeg foretrækker arbejde med klare regler og faste rammer",
            "anchor": "Fx tydelige krav, procedurer og forventninger.",
            "column": "Integrity",
            "reverse": False,
        },
        "Empathy_main": {
            "question": "Jeg inddrager andres perspektiver, før jeg træffer beslutninger",
            "anchor": "Fx at diskutere løsninger med andre før du beslutter dig.",
            "column": "Empathy",
            "reverse": False,
        },
        "Empathy_reverse": {
            "question": "Jeg træffer beslutninger uden i høj grad at inddrage andre",
            "anchor": "Fx at tage beslutninger selv uden at diskutere dem med andre.",
            "column": "Empathy",
            "reverse": True,
        },
        "LeadershipOrientation_main": {
            "question": "Jeg motiveres af at have ansvar for at lede og koordinere andre",
            "anchor": "Fx at fordele opgaver eller tage ansvar i grupper.",
            "column": "LeadershipOrientation",
            "reverse": False,
        },
    },
    "Faglige interesser": {
        "LawandGovernment_main": {
            "question": "Jeg interesserer mig for jura og regulering",
            "anchor": "Fx regler, lovgivning og offentlige systemer.",
            "column": "LawandGovernment",
            "reverse": False,
        },
        "Mathematics_main": {
            "question": "Jeg interesserer mig for matematik og talbaserede analyser",
            "anchor": "Fx dataanalyse, statistik eller økonomiske beregninger.",
            "column": "Mathematics",
            "reverse": False,
        },
        "Mathematics_reverse": {
            "question": "Jeg foretrækker opgaver, der ikke involverer tal eller analyser",
            "anchor": "Fx opgaver uden matematik, statistik eller dataanalyse.",
            "column": "Mathematics",
            "reverse": True,
        },
        "SalesandMarketing_main": {
            "question": "Jeg interesserer mig for marketing og forbrugeradfærd",
            "anchor": "Fx branding, reklame og kundeadfærd.",
            "column": "SalesandMarketing",
            "reverse": False,
        },
    },
}

WEIGHT_QUESTIONS = {
    "Arbejdsmarked": "Hvor stor betydning har arbejdsmarked og karrieremuligheder for dit valg af kandidatlinje?",
    "Studieform": "I hvor høj grad prioriterer du, at studieformen passer til dine præferencer?",
    "Arbejdsstil – kognitiv/performance": "Hvor vigtigt er det for dig, at uddannelsen matcher din måde at arbejde på?",
    "Arbejdsstil – social/ledelse": "Hvor vigtigt er det for dig, at uddannelsen matcher din sociale arbejdsstil?",
    "Faglige interesser": "Hvor vigtigt er det for dig, at uddannelsen matcher dine faglige interesser?",
}

GROUP_ORDER = list(GROUPS.keys())


def response_to_zero_one(value: int, reverse: bool = False) -> float:
    scaled = (value - 1) / 4
    return 1 - scaled if reverse else scaled


def zero_one_to_response(value: float, reverse: bool = False) -> int:
    scaled = 1 - value if reverse else value
    return int(round(scaled * 4 + 1))


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
    fig.add_trace(go.Scatterpolar(r=user_vals, theta=labels, fill="toself", name="Din profil"))
    fig.add_trace(go.Scatterpolar(r=line_vals, theta=labels, fill="toself", name=str(line_row["Linje"])))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
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

    # gem rå widgetsvar
    for key in items.keys():
        widget_key = f"widget_profile_{key}"
        answer = st.session_state.get(widget_key)
        if answer is not None:
            st.session_state.raw_answers[widget_key] = answer

    # omkod og aggreger til modelvariabler
    col_scores = {}
    for key, spec in items.items():
        widget_key = f"widget_profile_{key}"
        answer = st.session_state.get(widget_key)
        if answer is not None:
            scaled = response_to_zero_one(answer, reverse=spec.get("reverse", False))
            col_scores.setdefault(spec["column"], []).append(scaled)

    for col, values in col_scores.items():
        st.session_state.answers[col] = sum(values) / len(values)

    # vægt
    weight_widget_key = f"widget_weight_{group_name}"
    weight_answer = st.session_state.get(weight_widget_key)
    if weight_answer is not None:
        st.session_state.weights[group_name] = weight_answer


def load_current_group_defaults(group_name: str):
    items = GROUPS[group_name]

    for key in items.keys():
        widget_key = f"widget_profile_{key}"
        if widget_key not in st.session_state and widget_key in st.session_state.raw_answers:
            st.session_state[widget_key] = st.session_state.raw_answers[widget_key]

    weight_widget_key = f"widget_weight_{group_name}"
    if weight_widget_key not in st.session_state and group_name in st.session_state.weights:
        st.session_state[weight_widget_key] = st.session_state.weights[group_name]


def is_group_answered(group_name: str) -> bool:
    items = GROUPS[group_name]

    profile_ok = all(
        st.session_state.get(f"widget_profile_{key}") is not None
        for key in items.keys()
    )
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


# -------------------------
# STYLING
# -------------------------
st.markdown(
    """
    <style>
    .intro-box {
        background: #f8f9fb;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #e8ebf0;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .step-box {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #ececec;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .question-box {
        margin-bottom: 1.1rem;
    }

    .anchor-text {
        color: #5f6368;
        font-size: 0.92rem;
        margin-top: -0.35rem;
        margin-bottom: 0.35rem;
    }

    div[role="radiogroup"] {
        gap: 0.9rem;
        margin-top: 0.3rem;
        margin-bottom: 1rem;
    }

    div[role="radiogroup"] > label {
        border: 1px solid #d9d9d9;
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        background: #fafafa;
    }
    </style>
    """,
    unsafe_allow_html=True
)

init_state()

# -------------------------
# INTRO
# -------------------------
if st.session_state.page == "intro":
    st.title("🎓 Kandidatesten - Cand.merc.")

    st.markdown(
        """
        <div class="intro-box">
            <h3>Hvad handler testen om?</h3>
            <p>
                Denne test hjælper dig med at reflektere over, hvilken cand.merc.-linje der passer bedst til dig.
                Testen sammenholder dine præferencer med data om blandt andet studieform,
                arbejdsmarked, faglige interesser og arbejdsstil.
            </p>
            <h3>Hvorfor er den relevant?</h3>
            <p>
                Valg af kandidatlinje kan være svært, fordi flere uddannelser kan virke interessante på papiret.
                Testen fungerer som et beslutningsstøtteværktøj, der kan gøre dine overvejelser mere konkrete
                og hjælpe dig med at se, hvilke linjer der matcher dine prioriteringer bedst.
            </p>
            <h3>Hvordan fungerer den?</h3>
            <p>
                Du svarer på spørgsmål i små blokke. Til sidst beregner appen en samlet anbefaling
                og viser de linjer, der matcher din profil bedst.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("Se model og metode", expanded=False):
        st.latex(r"Score_j = \sum_k w_k \cdot (1 - |person_k - linje_{jk}|)")
        st.write(
            "Alle profilsvar omregnes fra 1–5 til 0–1. "
            "Reverse-coded spørgsmål vendes automatisk om, og hvis en dimension måles af både et normalt og et reverse-coded spørgsmål, "
            "beregnes den endelige profilsværdi som gennemsnittet af de to omkodede svar. "
            "Vægtene normaliseres automatisk, så de samlet summerer til 1."
        )

    st.button("Start testen", type="primary", on_click=go_to_test)

# -------------------------
# TESTFLOW
# -------------------------
elif st.session_state.page == "test":
    current_group = GROUP_ORDER[st.session_state.step]
    current_items = GROUPS[current_group]

    load_current_group_defaults(current_group)

    st.title("🎓 Kandidatesten - Cand.merc.")
    st.caption(f"Trin {st.session_state.step + 1} af {len(GROUP_ORDER)}")

    progress_value = (st.session_state.step + 1) / len(GROUP_ORDER)
    st.progress(progress_value)

    st.header(current_group)

    st.markdown('<div class="step-box">', unsafe_allow_html=True)

    st.markdown("#### Profilspørgsmål")
    st.caption("Skala: 1 = Slet ikke · 2 = I lav grad · 3 = I nogen grad · 4 = I høj grad · 5 = I meget høj grad")

    for key, spec in current_items.items():
        st.markdown('<div class="question-box">', unsafe_allow_html=True)
        st.radio(
            spec["question"],
            options=[1, 2, 3, 4, 5],
            horizontal=True,
            index=None,
            key=f"widget_profile_{key}"
        )
        if spec.get("anchor"):
            st.markdown(
                f'<div class="anchor-text">{spec["anchor"]}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### Vægtspørgsmål")
    st.caption("Angiv hvor vigtigt dette område samlet set er for dig i valget af kandidatlinje.")

    st.radio(
        WEIGHT_QUESTIONS[current_group],
        options=[1, 2, 3, 4, 5],
        horizontal=True,
        index=None,
        key=f"widget_weight_{current_group}"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("⬅ Tilbage"):
            save_current_group_answers(current_group)
            prev_step()
            st.rerun()

    with col2:
        if st.button("Videre ➜", type="primary"):
            if not is_group_answered(current_group):
                st.warning("Du skal besvare alle spørgsmål i denne blok, før du kan gå videre.")
            else:
                save_current_group_answers(current_group)
                next_step()
                st.rerun()

    st.markdown("---")
    st.caption("Dine svar gemmes løbende, så du kan gå frem og tilbage mellem blokkene.")

# -------------------------
# RESULTAT
# -------------------------
elif st.session_state.page == "result":
    user_profile = st.session_state.answers.copy()
    raw_weights = st.session_state.weights.copy()
    group_weights = normalize_weights(raw_weights)

    st.title("🎓 Dit resultat")

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

    st.subheader("Din endelige profil (efter reverse-kodning og gennemsnit)")
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
