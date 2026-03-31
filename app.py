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

    # Ledighed omkodes til jobsikkerhed
    if "Ledighed" in df.columns:
        df["Jobsikkerhed"] = 1 - df["Ledighed"]

    return df


LINE_DF = load_line_data(DATA_PATH)

GROUPS = {
    "Arbejdsmarked": {
        "Løn": {
            "question": "Det er vigtigt for mig at have en højere løn end gennemsnittet for kandidater fra min årgang",
            "column": "Løn",
        },
        "Jobsikkerhed": {
            "question": "Det er vigtigt for mig at have lavere risiko for ledighed end gennemsnittet for kandidater fra min årgang",
            "column": "Jobsikkerhed",
        },
        "karakter_avg": {
            "question": "Det er vigtigt for mig at gå på en uddannelse, hvor studerende i gennemsnit opnår høje karakterer",
            "column": "karakter_avg",
        },
    },
    "Studieform": {
        "Skriftlig": {
            "question": "Jeg foretrækker uddannelser med en høj andel af skriftlige eksamener",
            "column": "Skriftlig",
        },
        "Individuel": {
            "question": "Jeg foretrækker uddannelser, hvor arbejde primært foregår individuelt frem for i grupper",
            "column": "Individuel",
        },
        "timer_ects": {
            "question": "Jeg foretrækker uddannelser med mange undervisningstimer pr. ECTS-point",
            "column": "timer_ects",
        },
    },
    "Arbejdsstil – kognitiv/performance": {
        "Adaptability": {
            "question": "Jeg foretrækker opgaver, hvor krav og rammer ændrer sig løbende",
            "column": "Adaptability",
        },
        "AttentiontoDetail": {
            "question": "Jeg foretrækker opgaver, hvor præcision og detaljer er afgørende",
            "column": "AttentiontoDetail",
        },
        "Initiative": {
            "question": "Jeg tager ofte selv initiativ til nye opgaver uden at blive bedt om det",
            "column": "Initiative",
        },
    },
    "Arbejdsstil – social/ledelse": {
        "Integrity": {
            "question": "Jeg lægger vægt på at overholde regler og aftaler i mit arbejde",
            "column": "Integrity",
        },
        "Empathy": {
            "question": "Jeg tager ofte hensyn til andres perspektiver i mit arbejde",
            "column": "Empathy",
        },
        "LeadershipOrientation": {
            "question": "Jeg motiveres af at tage ansvar for at lede og koordinere andre",
            "column": "LeadershipOrientation",
        },
    },
    "Faglige interesser": {
        "LawandGovernment": {
            "question": "Jeg interesserer mig for jura, regulering og offentlige forhold",
            "column": "LawandGovernment",
        },
        "Mathematics": {
            "question": "Jeg interesserer mig for matematik og kvantitative analyser",
            "column": "Mathematics",
        },
        "SalesandMarketing": {
            "question": "Jeg interesserer mig for marketing, salg og forbrugeradfærd",
            "column": "SalesandMarketing",
        },
    },
}

WEIGHT_QUESTIONS = {
    "Arbejdsmarked": "Hvor vigtigt er arbejdsmarked og karrieremuligheder for dig i valget af kandidatlinje?",
    "Studieform": "Hvor vigtigt er det for dig, at studieformen passer til dine præferencer?",
    "Arbejdsstil – kognitiv/performance": "Hvor vigtigt er det for dig, at linjen matcher din måde at arbejde og præstere på?",
    "Arbejdsstil – social/ledelse": "Hvor vigtigt er det for dig, at linjen matcher din sociale og ledelsesmæssige arbejdsstil?",
    "Faglige interesser": "Hvor vigtigt er det for dig, at linjen matcher dine faglige interesser?",
}

GROUP_ORDER = list(GROUPS.keys())


def response_to_zero_one(value: int) -> float:
    return (value - 1) / 4


def normalize_weights(raw_weights: dict) -> dict:
    total = sum(raw_weights.values())
    if total == 0:
        return {k: 1 / len(raw_weights) for k in raw_weights}
    return {k: v / total for k, v in raw_weights.items()}


def compute_group_match(user_profile: dict, line_row: pd.Series, group_name: str) -> float:
    specs = GROUPS[group_name]
    scores = []

    for spec in specs.values():
        col = spec["column"]

        if (
            col in user_profile
            and col in line_row.index
            and pd.notna(line_row[col])
        ):
            scores.append(1 - abs(user_profile[col] - float(line_row[col])))

    return sum(scores) / len(scores) if scores else 0.0


def compute_all_scores(user_profile: dict, group_weights: dict, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        group_matches = {group: compute_group_match(user_profile, row, group) for group in GROUPS}
        total_score = sum(group_weights[g] * group_matches[g] for g in GROUPS)
        out = {"Linje": row["Linje"], "Score": total_score}
        for group in GROUPS:
            out[f"Match_{group}"] = group_matches[group]
        rows.append(out)

    return pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)


