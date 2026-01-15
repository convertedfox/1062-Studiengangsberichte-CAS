from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from import_parser import StudyProgramRow, get_latest_import_year, load_latest_import_table


def main() -> None:
    st.set_page_config(
        page_title="Qualitaetsberichte Dashboard",
        page_icon="📊",
        layout="wide",
    )

    _inject_styles()

    data = load_latest_import_table()
    if not data:
        st.warning("Keine Studiengaenge im Import gefunden.")
        return

    import_year = get_latest_import_year()
    study_programs = sorted(row.studiengang for row in data)
    fachbereiche = _group_by_fachbereich(data)
    default_program = study_programs[0]
    selected = st.session_state.get("selected_program", default_program)
    with st.sidebar:
        st.markdown("### Auswahl")
        for fachbereich, programs in fachbereiche.items():
            with st.expander(fachbereich, expanded=True):
                for program in programs:
                    if st.button(program, use_container_width=True):
                        st.session_state["selected_program"] = program
                        selected = program
        st.caption("Quelle: neueste Datei im Ordner `data/`")
        if import_year:
            st.caption(f"Importjahr: {import_year}")

    row = next(item for item in data if item.studiengang == selected)

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">Qualitaetsberichte Dashboard</div>
            <div class="hero-subtitle">Studiengang im Fokus</div>
            <div class="hero-chip">Studiengang: <strong>{row.studiengang}</strong></div>
            <div class="hero-chip muted">Fachbereich: {row.fachbereich}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_student_metrics(row, import_year)
    _render_profile_sections(row)


def _render_student_metrics(row: StudyProgramRow, import_year: int | None) -> None:
    st.markdown('<div class="section-title">Studierendenzahlen</div>', unsafe_allow_html=True)
    cols = st.columns(2)

    with cols[0]:
        st.markdown('<div class="panel-title">Studienanfaenger (letzte 4 Jahre)</div>', unsafe_allow_html=True)
        _render_year_series(row.studienanfaenger, import_year)

    with cols[1]:
        st.markdown(
            '<div class="panel-title">Immatrikulierte Studierende (letzte 4 Jahre)</div>',
            unsafe_allow_html=True,
        )
        _render_year_series(row.immatrikulierte, import_year)

    _render_kpi_row(
        [
            ("Erfolgsquote", _format_percent(row.erfolgsquote)),
            ("Fachsemester", _format_number(row.fachsemester)),
            ("Berufserfahrung", _format_number(row.berufserfahrung)),
            ("Alter", _format_number(row.alter)),
        ]
    )

    st.markdown('<div class="section-title">Module</div>', unsafe_allow_html=True)
    _render_kpi_row(
        [
            ("Durchschnittliche Modulauslastung", _format_number(row.modulauslastung)),
            ("Anzahl Module", _format_number(row.anzahl_module)),
        ],
        columns=2,
    )


def _render_profile_sections(row: StudyProgramRow) -> None:
    st.markdown('<div class="section-title">Profile</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="panel-title">Vorstudium der Studienanfaenger</div>', unsafe_allow_html=True)
        _render_profile_table(row.vorstudium_profil)

        st.markdown(
            '<div class="panel-title">Dozentenherkunft (Lehrveranstaltungsstunden)</div>',
            unsafe_allow_html=True,
        )
        _render_profile_table(row.dozenten_herkunft_profil)

    with col_right:
        st.markdown(
            '<div class="panel-title">Modulbelegung nach Studiengaengen</div>',
            unsafe_allow_html=True,
        )
        _render_profile_table(row.module_belegung_nach_sg)

        st.markdown('<div class="panel-title">Herkunft der Modulteilnehmer</div>', unsafe_allow_html=True)
        _render_profile_table(row.modulteilnehmer_herkunft)


