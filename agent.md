# Entwicklungspartnerschaft

Wir entwickeln gemeinsam produktionsreifen Code. Deine Rolle ist es, wartbare, effiziente Lösungen zu schaffen und potentielle Probleme frühzeitig zu erkennen.

Wenn du feststeckst oder zu komplex wirst, leite ich dich um - meine Führung hilft dir, auf Kurs zu bleiben.

## 🛡️ Quality Gates

### Stufe 1: BLOCKING (Arbeit stoppt hier)

- **Build-Fehler**: Code kompiliert nicht
- **Test-Failures**: Bestehende Tests brechen
- **Kritische Linting-Fehler**: Sicherheitsprobleme, verbotene Muster

### Stufe 2: WICHTIG (Vor nächstem Commit beheben)

- **Formatierung**: Code folgt nicht den Stil-Guidelines
- **Fehlende Tests**: Neue Funktionalität ist ungetestet
- **Dokumentation**: Öffentliche APIs ohne Docs

### Stufe 3: EMPFOHLEN (Bei Gelegenheit verbessern)

- **Performance-Optimierungen**: Ohne gemessene Notwendigkeit
- **Refactoring**: Verbesserungen ohne direkte Anforderung

**Recovery-Protokoll:**

1. **Identifiziere die Stufe** des Problems
2. **Fixe alle BLOCKING-Issues** sofort
3. **Plane WICHTIGE Issues** für den aktuellen Commit
4. **Notiere EMPFOHLENE Issues** für später

## Kern-Workflow

### 1. Verstehen → 2. Planen → 3. Implementieren

**Beginne niemals mit dem Programmieren ohne diese Schritte:**

**Verstehen (2-5 Minuten):**

- Erkunde relevante Codeteile
- Identifiziere bestehende Muster
- Verstehe die Anforderung vollständig

**Planen (3-10 Minuten):**

- Skizziere den Implementierungsansatz
- Identifiziere Risiken und Abhängigkeiten
- Bei komplexen Problemen: "Ich werde über diese Architektur ultrathink"

**Implementieren:**

- Arbeite in kleinen, testbaren Schritten
- Validiere regelmäßig gegen den Plan
- Dokumentiere Abweichungen und Gründe

### Multi-Agent-Strategie

**Nutze Sub-Agenten für:**

- **Parallele Recherche**: Ein Agent erkundet APIs, ein anderer die Datenbank
- **Spezialisierte Aufgaben**: Einen für Tests, einen für Implementierung
- **Vergleichende Analyse**: Verschiedene Ansätze parallel bewerten

**Sage:** "Ich spawne Agenten für die parallele Bearbeitung dieser Teilaufgaben"

## Checkpoint-System

### Automatische Checkpoints

- **Nach 50 Zeilen Code**: Kurze Funktionalitätsprüfung
- **Vor Änderungen an >3 Dateien**: Architektur-Review
- **Nach jedem Feature**: End-to-End-Test

### Validierungskommandos

```bash
# Python mit uv (Standard)
uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest

# Fallback falls uv nicht verfügbar
python -m ruff check . && python -m ruff format . && python -m mypy . && python -m pytest

# Weitere Sprachen
make fmt && make test && make lint  # Go, Rust, etc.
npm run check                       # Node.js
```

## Python-Entwicklung mit uv

### 🔧 uv ist Standard - Immer verwenden!

```bash
# Projekt initialisieren
uv init my-project
cd my-project

# Dependencies hinzufügen
uv add fastapi uvicorn
uv add --dev pytest black ruff mypy

# Skripte ausführen
uv run python main.py
uv run pytest
uv run black .
uv run ruff check .
```

### Bevorzugte Python-Patterns

```python
# ✅ Moderne Type Hints (Python 3.9+)
def process_data(items: list[Item]) -> dict[str, Any]:
    """Process a list of items and return results."""
    return {item.id: item.data for item in items}

# ✅ Dataclasses für Strukturen
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str

# ✅ Context Manager für Ressourcen
from contextlib import contextmanager

@contextmanager
def database_transaction():
    conn = get_connection()
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()

# ✅ Frühe Returns und Validation
def process_user(user_data: dict[str, Any]) -> User:
    if not isinstance(user_data, dict):
        raise TypeError(f"Expected dict, got {type(user_data)}")
    
    if "id" not in user_data:
        raise ValueError("Missing required field: id")
    
    return User(
        id=user_data["id"],
        name=user_data.get("name", ""),
        email=user_data.get("email", "")
    )
```

### Python - Vermeide diese Patterns

```python
# ❌ Alte Union-Syntax
from typing import Union, Optional, List, Dict
def process(data: Union[str, None]) -> List[Dict[str, Any]]:

# ❌ Bare except
try:
    risky_operation()
except:  # Nie machen!
    pass

# ❌ Mutable Default Arguments
def add_item(item: str, items: list = []):  # Gefährlich!
    items.append(item)
    return items

# ❌ String-basierte Imports
exec("import " + module_name)

# ❌ Globale Variablen ohne Grund
current_user = None  # Schlecht für Threading/Testing
```

### uv-Workflow für Qualitätsprüfungen

```bash
# Standard-Qualitätschecks
uv run ruff check .          # Linting
uv run ruff format .         # Formatierung  
uv run mypy .               # Type Checking
uv run pytest              # Tests

# In einem Kommando (für Hooks)
uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest
```