def radar_figure(user_profile: dict, line_row: pd.Series) -> go.Figure:
    axis_labels = list(GROUPS.keys())
    user_vals = []
    line_vals = []

    for group in axis_labels:
        cols = [spec["column"] for spec in GROUPS[group].values()]

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


def reset_test():
    keys_to_delete = []
    for key in list(st.session_state.keys()):
        if key.startswith("profile_") or key.startswith("weight_"):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]

    st.session_state.page = "intro"
    st.session_state.step = 0


def is_group_answered(group_name: str) -> bool:
    items = GROUPS[group_name]
    profile_ok = all(st.session_state.get(f"profile_{key}") is not None for key in items.keys())
    weight_ok = st.session_state.get(f"weight_{group_name}") is not None
    return profile_ok and weight_ok


def build_user_profile() -> dict:
    user_profile = {}
    for group_name, items in GROUPS.items():
        for key, spec in items.items():
            answer = st.session_state.get(f"profile_{key}")
            if answer is not None:
                user_profile[spec["column"]] = response_to_zero_one(answer)
    return user_profile


def build_raw_weights() -> dict:
    raw_weights = {}
    for group_name in GROUPS.keys():
        raw_weights[group_name] = st.session_state.get(f"weight_{group_name}", 0) or 0
    return raw_weights


def all_profile_columns_present(user_profile: dict) -> bool:
    required_cols = [
        spec["column"]
        for group in GROUPS.values()
        for spec in group.values()
    ]
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
            "Vægtene normaliseres automatisk, så de samlet summerer til 1."
        )

    st.button("Start testen", type="primary", on_click=go_to_test)


# -------------------------
# TESTFLOW
# -------------------------
elif st.session_state.page == "test":
    current_group = GROUP_ORDER[st.session_state.step]
    current_items = GROUPS[current_group]

    st.title("🎓 Kandidatesten - Cand.merc.")
    st.caption(f"Trin {st.session_state.step + 1} af {len(GROUP_ORDER)}")

    progress_value = (st.session_state.step + 1) / len(GROUP_ORDER)
    st.progress(progress_value)

    st.header(current_group)

    st.markdown('<div class="step-box">', unsafe_allow_html=True)

    st.markdown("#### Profilspørgsmål")
    st.caption("Skala: 1 = Slet ikke · 2 = I lav grad · 3 = I nogen grad · 4 = I høj grad · 5 = I meget høj grad")

    for key, spec in current_items.items():
        st.radio(
            spec["question"],
            options=[1, 2, 3, 4, 5],
            horizontal=True,
            index=None,
            key=f"profile_{key}"
        )

    st.markdown("#### Vægtspørgsmål")
    st.caption("Hvor vigtigt er dette område samlet set for dig i valget af kandidatlinje?")

    st.radio(
        WEIGHT_QUESTIONS[current_group],
        options=[1, 2, 3, 4, 5],
        horizontal=True,
        index=None,
        key=f"weight_{current_group}"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        st.button("⬅ Tilbage", on_click=prev_step)

    with col2:
        if st.button("Videre ➜", type="primary"):
            if not is_group_answered(current_group):
                st.warning("Du skal besvare alle spørgsmål i denne blok, før du kan gå videre.")
            else:
                next_step()
                st.rerun()

    st.markdown("---")
    st.caption("Dine svar gemmes løbende, så du kan gå frem og tilbage mellem blokkene.")


# -------------------------
# RESULTAT
# -------------------------
elif st.session_state.page == "result":
    user_profile = build_user_profile()
    raw_weights = build_raw_weights()
    group_weights = normalize_weights(raw_weights)

    if not all_profile_columns_present(user_profile):
        st.error("Der mangler et eller flere profilsvar. Gå tilbage og gennemfør alle spørgsmål igen.")
        st.stop()

    scores = compute_all_scores(user_profile, group_weights, LINE_DF)

    st.title("🎓 Dit resultat")

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

    st.subheader("Alle linjer")
    st.dataframe(scores, use_container_width=True, hide_index=True)

    st.subheader("Eksempel på udfyldt formel på gruppeniveau")
    terms = [f"{group_weights[g]:.3f} × {top3.iloc[0][f'Match_{g}']:.3f}" for g in GROUPS]
    st.code(" + ".join(terms) + f" = {top3.iloc[0]['Score']:.3f}")

    c1, c2, c3 = st.columns([1, 1, 3])

    with c1:
        st.button(
            "⬅ Tilbage til spørgsmål",
            on_click=lambda: st.session_state.update({"page": "test", "step": len(GROUP_ORDER) - 1})
        )

    with c2:
        st.button("Start forfra", on_click=reset_test)

    st.download_button(
        "Download resultater som CSV",
        data=scores.to_csv(index=False).encode("utf-8"),
        file_name="linjematch_resultater.csv",
        mime="text/csv",
    )
