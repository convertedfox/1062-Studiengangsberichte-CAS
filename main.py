from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from import_parser import StudyProgramRow, get_latest_import_year, load_latest_import_table


# Studiengänge, die nicht im Dashboard angezeigt werden sollen.
# Namen müssen exakt den Werten in `row.studiengang` entsprechen.
HIDDEN_STUDY_PROGRAMS: set[str] = {
    "Master in Business Management (auslaufend)"# "M.Sc. Beispielstudiengang",
}


def main() -> None:
    """Initialisiert das Dashboard, lädt Daten und rendert die passende Ansicht."""

    st.set_page_config(
        page_title="Studiengangskennzahlen Dashboard",
        page_icon="📊",
        layout="wide",
    )

    _inject_styles()

    data = load_latest_import_table()
    data = _filter_hidden_study_programs(data, HIDDEN_STUDY_PROGRAMS)
    if not data:
        st.warning("Keine Studiengänge im Import gefunden.")
        return

    import_year = get_latest_import_year()
    fachbereiche = _group_by_fachbereich(data)
    fachbereich_by_program = {row.studiengang: row.fachbereich for row in data}
    if "selected_kind" not in st.session_state:
        first_fachbereich = next(iter(fachbereiche))
        st.session_state["selected_kind"] = "program"
        st.session_state["selected_value"] = fachbereiche[first_fachbereich][0]
    else:
        st.session_state["selected_kind"], st.session_state["selected_value"] = _normalize_selection(
            fachbereiche,
            fachbereich_by_program,
            st.session_state.get("selected_kind", "program"),
            st.session_state.get("selected_value"),
        )
    selected_kind = st.session_state["selected_kind"]
    selected_value = st.session_state["selected_value"]

    with st.sidebar:
        st.markdown("### Auswahl")
        for fachbereich, programs in fachbereiche.items():
            st.markdown(_fachbereich_header(fachbereich), unsafe_allow_html=True)
            if selected_kind == "fachbereich" and selected_value == fachbereich:
                st.markdown(f"- **Übersicht {fachbereich}**")
            else:
                st.button(
                    f"Übersicht {fachbereich}",
                    key=f"fachbereich-{fachbereich}",
                    use_container_width=True,
                    on_click=_select_fachbereich,
                    args=(fachbereich,),
                )
            for program in programs:
                if selected_kind == "program" and program == selected_value:
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

    if selected_kind == "fachbereich":
        rows = [item for item in data if item.fachbereich == selected_value]
        _render_fachbereich_overview(rows, import_year, selected_value)
    else:
        row = next(item for item in data if item.studiengang == selected_value)

        st.title("Studiengangskennzahlen DHBW CAS")
        st.subheader(row.studiengang)
        st.caption(f"Fachbereich: {row.fachbereich}")

        _render_student_metrics(row, import_year)
        _render_profile_sections(row)


def _render_student_metrics(row: StudyProgramRow, import_year: int | None) -> None:
    """Zeigt Zeitreihen und KPI-Karten zu Studierendenzahlen und Modulen eines Studiengangs."""

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
        ],
        columns=1,
    )


def _render_profile_sections(row: StudyProgramRow) -> None:
    """Zeigt die Profilverteilungen des gewählten Studiengangs in zwei Spalten."""

    _section_title("Profile")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="panel-title">Vorstudium der Studienanfänger(innen)</div>', unsafe_allow_html=True)
        _render_profile_table(row.vorstudium_profil)

        st.markdown(
            '<div class="panel-title">Dozierendenherkunft</div>',
            unsafe_allow_html=True,
        )
        _render_profile_table(row.dozenten_herkunft_profil)

    with col_right:
        st.markdown('<div class="panel-title">Modulbelegung nach Studiengängen</div>', unsafe_allow_html=True)
        _render_profile_table(row.module_belegung_nach_sg)

        st.markdown('<div class="panel-title">Herkunft der Modulteilnehmer(innen)</div>', unsafe_allow_html=True)
        _render_profile_table(row.modulteilnehmer_herkunft)


def _render_fachbereich_overview(rows: list[StudyProgramRow], import_year: int | None, fachbereich: str) -> None:
    """Rendert aggregierte Kennzahlen und Profile für einen gesamten Fachbereich."""

    st.title("Fachbereichsübersicht DHBW CAS")
    st.subheader(fachbereich)

    _section_title("Studierendenzahlen")
    cols = st.columns(2)
    with cols[0]:
        st.markdown(
            '<div class="panel-title">Studienanfänger(innen) (letzte 4 Jahre)</div>',
            unsafe_allow_html=True,
        )
        _render_year_series(_sum_year_series(rows, "studienanfaenger"), import_year)

    with cols[1]:
        st.markdown(
            '<div class="panel-title">Immatrikulierte Studierende (letzte 4 Jahre)</div>',
            unsafe_allow_html=True,
        )
        _render_year_series(_sum_year_series(rows, "immatrikulierte"), import_year)

    _render_kpi_row(
        [
            ("Erfolgsquote", _format_percent(_average_metric(rows, "erfolgsquote"))),
            ("Ø Benötigte Anzahl an Fachsemestern", _format_number(_average_metric(rows, "fachsemester"))),
            ("Ø Berufserfahrung zu Studienbeginn in Jahren", _format_number(_average_metric(rows, "berufserfahrung"))),
            ("Ø Alter zu Studienbeginn in Jahren", _format_number(_average_metric(rows, "alter"))),
        ]
    )

    _section_title("Module")
    cols = st.columns(2)
    with cols[0]:
        st.markdown('<div class="panel-title">Modulbelegung nach Studiengängen</div>', unsafe_allow_html=True)
        _render_profile_table(_aggregate_profiles(rows, "module_belegung_nach_sg"))
    with cols[1]:
        st.markdown('<div class="panel-title">Herkunft der Modulteilnehmer(innen)</div>', unsafe_allow_html=True)
        _render_profile_table(_aggregate_profiles(rows, "modulteilnehmer_herkunft"))

    _render_kpi_row(
        [
            ("Durchschnittliche Modulauslastung", _format_number(_average_metric(rows, "modulauslastung"))),
        ],
        columns=1,
    )


