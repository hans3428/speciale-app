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

    # Ledighed vendes om til jobsikkerhed
    if "Ledighed" in df.columns:
        df["Jobsikkerhed"] = 1 - df["Ledighed"]

    return df

LINE_DF = load_line_data(DATA_PATH)

GROUPS = {
    "Arbejdsmarked": {
        "Løn": {
            "question": "Jeg lægger vægt på, at mit fremtidige arbejde giver en høj løn",
            "column": "Løn",
        },
        "Jobsikkerhed": {
            "question": "Jeg lægger vægt på, at mit fremtidige arbejde giver høj jobsikkerhed",
            "column": "Jobsikkerhed",
        },
        "karakter_avg": {
            "question": "Jeg trives med høje faglige krav og et højt akademisk niveau",
            "column": "karakter_avg",
        },
    },
    "Studieform": {
        "Skriftlig": {
            "question": "Jeg foretrækker skriftlige eksamener frem for andre eksamensformer",
            "column": "Skriftlig",
        },
        "Individuel": {
            "question": "Jeg foretrækker at arbejde individuelt frem for i grupper",
            "column": "Individuel",
        },
        "timer_ects": {
            "question": "Jeg foretrækker en uddannelse med mange undervisningstimer og fast struktur",
            "column": "timer_ects",
        },
    },
    "Arbejdsstil – kognitiv/performance": {
        "Adaptability": {
            "question": "Jeg trives med forandringer og tilpasning til nye situationer",
            "column": "Adaptability",
        },
        "AttentiontoDetail": {
            "question": "Jeg arbejder grundigt og detaljeorienteret",
            "column": "AttentiontoDetail",
        },
        "Initiative": {
            "question": "Jeg tager ofte initiativ i opgaver og projekter",
            "column": "Initiative",
        },
    },
    "Arbejdsstil – social/ledelse": {
        "Integrity": {
            "question": "Det er vigtigt for mig at handle ansvarligt og i overensstemmelse med mine værdier",
            "column": "Integrity",
        },
        "Empathy": {
            "question": "Jeg er god til at forstå og tage hensyn til andre menneskers perspektiver",
            "column": "Empathy",
        },
        "LeadershipOrientation": {
            "question": "Jeg motiveres af at tage lederskab og sætte retning for andre",
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
        line_vals.append(sum(float(line_row[c]) for c in cols if c in line_row.index and pd.notna(line_row[c])) / len(cols))

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

st.title("🎓 Cand.merc.-linjematch")
st.write(
    "Svar på spørgsmålene, så beregner appen en personlig anbefaling baseret på dine præferencer, "
    "dine vægte og linjernes profiler i DATA.xlsx."
)

with st.expander("Model", expanded=False):
    st.latex(r"Score_j = \sum_k w_k \cdot (1 - |person_k - linje_{jk}|)")
    st.write(
        "Alle profilsvar omregnes fra 1–5 til 0–1. "
        "Vægtene angives løbende efter hver blok og normaliseres automatisk, så de summerer til 1."
    )

st.header("1. Spørgeskema")
st.markdown("**Profilskala:** 1 = Slet ikke, 2 = I lav grad, 3 = I nogen grad, 4 = I høj grad, 5 = I meget høj grad")
st.markdown("**Vægtskala:** 1 = Slet ikke vigtigt, 2 = Lidt vigtigt, 3 = Moderat vigtigt, 4 = Vigtigt, 5 = Meget vigtigt")

user_profile = {}
raw_weights = {}

for group_name, items in GROUPS.items():
    st.subheader(group_name)

    # 3 profilspørgsmål
    for key, spec in items.items():
        answer = st.slider(
            spec["question"],
            min_value=1,
            max_value=5,
            value=3,
            key=f"profile_{key}"
        )
        user_profile[spec["column"]] = response_to_zero_one(answer)

    # 1 vægtspørgsmål lige efter blokken
    raw_weights[group_name] = st.slider(
        WEIGHT_QUESTIONS[group_name],
        min_value=1,
        max_value=5,
        value=3,
        key=f"weight_{group_name}"
    )

    st.markdown("---")

group_weights = normalize_weights(raw_weights)

st.header("2. Dine vægte")
weights_df = pd.DataFrame({
    "Dimension": list(group_weights.keys()),
    "Rå score": [raw_weights[g] for g in group_weights],
    "Normaliseret vægt": [round(group_weights[g], 3) for g in group_weights],
})
st.dataframe(weights_df, use_container_width=True, hide_index=True)

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