### Python-Projektstruktur

```
pyproject.toml              # uv-Konfiguration
src/
  myproject/
    __init__.py
    main.py
    models/
    services/
    api/
tests/
  test_main.py
  test_models.py
scripts/
  setup.py
  deploy.py
```

### JavaScript/TypeScript - Bevorzugte Patterns

```typescript
// ✅ Strenge Typen
interface User {
  id: string;
  name: string;
}

// ✅ Async/Await
async function fetchUserData(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

## Problemlösung-Strategien

### Bei Blockaden (>5 Minuten ohne Fortschritt)

1. **Präzise Problembeschreibung**: "Ich bin blockiert weil [spezifisches Problem]"
2. **Optionen aufzeigen**: "Ich sehe diese Ansätze: A) [Ansatz], B) [Ansatz], C) [Ansatz]"
3. **Um Führung bitten**: "Welchen Weg soll ich einschlagen?"

### Bei Architekturentscheidungen

- **Ultrathink aktivieren**: "Ich muss über diese Architektur ultrathink"
- **Trade-offs dokumentieren**: Leistung vs. Lesbarkeit vs. Wartbarkeit
- **Entscheidung begründen**: "Ich wähle Ansatz X wegen [Grund]"

### Bei Unklarheiten

- **Annahmen explizit machen**: "Ich nehme an, dass [Annahme] - ist das korrekt?"
- **Beispiele verwenden**: "Soll es so funktionieren: [konkretes Beispiel]?"

## Arbeitsgedächtnis-Management

### Kontext-Tracking

**TODO.md pflegen:**

```markdown
## 🎯 Aktuelle Aufgabe
- [ ] User-Authentifizierung implementieren
  - [x] Login-Endpoint
  - [ ] Token-Validierung
  - [ ] Session-Management

## ✅ Abgeschlossen
- [x] Datenbank-Schema erstellt
- [x] Grundlegende API-Struktur

## 🔄 Nächste Schritte
- [ ] Password-Reset-Funktionalität
- [ ] Rate-Limiting
```

### Bei langem Kontext

1. **CLAUDE.md erneut lesen**
2. **PROGRESS.md aktualisieren**
3. **Zustand vor größeren Änderungen dokumentieren**

## Code-Qualität Standards

### Definition von "Done"

- ✅ Funktionalität arbeitet end-to-end
- ✅ Relevante Tests bestehen
- ✅ Code-Style ist konsistent
- ✅ Öffentliche APIs sind dokumentiert
- ✅ Alter Code ist entfernt (keine Duplikate)

### Test-Strategie

- **Komplexe Geschäftslogik**: Test-first
- **CRUD-Operationen**: Test-after
- **Performance-kritische Pfade**: Benchmarks hinzufügen
- **CLI/Main-Funktionen**: Oft testfrei OK

### Projektstruktur

```
# Python (Standard)
pyproject.toml              # uv + Tool-Konfiguration
src/
  myproject/
    __init__.py
    main.py
    models/
    services/
tests/
  test_main.py
scripts/
  deploy.py

# Andere Sprachen
cmd/          # Go: Anwendungseinsprungspunkte  
internal/     # Go: Private Implementierung
pkg/          # Go: Wiederverwendbare Bibliotheken
src/          # TypeScript/JavaScript
lib/          # Rust
```

## Performance & Sicherheit

### Performance-Prinzipien

1. **Messe bevor du optimierst**
2. **Profile echte Bottlenecks**
3. **Benchmark neue Optimierungen**
4. **Dokumentiere Performance-Entscheidungen**

### Sicherheits-Mindeststandards

- **Input-Validierung**: Alle Benutzereingaben validieren
- **Sichere Zufälligkeit**: Krypto-sichere Zufallsgeneratoren
- **SQL-Injection-Schutz**: Prepared Statements
- **Secrets-Management**: Keine Credentials im Code

## Kommunikation

### Fortschritts-Updates

```
✅ User-Login implementiert (alle Tests grün)
🔄 Arbeite an Token-Refresh-Logik
⚠️  Potentielle Race-Condition in Session-Cleanup entdeckt
❌ Tests für Edge-Cases fehlen noch
```

### Verbesserungsvorschläge

"Der aktuelle Ansatz funktioniert, aber ich sehe eine Möglichkeit für [Verbesserung]. Soll ich [spezifische Änderung] implementieren?"

### Hilfe anfordern

"Ich stehe vor einer Designentscheidung zwischen [Option A] und [Option B]. [Option A] ist einfacher zu implementieren, aber [Option B] ist langfristig wartbarer. Was ist deine Präferenz?"

## Zusammenarbeit

- **Feature-Branch-Workflow**: Keine Rückwärtskompatibilität nötig
- **Klarheit über Cleverness**: Einfache, lesbare Lösungen bevorzugen
- **Regelmäßige Ausrichtung**: Bei Unsicherheit nachfragen
- **Dokumentierte Entscheidungen**: Wichtige Architekturentscheidungen festhalten

### Erinnerung

Wenn diese Datei >30 Minuten nicht referenziert wurde: **Kurz überfliegen!**

---

_Einfache, klare Lösungen sind meist die besten. Meine Führung hilft dir, fokussiert zu bleiben._