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

    data = load_latest_import_table()
    if not data:
        st.warning("Keine Studiengaenge im Import gefunden.")
        return

    import_year = get_latest_import_year()
    fachbereiche = _group_by_fachbereich(data)
    fachbereich_by_program = {row.studiengang: row.fachbereich for row in data}
    if "selected_program" not in st.session_state:
        first_fachbereich = next(iter(fachbereiche))
        st.session_state["selected_program"] = fachbereiche[first_fachbereich][0]
    selected = st.session_state["selected_program"]
    selected_fachbereich = fachbereich_by_program.get(selected)

    with st.sidebar:
        st.markdown("### Auswahl")
        for fachbereich, programs in fachbereiche.items():
            is_active = fachbereich == selected_fachbereich
            with st.expander(fachbereich, expanded=is_active):
                current = selected if selected in programs else programs[0]
                st.radio(
                    "Studiengang",
                    programs,
                    key=f"program-{fachbereich}",
                    index=programs.index(current),
                    label_visibility="collapsed",
                    on_change=_select_program,
                    args=(fachbereich,),
                )
        st.markdown("### Info")
        st.caption("Quelle: neueste Datei im Ordner `data/`")
        if import_year:
            st.caption(f"Importjahr: {import_year}")

    row = next(item for item in data if item.studiengang == selected)

    st.title("Qualitätsberichte DHBW CAS")
    st.subheader(row.studiengang)
    st.caption(f"Fachbereich: {row.fachbereich}")

    _render_student_metrics(row, import_year)
    _render_profile_sections(row)


def _render_student_metrics(row: StudyProgramRow, import_year: int | None) -> None:
    st.markdown("### Studierendenzahlen")
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**Studienanfaenger (letzte 4 Jahre)**")
        _render_year_series(row.studienanfaenger, import_year)

    with cols[1]:
        st.markdown("**Immatrikulierte Studierende (letzte 4 Jahre)**")
        _render_year_series(row.immatrikulierte, import_year)

    metrics = st.columns(4)
    metrics[0].metric("Erfolgsquote", _format_percent(row.erfolgsquote))
    metrics[1].metric("Fachsemester", _format_number(row.fachsemester))
    metrics[2].metric("Berufserfahrung", _format_number(row.berufserfahrung))
    metrics[3].metric("Alter", _format_number(row.alter))

    st.markdown("### Module")
    module_cols = st.columns(2)
    module_cols[0].metric("Durchschnittliche Modulauslastung", _format_number(row.modulauslastung))
    module_cols[1].metric("Anzahl Module", _format_number(row.anzahl_module))


def _render_profile_sections(row: StudyProgramRow) -> None:
    st.markdown("### Profile")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Vorstudium der Studienanfaenger**")
        _render_profile_table(row.vorstudium_profil)

        st.markdown("**Dozentenherkunft (Lehrveranstaltungsstunden)**")
        _render_profile_table(row.dozenten_herkunft_profil)

    with col_right:
        st.markdown("**Modulbelegung nach Studiengaengen**")
        _render_profile_table(row.module_belegung_nach_sg)

        st.markdown("**Herkunft der Modulteilnehmer**")
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
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
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
            color=alt.Color("Kategorie:N", legend=alt.Legend(orient="right", title=None)),
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
        .mark_text(radius=110, size=12)
        .encode(text=alt.Text("pct:Q", format=".0%"), theta=alt.Theta("Wert:Q"))
    )

    st.altair_chart(
        (chart + labels).configure_view(strokeOpacity=0),
        use_container_width=True,
    )


def _select_program(fachbereich: str) -> None:
    st.session_state["selected_program"] = st.session_state[f"program-{fachbereich}"]


def _group_by_fachbereich(rows: list[StudyProgramRow]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        key = row.fachbereich or "Ohne Fachbereich"
        groups.setdefault(key, []).append(row.studiengang)
    return {key: sorted(values) for key, values in sorted(groups.items())}


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
