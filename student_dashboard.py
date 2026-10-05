import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# ---------------------------------------------------------
# Student Marks Dashboard
# ---------------------------------------------------------

st.set_page_config(
    page_title="Student Marks Dashboard",
    page_icon="📊",
    layout="wide"
)

# The PDF has these columns. The PDF extractor can return
# the header text vertically, so we use clean column names.
COLUMNS = [
    "S.No",
    "Index",
    "Name",
    "Tamil",
    "English",
    "Sinhala",
    "Maths",
    "Science",
    "RC",
    "NRC",
    "Hinduism",
    "Islam",
    "History",
    "Geography",
    "Civics",
    "Art",
    "Drama",
    "Music",
    "PT",
    "ICT",
    "PTS",
]


def extract_students(pdf_file):
    """Extract student rows from the PDF table."""

    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # Skip the first row because the PDF header is
                # vertically arranged and difficult to extract cleanly.
                for row in table[1:]:
                    if not row or len(row) < 3:
                        continue

                    # Make sure the row looks like a student row.
                    sno = str(row[0]).strip() if row[0] else ""
                    index = str(row[1]).strip() if row[1] else ""
                    name = str(row[2]).strip() if row[2] else ""

                    if not re.fullmatch(r"\d+", sno):
                        continue

                    if not re.fullmatch(r"\d+", index):
                        continue

                    if not name:
                        continue

                    # Make exactly 21 columns.
                    row = list(row[:21])
                    while len(row) < 21:
                        row.append("")

                    cleaned = []
                    for value in row:
                        if value is None:
                            cleaned.append("")
                        else:
                            cleaned.append(str(value).strip())

                    rows.append(cleaned)

    if not rows:
        raise ValueError("No student table was found in the PDF.")

    df = pd.DataFrame(rows, columns=COLUMNS)

    return df


def numeric(value):
    """Convert a mark to a number; return None for AB/blank."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def student_summary(student):
    """Create a summary of one student's marks."""

    # These are actual subject columns in the PDF.
    subject_columns = [
        "Tamil",
        "English",
        "Sinhala",
        "Maths",
        "Science",
        "RC",
        "NRC",
        "Hinduism",
        "Islam",
        "History",
        "Geography",
        "Civics",
        "Art",
        "Drama",
        "Music",
        "PT",
        "ICT",
    ]

    marks = []
    for subject in subject_columns:
        value = numeric(student[subject])
        if value is not None:
            marks.append((subject, value))

    if marks:
        total = sum(mark for _, mark in marks)
        average = total / len(marks)
    else:
        total = 0
        average = 0

    return len(marks), total, average


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.title("📊 Student Marks Dashboard")
st.caption("Search a student using the Index Number.")

uploaded_file = st.file_uploader(
    "Upload the student marks PDF",
    type=["pdf"]
)

if uploaded_file is None:
    st.info("Upload the PDF containing the student marks to begin.")
    st.stop()

try:
    df = extract_students(BytesIO(uploaded_file.getvalue()))
except Exception as e:
    st.error(f"Could not read the PDF: {e}")
    st.stop()

# Make Index searchable as text.
df["Index"] = df["Index"].astype(str)

st.success(f"Loaded {len(df)} students.")

# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

index = st.text_input(
    "Enter Student Index Number",
    placeholder="Example: 7163"
).strip()

if index:
    result = df[df["Index"] == index]

    if result.empty:
        st.error(f"No student found with index number: {index}")

    else:
        student = result.iloc[0]

        st.subheader("Student Details")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Index", student["Index"])

        with col2:
            st.metric("Student Name", student["Name"])

        with col3:
            subject_count, total, average = student_summary(student)
            st.metric("Average", f"{average:.2f}")

        st.divider()

        # Subject marks
        st.subheader("Subject Marks")

        subject_columns = [
            "Tamil",
            "English",
            "Sinhala",
            "Maths",
            "Science",
            "RC",
            "NRC",
            "Hinduism",
            "Islam",
            "History",
            "Geography",
            "Civics",
            "Art",
            "Drama",
            "Music",
            "PT",
            "ICT",
            "PTS",
        ]

        marks_data = []

        for subject in subject_columns:
            value = student[subject]

            if value != "":
                marks_data.append({
                    "Subject": subject,
                    "Mark": value
                })

        marks_df = pd.DataFrame(marks_data)

        st.dataframe(
            marks_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Full original row
        with st.expander("Show all recorded details"):
            full_details = pd.DataFrame(
                [student],
                columns=COLUMNS
            ).T

            full_details.columns = ["Value"]

            st.dataframe(
                full_details,
                use_container_width=True
            )

else:
    st.subheader("Student List")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.info("Enter an Index Number above to view one student's details.")

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("Dashboard")

    st.write(f"**Students:** {len(df)}")

    st.write(
        "**Search:** Enter the student's Index Number "
        "in the search box."
    )

    st.divider()

    st.write("### PDF Information")

    st.write(
        "This dashboard reads the student table directly "
        "from the uploaded PDF."
    )