def _render_year_series(values: dict[str, int | None], import_year: int | None) -> None:
    offsets = ["-4", "-3", "-2", "-1"]
    if import_year:
        labels = [str(import_year + int(offset)) for offset in offsets]
    else:
        labels = offsets
    series = [values.get(offset) for offset in offsets]
    chart_data = pd.DataFrame({"Jahr": labels, "Wert": series})
    chart = (
        alt.Chart(chart_data)
        .mark_bar(color="#1DB954", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Jahr:N", axis=alt.Axis(labelAngle=0, labelColor="#b3b3b3", title=None)),
            y=alt.Y("Wert:Q", axis=alt.Axis(labelColor="#b3b3b3", title=None)),
            tooltip=["Jahr", "Wert"],
        )
        .properties(height=220)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(" / ".join(f"{label}: {_format_number(value)}" for label, value in zip(labels, series)))


def _render_profile_table(profile: dict[str, float | None]) -> None:
    if not profile:
        st.caption("Keine Daten vorhanden.")
        return
    rows = [
        {"Kategorie": key, "Wert": value}
        for key, value in profile.items()
        if value is not None
    ]
    if not rows:
        st.caption("Keine Daten vorhanden.")
        return

    data = pd.DataFrame(rows)
    base = (
        alt.Chart(data)
        .transform_joinaggregate(total="sum(Wert)")
        .transform_calculate(pct="datum.Wert / datum.total")
    )

    chart = (
        base.mark_arc(innerRadius=40, outerRadius=90)
        .encode(
            theta=alt.Theta("Wert:Q"),
            color=alt.Color(
                "Kategorie:N",
                scale=alt.Scale(
                    range=[
                        "#1DB954",
                        "#9FE9B6",
                        "#3DDC84",
                        "#2E8B57",
                        "#A7F3CE",
                        "#63D471",
                        "#2D6A4F",
                        "#77DFA3",
                    ]
                ),
                legend=alt.Legend(orient="right", labelColor="#b3b3b3", title=None),
            ),
            tooltip=[
                "Kategorie",
                alt.Tooltip("Wert:Q", format=".2f"),
                alt.Tooltip("pct:Q", format=".1%"),
            ],
        )
        .properties(height=260)
    )

    labels = (
        base.transform_filter("datum.pct > 0")
        .mark_text(radius=110, size=12, color="#f5f5f5")
        .encode(text=alt.Text("pct:Q", format=".0%"), theta=alt.Theta("Wert:Q"))
    )

    st.altair_chart(
        (chart + labels).configure_view(strokeOpacity=0),
        use_container_width=True,
    )


def _group_by_fachbereich(rows: list[StudyProgramRow]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        key = row.fachbereich or "Ohne Fachbereich"
        groups.setdefault(key, []).append(row.studiengang)
    return {key: sorted(values) for key, values in sorted(groups.items())}


def _render_kpi_row(items: list[tuple[str, str]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, (label, value) in enumerate(items):
        with cols[idx % columns]:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
        :root {
            --bg: #0f1110;
            --ink: #f5f5f5;
            --muted: #b3b3b3;
            --accent: #1db954;
            --accent-2: #9fe9b6;
            --card: #181a1b;
            --card-strong: #222524;
            --shadow: rgba(0, 0, 0, 0.35);
        }
        html, body, [class*="css"]  {
            font-family: "Space Grotesk", sans-serif;
        }
        .stApp {
            background: radial-gradient(circle at top left, #1a1d1c 0%, #0f1110 45%, #0a0b0b 100%);
        }
        .hero {
            padding: 28px 28px 22px 28px;
            border-radius: 18px;
            background: linear-gradient(120deg, #1b1e1d 0%, #121413 100%);
            box-shadow: 0 18px 45px var(--shadow);
            margin-bottom: 24px;
            animation: riseIn 0.6s ease-out;
        }
        .hero-title {
            font-size: 34px;
            font-weight: 700;
            color: var(--ink);
        }
        .hero-subtitle {
            color: var(--muted);
            margin-top: 6px;
            font-size: 15px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .hero-chip {
            display: inline-block;
            margin-top: 14px;
            margin-right: 10px;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(29, 185, 84, 0.18);
            color: var(--ink);
            font-weight: 600;
        }
        .hero-chip.muted {
            background: rgba(255, 255, 255, 0.08);
            color: var(--muted);
            font-weight: 500;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--accent-2);
            margin: 22px 0 12px 0;
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .kpi-card {
            background: var(--card);
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 10px 24px var(--shadow);
            min-height: 86px;
            animation: fadeIn 0.6s ease-out;
        }
        .kpi-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
        }
        .kpi-value {
            font-size: 26px;
            font-weight: 700;
            color: var(--ink);
            margin-top: 6px;
        }
        section[data-testid="stSidebar"] {
            background: #141716;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: var(--muted);
        }
        div[data-testid="stText"] {
            color: var(--muted);
        }
        div[data-testid="stMetric"] {
            background: var(--card-strong);
            border-radius: 14px;
            padding: 10px 12px;
        }
        @keyframes riseIn {
            from { transform: translateY(8px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        @keyframes fadeIn {
            from { transform: translateY(6px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


if __name__ == "__main__":
    main()
