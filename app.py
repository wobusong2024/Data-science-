from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st


# ------------------------------------------------------------
# 1. PAGE STYLE AND COLOURS
# ------------------------------------------------------------
st.set_page_config(
    page_title="Student Screen Time Dashboard",
    layout="wide"
)

NAVY = "#173B45"
TEAL = "#247A78"
MINT = "#83B9AE"
GOLD = "#D5A04A"
TEXT = "#344B50"
BACKGROUND = "#F3F7F7"
WHITE = "#FFFFFF"

sns.set_theme(style="whitegrid")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }}

    [data-testid="stSidebar"] {{
        background-color: #EAF1F1;
        border-right: 1px solid #D5E0E0;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.4rem;
    }}

    [data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        border-radius: 8px;
        border-color: #B9CCCC;
        background-color: white;
    }}

    div[data-testid="stMetric"] {{
        background-color: {WHITE};
        border: 1px solid #DCE6E5;
        padding: 13px;
        border-radius: 10px;
    }}

    h1, h2, h3 {{
        color: {NAVY};
    }}

    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: {NAVY};
        border-bottom-color: {TEAL};
        font-weight: 700;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# 2. SURVEY COLUMN NAMES
# ------------------------------------------------------------
GROUP_COL = "Are you currently a school or college student?"
GENDER_COL = "What is your gender?"
DAILY_COL = "On a normal day, about how much time do you spend using digital devices?"
PURPOSE_COL = "What do you mainly use your digital devices for?"
SCORE_COL = "What was your most recent overall academic score or percentage?"

ACTIVITY_COLUMNS = {
    "Studying or learning":
        "About how much time do you spend using digital devices for studying or learning each day?",
    "Social media":
        "About how much time do you spend on social media each day?",
    "Gaming":
        "About how much time do you spend playing games on digital devices each day?",
    "Entertainment":
        "About how much time do you spend watching videos, movies, or other entertainment each day?",
}

REQUIRED_COLUMNS = [
    GROUP_COL,
    GENDER_COL,
    DAILY_COL,
    PURPOSE_COL,
    SCORE_COL,
    *ACTIVITY_COLUMNS.values(),
]


# ------------------------------------------------------------
# 3. RESPONSE RANGES
# ------------------------------------------------------------
DAILY_HOURS = {
    "Less than 1 hour": 0.5,
    "1–2 hours": 1.5,
    "2–3 hours": 2.5,
    "3–4 hours": 3.5,
    "4–5 hours": 4.5,
    "5–6 hours": 5.5,
    "More than 6 hours": 6.5,
}

DAILY_ORDER = list(DAILY_HOURS.keys())

ACTIVITY_HOURS = {
    "Studying or learning": {
        "Less than 1 hour": 0.5,
        "1–2 hours": 1.5,
        "2–3 hours": 2.5,
        "3–4 hours": 3.5,
        "More than 4 hours": 4.5,
    },
    "Social media": {
        "I do not use social media": 0,
        "Less than 30 minutes": 0.25,
        "30 minutes–1 hour": 0.75,
        "1–2 hours": 1.5,
        "2–3 hours": 2.5,
        "More than 3 hours": 3.5,
    },
    "Gaming": {
        "I do not play games": 0,
        "Less than 30 minutes": 0.25,
        "30 minutes–1 hour": 0.75,
        "1–2 hours": 1.5,
        "2–3 hours": 2.5,
        "More than 3 hours": 3.5,
    },
    "Entertainment": {
        "I do not spend time on entertainment": 0,
        "Less than 30 minutes": 0.25,
        "1–2 hours": 1.5,
        "2–3 hours": 2.5,
        "More than 3 hours": 3.5,
    },
}

SCORE_MIDPOINTS = {
    "Below 40%": 35,
    "40–49%": 45,
    "50–59%": 55,
    "60–69%": 65,
    "70–79%": 75,
    "80–89%": 85,
    "90–100%": 95,
}


# ------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ------------------------------------------------------------
def tidy_name(name):
    """Remove extra spaces and line breaks from column headings."""
    return re.sub(r"\s+", " ", str(name)).strip()


def one_answer(series):
    """
    Keep answers with one option.
    Exclude answers with multiple options separated by a semicolon
    from calculations that require one answer.
    """
    values = series.astype("string").str.strip()
    has_multiple_answers = values.str.contains(";", na=False)
    return values.mask(has_multiple_answers)