def _render_year_series(values: dict[str, int | None], import_year: int | None) -> None:
    """Visualisiert eine 4-Jahresreihe als Balkendiagramm plus Textzusammenfassung."""

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
    """Stellt Profilanteile als Donut-Chart dar, sofern verwertbare Werte vorhanden sind."""

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
    data_filtered = data[data["Wert"].fillna(0) > 0]
    if data_filtered.empty:
        st.caption("Keine Daten vorhanden.")
        return
    base = (
        alt.Chart(data_filtered)
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
    """Setzt den aktuell ausgewählten Studiengang in der Session."""

    st.session_state["selected_kind"] = "program"
    st.session_state["selected_value"] = program


def _select_fachbereich(fachbereich: str) -> None:
    """Setzt die aktuell ausgewählte Fachbereichsübersicht in der Session."""

    st.session_state["selected_kind"] = "fachbereich"
    st.session_state["selected_value"] = fachbereich


def _group_by_fachbereich(rows: list[StudyProgramRow]) -> dict[str, list[str]]:
    """Gruppiert Studiengänge nach Fachbereich und sortiert Gruppen sowie Einträge."""

    groups: dict[str, list[str]] = {}
    for row in rows:
        key = row.fachbereich or "Ohne Fachbereich"
        groups.setdefault(key, []).append(row.studiengang)
    return {key: sorted(values) for key, values in sorted(groups.items())}


def _filter_hidden_study_programs(
    rows: list[StudyProgramRow], hidden_programs: set[str]
) -> list[StudyProgramRow]:
    """Entfernt alle Studiengänge, die in der Ausblendeliste stehen."""

    if not hidden_programs:
        return rows
    hidden_normalized = {name.strip().lower() for name in hidden_programs if name.strip()}
    return [row for row in rows if row.studiengang.strip().lower() not in hidden_normalized]


def _normalize_selection(
    fachbereiche: dict[str, list[str]],
    fachbereich_by_program: dict[str, str],
    selected_kind: str,
    selected_value: object,
) -> tuple[str, str]:
    """Sorgt dafür, dass die Sidebar-Auswahl nach Filterung gültig bleibt."""

    if selected_kind == "fachbereich" and isinstance(selected_value, str) and selected_value in fachbereiche:
        return selected_kind, selected_value

    if selected_kind == "program" and isinstance(selected_value, str) and selected_value in fachbereich_by_program:
        return selected_kind, selected_value

    first_fachbereich = next(iter(fachbereiche))
    first_program = fachbereiche[first_fachbereich][0]
    return "program", first_program


def _sum_year_series(rows: list[StudyProgramRow], attr: str) -> dict[str, int | None]:
    """Summiert eine Jahresreihe über mehrere Studiengänge und berücksichtigt fehlende Werte."""

    totals: dict[str, int] = {"-4": 0, "-3": 0, "-2": 0, "-1": 0}
    seen: dict[str, bool] = {"-4": False, "-3": False, "-2": False, "-1": False}
    for row in rows:
        series = getattr(row, attr)
        for key in totals:
            value = series.get(key)
            if value is None:
                continue
            totals[key] += value
            seen[key] = True
    return {key: (totals[key] if seen[key] else None) for key in totals}


def _aggregate_profiles(rows: list[StudyProgramRow], attr: str) -> dict[str, float | None]:
    """Addiert gleichnamige Profilwerte über mehrere Studiengänge."""

    totals: dict[str, float] = {}
    for row in rows:
        profile = getattr(row, attr)
        for key, value in profile.items():
            if value is None:
                continue
            totals[key] = totals.get(key, 0.0) + float(value)
    return totals


def _average_metric(rows: list[StudyProgramRow], attr: str) -> float | None:
    """Mittelwert über einen numerischen Kennzahlenwert mehrerer Studiengänge."""

    values = [float(value) for row in rows if (value := getattr(row, attr)) is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _fachbereich_header(fachbereich: str) -> str:
    """Erzeugt den farbigen HTML-Header für einen Fachbereich in der Sidebar."""

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
    """Rendert einen einheitlich gestylten Abschnittstitel."""

    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def _render_kpi_row(items: list[tuple[str, str]], columns: int = 4) -> None:
    """Rendert KPI-Karten in einer konfigurierbaren Anzahl von Spalten."""

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
    """Injiziert das globale CSS-Theme für Layout und Farben des Dashboards."""

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
            min-height: 118px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .kpi-label {
            color: #000000;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            line-height: 1.25;
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
    """Formatiert Zahlen kompakt oder gibt bei fehlendem Wert `n/a` zurück."""

    if value is None:
        return "n/a"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_percent(value: float | None) -> str:
    """Formatiert einen Dezimalwert als Prozentanzeige oder `n/a`."""

    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


if __name__ == "__main__":
    main()
