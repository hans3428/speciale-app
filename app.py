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
        if col in line_row.index and pd.notna(line_row[col]):
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
        user_vals.append(sum(user_profile[c] for c in cols) / len(cols))
        line_vals.append(
            sum(float(line_row[c]) for c in cols if c in line_row.index and pd.notna(line_row[c])) / len(cols)
        )

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


# -------------------------
# HEADER
# -------------------------
st.title("🎓 Kandidatesten - Cand.merc.")
st.write(
    "Svar på spørgsmålene, så beregner appen en personlig anbefaling baseret på dine præferencer, "
    "dine vægte og linjernes profiler. Værktøjet skal bruges som et støtteværktøj til dine personlige tanker."
)

with st.expander("Model", expanded=False):
    st.latex(r"Score_j = \sum_k w_k \cdot (1 - |person_k - linje_{jk}|)")
    st.write(
        "Alle profilsvar omregnes fra 1–5 til 0–1. "
        "Vægtene angives løbende efter hver blok og normaliseres automatisk, så de summerer til 1."
    )


# -------------------------
# SPØRGESKEMA
# -------------------------

user_profile = {}
raw_weights = {}

for group_name, items in GROUPS.items():
    # Stor gruppetitel
    st.header(group_name)

    # Profilspørgsmål
    st.markdown("#### Profilspørgsmål")
    st.caption("Skala: 1 = Slet ikke · 2 = I lav grad · 3 = I nogen grad · 4 = I høj grad · 5 = I meget høj grad")
    st.caption("Svar på hvor godt udsagnene passer på dig.")

    for key, spec in items.items():
        answer = st.slider(
            spec["question"],
            min_value=1,
            max_value=5,
            value=3,
            key=f"profile_{key}"
        )
        user_profile[spec["column"]] = response_to_zero_one(answer)

    # Vægtspørgsmål
    st.markdown("#### Vægtspørgsmål")
    st.caption("Skala: 1 = Slet ikke vigtigt · 2 = Lidt vigtigt · 3 = Moderat vigtigt · 4 = Vigtigt · 5 = Meget vigtigt")
    st.caption("Angiv hvor vigtigt dette område samlet set er for dig i valget af kandidatlinje.")

    raw_weights[group_name] = st.slider(
        WEIGHT_QUESTIONS[group_name],
        min_value=1,
        max_value=5,
        value=3,
        key=f"weight_{group_name}"
    )

    st.markdown("---")


# -------------------------
# VÆGTE
# -------------------------
group_weights = normalize_weights(raw_weights)

st.header("2. Dine vægte")
weights_df = pd.DataFrame({
    "Dimension": list(group_weights.keys()),
    "Rå score": [raw_weights[g] for g in group_weights],
    "Normaliseret vægt": [round(group_weights[g], 3) for g in group_weights],
})
st.dataframe(weights_df, use_container_width=True, hide_index=True)


# -------------------------
# RESULTAT
# -------------------------
if st.button("Beregn anbefaling", type="primary"):
    scores = compute_all_scores(user_profile, group_weights, LINE_DF)

    st.header("3. Resultat")
    top3 = scores.head(3)

    for idx, row in top3.iterrows():
        st.metric(label=f"Top {idx+1}: {row['Linje']}", value=f"{row['Score']:.3f}")

    st.subheader("Alle linjer")
    st.dataframe(scores, use_container_width=True, hide_index=True)

    best_name = top3.iloc[0]["Linje"]
    best_row = LINE_DF.loc[LINE_DF["Linje"] == best_name].iloc[0]

    st.subheader(f"Profilsammenligning: dig vs. {best_name}")
    st.plotly_chart(radar_figure(user_profile, best_row), use_container_width=True)

    st.subheader("Kort fortolkning")
    group_matches = {g: top3.iloc[0][f"Match_{g}"] for g in GROUPS}
    sorted_groups = sorted(group_matches.items(), key=lambda x: x[1], reverse=True)
    strengths = ", ".join(g for g, _ in sorted_groups[:2])
    weaker = ", ".join(g for g, _ in sorted_groups[-2:])
    st.write(
        f"Dit bedste match er **{best_name}**. Dine stærkeste matches ligger især inden for **{strengths}**, "
        f"mens de relativt svagere matches ligger inden for **{weaker}**."
    )

    st.subheader("Eksempel på udfyldt formel på gruppeniveau")
    terms = [f"{group_weights[g]:.3f} × {top3.iloc[0][f'Match_{g}']:.3f}" for g in GROUPS]
    st.code(" + ".join(terms) + f" = {top3.iloc[0]['Score']:.3f}")

    st.download_button(
        "Download resultater som CSV",
        data=scores.to_csv(index=False).encode("utf-8"),
        file_name="linjematch_resultater.csv",
        mime="text/csv",
    )