def show_explanation(message):
    """Show a short explanation below a chart."""
    st.markdown(
        f"""
        <div style="
            background:#E8F1EF;
            border-left:4px solid {TEAL};
            padding:11px 14px;
            border-radius:6px;
            margin:6px 0 17px 0;
            color:{NAVY};">
            <b>How to understand this:</b> {message}
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# 5. DASHBOARD TITLE AND CSV UPLOAD
# ------------------------------------------------------------
st.markdown(
    f"""
    <div style="
        background:{NAVY};
        padding:22px 25px;
        border-radius:12px;
        color:white;
        margin-bottom:18px;">
        <div style="font-size:12px;letter-spacing:1px;">
            INTERACTIVE SURVEY DASHBOARD
        </div>
        <div style="font-size:27px;font-weight:700;margin-top:6px;">
            Student Screen Time and Academic Performance
        </div>
        <div style="font-size:15px;margin-top:7px;color:#E4EEEE;">
            Explore screen-time patterns among school and college students.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

survey_path = Path(__file__).resolve().with_name("survey_data.csv")
try:
    raw = pd.read_csv(survey_path)
except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
    st.error("The survey data could not be loaded. Check that survey_data.csv is beside app.py.")
    st.stop()

raw.columns = [tidy_name(column) for column in raw.columns]

missing_columns = [
    column for column in REQUIRED_COLUMNS
    if column not in raw.columns
]

if missing_columns:
    st.error(
        "Some survey columns were not found. Please upload the correct CSV file."
    )
    st.write("Columns not found:", missing_columns)
    st.stop()


# ------------------------------------------------------------
# 6. CLEAN THE DATA
# ------------------------------------------------------------
rows_before_cleaning = len(raw)
duplicates_found = int(raw.duplicated().sum())

# Keep the original survey columns for the missing-value report.
source_columns = raw.columns.tolist()

# Remove exact duplicate rows.
df = raw.drop_duplicates().copy()

# Remove extra spaces from text answers.
for column in df.select_dtypes(include=["object", "string"]).columns:
    df[column] = df[column].astype("string").str.strip()

# Make single-answer versions of the main responses.
df["Daily screen-time answer"] = one_answer(df[DAILY_COL])
df["Academic score answer"] = one_answer(df[SCORE_COL])

# Estimate hours and scores using the midpoint of each range.
df["Estimated daily screen hours"] = (
    df["Daily screen-time answer"].map(DAILY_HOURS)
)
df["Estimated academic score"] = (
    df["Academic score answer"].map(SCORE_MIDPOINTS)
)

for activity, column in ACTIVITY_COLUMNS.items():
    answer_column = f"{activity} answer"
    hours_column = f"{activity} estimated hours"

    df[answer_column] = one_answer(df[column])
    df[hours_column] = df[answer_column].map(ACTIVITY_HOURS[activity])


# ------------------------------------------------------------
# 7. SIDEBAR DROPDOWNS
# ------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="
        color:{NAVY};
        padding:4px 2px 12px 2px;
        border-bottom:1px solid #CAD8D8;
        margin-bottom:14px;">
        <div style="font-size:19px;font-weight:700;">
            Dashboard filters
        </div>
        <div style="font-size:13px;color:{TEXT};margin-top:5px;">
            Choose a group and an activity to explore.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

dashboard_options = [
    "School students",
    "College students",
    "Compare both groups",
]

selected_view = st.sidebar.selectbox(
    "Choose student group",
    dashboard_options
)

activity_options = list(ACTIVITY_COLUMNS.keys())

selected_activity = st.sidebar.selectbox(
    "Choose an activity",
    activity_options
)

st.sidebar.caption(
    "Changing these dropdowns updates the dashboard results."
)

if selected_view == "School students":
    selected_groups = ["School student"]
    dashboard_title = "School Student Screen Time Dashboard"
elif selected_view == "College students":
    selected_groups = ["College student"]
    dashboard_title = "College Student Screen Time Dashboard"
else:
    selected_groups = ["School student", "College student"]
    dashboard_title = "School and College Student Comparison Dashboard"

view = df[df[GROUP_COL].isin(selected_groups)].copy()

if view.empty:
    st.warning("No responses were found for this selection.")
    st.stop()

st.title(dashboard_title)
st.caption(
    "Use the tabs below to explore screen time, activities, gender, "
    "and academic performance."
)


# ------------------------------------------------------------
# 8. SUMMARY CARDS
# ------------------------------------------------------------
valid_daily = view.dropna(subset=["Estimated daily screen hours"])
common_range = view["Daily screen-time answer"].mode()

if selected_view == "Compare both groups":
    school_total = int((view[GROUP_COL] == "School student").sum())
    college_total = int((view[GROUP_COL] == "College student").sum())
    participant_label = "School / college participants"
    participant_value = f"{school_total} / {college_total}"
else:
    participant_label = "Participants"
    participant_value = f"{len(view):,}"

card1, card2, card3, card4 = st.columns(4)

card1.metric(participant_label, participant_value)
card2.metric("Responses in this view", f"{len(view):,}")

if len(valid_daily):
    card3.metric(
        "Estimated average screen time",
        f"{valid_daily['Estimated daily screen hours'].mean():.1f} hours/day"
    )
else:
    card3.metric("Estimated average screen time", "Not available")

card4.metric(
    "Most common screen-time range",
    common_range.iloc[0] if len(common_range) else "Not available"
)


# ------------------------------------------------------------
# 9. DASHBOARD TABS
# ------------------------------------------------------------
daily_tab, activity_tab, gender_tab, grades_tab, data_tab = st.tabs(
    [
        "Daily Screen Time",
        "Screen Activities",
        "Gender",
        "Academic Performance",
        "Data Quality",
    ]
)


# ------------------------------------------------------------
# DAILY SCREEN TIME
# ------------------------------------------------------------
with daily_tab:
    st.subheader("How much time do students spend on screens each day?")
    st.write(
        "This chart shows the percentage of students in each screen-time range."
    )

    daily_data = view.dropna(subset=["Daily screen-time answer"])

    if daily_data.empty:
        st.info("There are no single-answer screen-time responses to show.")
    else:
        groups_in_view = [
            group for group in ["School student", "College student"]
            if group in daily_data[GROUP_COL].unique()
        ]

        fig, ax = plt.subplots(figsize=(7.5, 3.3))
        x_positions = np.arange(len(DAILY_ORDER))
        group_colors = {
            "School student": TEAL,
            "College student": GOLD,
        }

        for index, group in enumerate(groups_in_view):
            group_data = daily_data[daily_data[GROUP_COL] == group]

            percentages = (
                group_data["Daily screen-time answer"]
                .value_counts(normalize=True)
                .reindex(DAILY_ORDER, fill_value=0)
                .values * 100
            )

            if len(groups_in_view) == 1:
                positions = x_positions
                bar_width = 0.62
            else:
                bar_width = 0.36
                positions = x_positions + (index - 0.5) * bar_width

            ax.bar(
                positions,
                percentages,
                width=bar_width,
                label=group,
                color=group_colors[group],
                edgecolor="white"
            )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(DAILY_ORDER, rotation=20, ha="right")
        ax.set_ylabel("Students (%)")
        ax.set_xlabel("Reported daily screen time")
        ax.set_title("Daily Screen-Time Responses", color=NAVY)
        ax.legend(title="Student group", frameon=False)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        most_common = daily_data["Daily screen-time answer"].mode()

        if len(most_common):
            show_explanation(
                f"The most frequently selected range is "
                f"<b>{most_common.iloc[0]}</b>. This is the most common answer, "
                f"not the average screen time."
            )


# ------------------------------------------------------------
# SCREEN ACTIVITIES
# ------------------------------------------------------------
with activity_tab:
    st.subheader("Which screen activities are most common?")
    st.write(
        "Students could select more than one device use. "
        "The percentages may add up to more than 100%."
    )

    purpose_counts = {}

    for answer in view[PURPOSE_COL].dropna():
        for purpose in str(answer).split(";"):
            purpose = purpose.strip()
            if purpose:
                purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

    if purpose_counts:
        purpose_table = pd.DataFrame(
            list(purpose_counts.items()),
            columns=["Activity", "Number of selections"]
        )
        purpose_table["Percent of participants"] = (
            purpose_table["Number of selections"] / len(view) * 100
        )
        purpose_table = purpose_table.sort_values(
            "Percent of participants",
            ascending=True
        )

        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.barh(
            purpose_table["Activity"],
            purpose_table["Percent of participants"],
            color=TEAL
        )
        ax.set_xlabel("Participants selecting this activity (%)")
        ax.set_title("Main Uses of Digital Devices", color=NAVY)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        top_activity = purpose_table.iloc[-1]

        show_explanation(
            f"<b>{top_activity['Activity']}</b> was selected by the largest "
            f"share of participants: "
            f"<b>{top_activity['Percent of participants']:.1f}%</b>."
        )

    st.divider()
    st.subheader(f"Time spent on {selected_activity.lower()}")
    st.write(
        "Use the activity dropdown in the sidebar to view a different activity."
    )

    activity_answer_column = f"{selected_activity} answer"
    activity_counts = view[activity_answer_column].value_counts()

    if len(activity_counts):
        fig, ax = plt.subplots(figsize=(7.2, 3.1))
        ax.bar(
            activity_counts.index.astype(str),
            activity_counts.values,
            color=MINT,
            edgecolor="white"
        )
        ax.set_ylabel("Number of students")
        ax.set_xlabel("Reported time range")
        ax.set_title(f"Reported Time: {selected_activity}", color=NAVY)
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        show_explanation(
            f"The most common response for {selected_activity.lower()} is "
            f"<b>{activity_counts.index[0]}</b>."
        )
    else:
        st.info("There are not enough single-answer responses for this activity.")


# ------------------------------------------------------------
# SCREEN TIME BY GENDER
# ------------------------------------------------------------
with gender_tab:
    st.subheader("Does screen time differ by gender?")
    st.write(
        "This chart estimates daily hours from the middle of each reported range."
    )

    gender_data = view.dropna(
        subset=["Estimated daily screen hours", GENDER_COL]
    )

    if gender_data.empty:
        st.info("There are not enough responses for this comparison.")
    else:
        gender_summary = (
            gender_data.groupby([GROUP_COL, GENDER_COL])[
                "Estimated daily screen hours"
            ]
            .mean()
            .reset_index()
        )

        groups_in_view = [
            group for group in ["School student", "College student"]
            if group in gender_summary[GROUP_COL].unique()
        ]
        genders_in_view = [
            gender for gender in ["Female", "Male", "Others"]
            if gender in gender_summary[GENDER_COL].unique()
        ]

        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        x_positions = np.arange(len(genders_in_view))
        group_colors = {
            "School student": TEAL,
            "College student": GOLD,
        }

        if len(groups_in_view) == 1:
            group = groups_in_view[0]
            current = gender_summary[gender_summary[GROUP_COL] == group]

            values = [
                current.loc[current[GENDER_COL] == gender,
                            "Estimated daily screen hours"].iloc[0]
                if (current[GENDER_COL] == gender).any()
                else 0
                for gender in genders_in_view
            ]

            ax.bar(
                x_positions,
                values,
                width=0.58,
                color=TEAL
            )
        else:
            width = 0.36

            for index, group in enumerate(groups_in_view):
                current = gender_summary[gender_summary[GROUP_COL] == group]

                values = [
                    current.loc[current[GENDER_COL] == gender,
                                "Estimated daily screen hours"].iloc[0]
                    if (current[GENDER_COL] == gender).any()
                    else 0
                    for gender in genders_in_view
                ]

                ax.bar(
                    x_positions + (index - 0.5) * width,
                    values,
                    width=width,
                    label=group,
                    color=group_colors[group]
                )

            ax.legend(title="Student group", frameon=False)

        ax.set_xticks(x_positions)
        ax.set_xticklabels(genders_in_view)
        ax.set_ylabel("Estimated hours per day")
        ax.set_title("Estimated Screen Time by Gender", color=NAVY)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        display_gender = gender_summary.rename(
            columns={
                GROUP_COL: "Student group",
                GENDER_COL: "Gender",
                "Estimated daily screen hours": "Estimated average hours/day",
            }
        )

        st.dataframe(
            display_gender.round(2),
            use_container_width=True,
            hide_index=True
        )

        female_mean = gender_summary.loc[
            gender_summary[GENDER_COL] == "Female",
            "Estimated daily screen hours"
        ].mean()

        male_mean = gender_summary.loc[
            gender_summary[GENDER_COL] == "Male",
            "Estimated daily screen hours"
        ].mean()

        if pd.notna(female_mean) and pd.notna(male_mean):
            if female_mean > male_mean:
                gender_result = "Female respondents have the higher estimated average."
            elif male_mean > female_mean:
                gender_result = "Male respondents have the higher estimated average."
            else:
                gender_result = "Female and male respondents have the same estimated average."

            show_explanation(
                f"{gender_result} Female: <b>{female_mean:.1f} hours/day</b>; "
                f"male: <b>{male_mean:.1f} hours/day</b>."
            )


# ------------------------------------------------------------
# SCREEN TIME AND ACADEMIC PERFORMANCE
# ------------------------------------------------------------
with grades_tab:
    st.subheader("How is screen time related to academic performance?")
    st.write(
        "The chart shows average score estimates for each daily screen-time range."
    )

    score_data = view.dropna(
        subset=["Daily screen-time answer", "Estimated academic score"]
    )

    if score_data.empty:
        st.info("There are not enough single-answer screen-time and score responses.")
    else:
        short_labels = {
            "Less than 1 hour": "<1",
            "1–2 hours": "1–2",
            "2–3 hours": "2–3",
            "3–4 hours": "3–4",
            "4–5 hours": "4–5",
            "5–6 hours": "5–6",
            "More than 6 hours": ">6",
        }

        def draw_score_chart(group_name, bar_color):
            group_data = score_data[score_data[GROUP_COL] == group_name]

            average_scores = (
                group_data.groupby("Daily screen-time answer")[
                    "Estimated academic score"
                ]
                .mean()
                .reindex(DAILY_ORDER)
            )

            fig, ax = plt.subplots(figsize=(5.2, 3.3))

            ax.bar(
                [short_labels[label] for label in DAILY_ORDER],
                average_scores.values,
                color=bar_color,
                width=0.65
            )

            ax.set_title(
                f"{group_name} (n={len(group_data)})",
                color=NAVY,
                fontsize=11
            )
            ax.set_xlabel("Daily screen time")
            ax.set_ylabel("Approximate score (%)")
            ax.set_ylim(0, 100)
            ax.tick_params(axis="x", labelsize=9)
            ax.grid(axis="x", visible=False)

            fig.tight_layout()
            st.pyplot(fig, use_container_width=False)
            plt.close(fig)

        if selected_view == "Compare both groups":
            school_chart, college_chart = st.columns(2)

            with school_chart:
                draw_score_chart("School student", TEAL)

            with college_chart:
                draw_score_chart("College student", GOLD)
        else:
            draw_score_chart(selected_groups[0], TEAL)

        show_explanation(
            "Each chart shows the estimated average score for each screen-time range. "
            "The short labels mean hours: for example, “1–2” means 1–2 hours. "
            "Compare the school and college charts separately. This shows a relationship "
            "in the survey data, not proof that screen time causes a change in grades."
        )

    st.divider()
    st.subheader("Which screen-time patterns are associated with scores?")
    st.write(
        "This table describes whether higher reported time tends to appear "
        "with higher or lower score estimates."
    )

    pattern_columns = {
        "Total daily screen time": "Estimated daily screen hours",
        "Study / learning screen time": "Studying or learning estimated hours",
        "Social media time": "Social media estimated hours",
        "Gaming time": "Gaming estimated hours",
        "Entertainment time": "Entertainment estimated hours",
    }

    relationship_rows = []

    for pattern, hours_column in pattern_columns.items():
        subset = view.dropna(
            subset=[hours_column, "Estimated academic score"]
        )

        if len(subset) >= 3 and subset[hours_column].nunique() > 1:
            correlation = subset[hours_column].corr(
                subset["Estimated academic score"],
                method="spearman"
            )

            if pd.notna(correlation):
                if correlation > 0.05:
                    direction = "Higher time tends to appear with higher scores"
                elif correlation < -0.05:
                    direction = "Higher time tends to appear with lower scores"
                else:
                    direction = "No clear pattern"

                relationship_rows.append({
                    "Screen-time pattern": pattern,
                    "Responses used": len(subset),
                    "Observed pattern": direction,
                    "Relationship value": correlation,
                })

    if relationship_rows:
        relationship_table = pd.DataFrame(relationship_rows)

        st.dataframe(
            relationship_table.style.format({
                "Relationship value": "{:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Relationship values near zero mean little pattern; values farther "
            "from zero mean a clearer pattern. These results do not prove cause and effect."
        )
    else:
        st.info("There are not enough complete responses to calculate these patterns.")


# ------------------------------------------------------------
# DATA QUALITY
# ------------------------------------------------------------
with data_tab:
    st.subheader("How the survey data was prepared")

    data_card1, data_card2, data_card3 = st.columns(3)

    data_card1.metric(
        "Rows before cleaning",
        f"{rows_before_cleaning:,}"
    )
    data_card2.metric(
        "Exact duplicates removed",
        f"{duplicates_found:,}"
    )
    data_card3.metric(
        "Participants after cleaning",
        f"{len(df):,}"
    )

    st.write(
        "Missing responses are left blank. They are not filled with guessed values. "
        "Answers with multiple selected options are excluded only from analyses "
        "that need one answer."
    )

    missing_summary = (
        df[source_columns]
        .isna()
        .sum()
        .rename("Missing responses")
        .reset_index()
        .rename(columns={"index": "Survey column"})
    )

    missing_summary = missing_summary[
        missing_summary["Missing responses"] > 0
    ]

    if len(missing_summary):
        st.write("Survey columns with missing responses:")
        st.dataframe(
            missing_summary,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No missing responses were found after duplicate removal.")

# ------------------------------------------------------------
# NOTE ABOUT ESTIMATES
# ------------------------------------------------------------
st.caption(
    "Estimated hours use the middle of each time range. For example, "
    "“2–3 hours” is represented as 2.5 hours. Answers with multiple ranges "
    "are excluded from single-answer calculations."
)
