from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from import_parser import StudyProgramRow, get_latest_import_year, load_latest_import_table


def main() -> None:
    st.set_page_config(
        page_title="Studiengangskennzahlen Dashboard",
        page_icon="📊",
        layout="wide",
    )

    _inject_styles()

    data = load_latest_import_table()
    if not data:
        st.warning("Keine Studiengänge im Import gefunden.")
        return

    import_year = get_latest_import_year()
    fachbereiche = _group_by_fachbereich(data)
    fachbereich_by_program = {row.studiengang: row.fachbereich for row in data}
    if "selected_program" not in st.session_state:
        first_fachbereich = next(iter(fachbereiche))
        st.session_state["selected_program"] = fachbereiche[first_fachbereich][0]
    selected = st.session_state["selected_program"]
    selected_fachbereich = fachbereich_by_program.get(selected, "")

    with st.sidebar:
        st.markdown("### Auswahl")
        for fachbereich, programs in fachbereiche.items():
            st.markdown(_fachbereich_header(fachbereich), unsafe_allow_html=True)
            for program in programs:
                if program == selected:
                    st.markdown(f"- **{program}**")
                else:
                    st.button(
                        program,
                        key=f"program-{fachbereich}-{program}",
                        use_container_width=True,
                        on_click=_select_program,
                        args=(program,),
                    )
        st.markdown("### Info")
        st.caption("Quelle: neueste Datei im Ordner `data/`")
        if import_year:
            st.caption(f"Importjahr: {import_year}")

    row = next(item for item in data if item.studiengang == selected)

    st.title("Studiengangskennzahlen DHBW CAS")
    st.subheader(row.studiengang)
    st.caption(f"Fachbereich: {row.fachbereich}")

    _render_student_metrics(row, import_year)
    _render_profile_sections(row)


def _render_student_metrics(row: StudyProgramRow, import_year: int | None) -> None:
    _section_title("Studierendenzahlen")
    cols = st.columns(2)

    with cols[0]:
        st.markdown('<div class="panel-title">Studienanfänger(innen) (letzte 4 Jahre)</div>', unsafe_allow_html=True)
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
            ("Ø benötigte Anzahl an Fachsemestern", _format_number(row.fachsemester)),
            ("Ø Berufserfahrung zu Studienbeginn in Jahren", _format_number(row.berufserfahrung)),
            ("Ø Alter zu Studienbeginn in Jahren", _format_number(row.alter)),
        ]
    )

    _section_title("Module")
    _render_kpi_row(
        [
            ("Durchschnittliche Modulauslastung", _format_number(row.modulauslastung)),
            ("Anzahl Module", _format_number(row.anzahl_module)),
        ],
        columns=2,
    )


def _render_profile_sections(row: StudyProgramRow) -> None:
    _section_title("Profile")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="panel-title">Vorstudium der Studienanfänger(innen)</div>', unsafe_allow_html=True)
        _render_profile_table(row.vorstudium_profil)

        st.markdown(
            '<div class="panel-title">Dozentenherkunft (Lehrveranstaltungsstunden)</div>',
            unsafe_allow_html=True,
        )
        _render_profile_table(row.dozenten_herkunft_profil)

    with col_right:
        st.markdown('<div class="panel-title">Modulbelegung nach Studiengängen</div>', unsafe_allow_html=True)
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
        .mark_bar(color="#E2001A", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Jahr:N", axis=alt.Axis(labelAngle=0, labelColor="#000000", titleColor="#000000", title=None)),
            y=alt.Y("Wert:Q", axis=alt.Axis(labelColor="#000000", titleColor="#000000", title=None)),
            tooltip=["Jahr", "Wert"],
        )
        .properties(height=220)
        .configure_view(strokeOpacity=0, fill="#FFFFFF")
        .configure(background="#FFFFFF")
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
    data["Wert"] = pd.to_numeric(data["Wert"], errors="coerce")
    data = data[data["Wert"].fillna(0) > 0]
    if data.empty:
        st.caption("Keine Daten vorhanden.")
        return
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
                legend=alt.Legend(orient="right", title=None, labelColor="#000000"),
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
        .mark_text(radius=110, size=12, color="#FFFFFF")
        .encode(text=alt.Text("pct:Q", format=".0%"), theta=alt.Theta("Wert:Q"))
    )

    st.altair_chart(
        (chart + labels)
        .configure_view(strokeOpacity=0, fill="#FFFFFF")
        .configure(background="#FFFFFF"),
        use_container_width=True,
    )


def _select_program(program: str) -> None:
    st.session_state["selected_program"] = program


def _group_by_fachbereich(rows: list[StudyProgramRow]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        key = row.fachbereich or "Ohne Fachbereich"
        groups.setdefault(key, []).append(row.studiengang)
    return {key: sorted(values) for key, values in sorted(groups.items())}


def _fachbereich_header(fachbereich: str) -> str:
    colors = {
        "Technik": "#4192AB",
        "Wirtschaft": "#003966",
        "Sozialwesen": "#9B0B33",
        "Gesundheit": "#3DCC00",
    }
    color = colors.get(fachbereich, "#5C6971")
    return (
        f'<div class="fachbereich-chip" style="background: {color};">'
        f"{fachbereich}</div>"
    )


def _section_title(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


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
        :root {
            --dhbw-primary: #3D4548;
            --dhbw-secondary: #5C6971;
            --dhbw-accent: #E2001A;
            --dhbw-secondary-75: rgba(92, 105, 113, 0.75);
            --dhbw-secondary-50: rgba(92, 105, 113, 0.5);
            --dhbw-secondary-25: rgba(92, 105, 113, 0.25);
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #000000;
            padding-bottom: 6px;
            border-bottom: 2px solid var(--dhbw-accent);
            margin: 20px 0 12px 0;
        }
        .panel-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #000000;
            margin-bottom: 6px;
        }
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid var(--dhbw-secondary-50);
            border-radius: 8px;
            padding: 10px 12px;
        }
        .kpi-label {
            color: #000000;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            color: #000000;
            font-size: 1.4rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .stApp,
        .stMarkdown,
        .stText,
        .stCaption,
        .stSubheader,
        .stHeader,
        .stTitle,
        label,
        p,
        span {
            color: #000000;
        }
        .stApp,
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
        }
        section[data-testid="stSidebar"] .stButton button {
            background-color: #FFFFFF;
            border: 1px solid var(--dhbw-secondary-50);
            color: #000000;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            border-color: var(--dhbw-secondary-75);
        }
        header,
        [data-testid="stHeader"] {
            background-color: #FFFFFF;
        }
        div[data-testid="stVegaLiteChart"] {
            background: #FFFFFF;
            border: 1px solid var(--dhbw-secondary-50);
            border-radius: 8px;
            padding: 8px;
        }
        div[data-testid="stDataFrame"] {
            background: #FFFFFF;
            border: 1px solid var(--dhbw-secondary-50);
            border-radius: 8px;
            padding: 4px;
        }
        .fachbereich-chip {
            color: #FFFFFF;
            font-weight: 700;
            border-radius: 8px;
            padding: 6px 10px;
            margin: 12px 0 6px 0;
        }
        a {
            color: var(--dhbw-accent);
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
