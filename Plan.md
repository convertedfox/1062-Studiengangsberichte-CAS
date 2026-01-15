# Ziel
## Einleitung
Ziel dieser Anwendung ist es, ein übersichtliches Dashboard für die Qualitätsberichterstattung von Studiengängen zu erstellen. 
Mit Hilfe von Python und Streamlit sollen statistische Daten aus einer großen Excel-Datei gezogen und in einer benutzerfreundlichen Form dargestellt werden. Jede Unterseite des Dashboards wird dabei die gleichen Kennzahlen für einen bestimmten Studiengang abbilden.
## Dargestellte Daten
Das Dashboard soll folgende Metriken für jeden Studiengang visualisieren:

a) Studienanfängerzahlen der letzten vier Jahre: Diese Daten befinden sich am Anfang der Excel-Datei in den ersten Spalten.
b) Immatrikulierte Studierende der letzten vier Jahre: Ebenfalls ein wichtiger statistischer Wert.
c) Hochschultyp des Vorstudiums der Studienanfänger: Eine Übersicht darüber, von welcher Art Hochschule die Studienanfänger kommen.
d) Erfolgsquote der Studierenden: Wie viele Studierende schließen das Studium erfolgreich ab.
e) Anzahl der für das Studium benötigten Fachsemester: Durchschnittliche Fachsemesterzahl bis zum Abschluss.
f) Berufserfahrung der Studienanfänger: Wie viele Jahre Berufserfahrung die Studienanfänger mitbringen.
g) Durchschnittliches Alter zu Beginn des Studiums: Das Durchschnittsalter der Studierenden beim Studienstart.
h) Herkunft der Dozenten: Eine Übersicht, woher die Lehrenden stammen.
i) Modulbelegung nach Studiengängen: In welchen Studiengängen die Studierenden welche Module belegen.
j) Herkunft der Modulteilnehmer: Aus welchen Studiengängen kommen die Teilnehmer eines Moduls.
k) Durchschnittliche Modulauslastung: Eine Fließkommazahl, die zeigt, wie stark Module im Schnitt ausgelastet sind.
l) Anzahl der Module: Wie viele Module insgesamt angeboten werden.
# Architektur
## Quelldateien
Die Quelldaten werden stets in einer Excel-Datei angeliefert, die einer festen Struktur folgt. Diese Excel-Daten werden im ersten Schritt in einen oder mehrere DataFrames überführt, damit die statistischen Werte sauber weiterverarbeitet werden können.
Diese liegt immer im Ordner "data" und heisst immer "Import YYYY". Nimm stets die aktuellste Datei als Quelle, also z.b. "Import 2025.xlsx" vor "Import 2024.xlsx

## Framework
Als Framework dient Streamlit, um die Web-Oberfläche des Dashboards zu gestalten. Die Grafiken und Visualisierungen werden direkt aus den DataFrames heraus generiert und auf den Unterseiten für die jeweiligen Studiengänge angezeigt.
# Benutzeroberfläche
Für die Navigation der Nutzer wird es auf der linken Seite eine Seitenleiste geben, in der alle verfügbaren Studiengänge aufgelistet sind. 
Jeder Studiengang erhält eine eigene Unterseite, die automatisch aus der vorliegenden Excel-Datei generiert wird. 
Das Programm wertet also aus, wie viele Studiengänge vorhanden sind, und erstellt für jeden davon eine eigene Sektion im Dashboard. 
Auf diese Weise können die Benutzer einfach durch die Studiengänge navigieren und erhalten auf jeder Unterseite die relevanten statistischen Kennzahlen.