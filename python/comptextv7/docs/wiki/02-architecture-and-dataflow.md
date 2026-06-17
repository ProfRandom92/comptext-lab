# 02 — Architecture and Dataflow

## High-Level-Architektur

```mermaid
flowchart TB
    subgraph Input[Input Layer]
      L1[XENTRY-style logs]
      L2[OBD / CAN diagnostics]
      L3[SCADA / plant events]
      L4[Sparse workshop notes]
    end

    subgraph Core[KVTC Core]
      N[Line normalizer]
      P[Structured event parser]
      C[Extreme consonant mapping v2]
      S[KVTC four-layer sandwich]
    end

    subgraph Evidence[Evidence Layer]
      H[Header]
      M[Middle families]
      W[Temporal windows]
      F[Frame payload]
    end

    subgraph Controls[Validation Controls]
      G[Golden corpus]
      R[Replay determinism]
      A[Semantic forensic audit]
      T[Token telemetry]
    end

    subgraph Outputs[Outputs]
      D[Industrial dashboard]
      B[Benchmark reports]
      API[Assistant / copilot / analytics handoff]
    end

    Input --> N --> P --> C --> S
    S --> H
    S --> M
    S --> W
    S --> F
    H --> Controls
    M --> Controls
    W --> Controls
    F --> Controls
    Controls --> D
    Controls --> B
    F --> API
```

## Datenfluss in Phasen

| Phase | Aufgabe | Ergebnis |
| --- | --- | --- |
| 1. Normalisieren | Eingabe als String oder Iterable in Zeilen zerlegen. | Stabile Zeilenfolge. |
| 2. Parsen | Zeitstempel, Severity, ECU/Modul, Codes und Key-Value-Felder extrahieren. | `StructuredLogEvent` pro Logzeile. |
| 3. Signieren | Low-Entropy-Prefixe entfernen, Konsonanten-/Domänensignatur bilden. | Familienfähige Event-Signatur. |
| 4. Schichten bauen | Header, Middle, Window und Frame erzeugen. | Auditierbares KVTC-Sandwich. |
| 5. Validieren | Replay, Golden Corpus, Forensik und Token-Telemetrie prüfen. | Release-fähige Evidenz oder Blocker. |
| 6. Ausgeben | Payload, Reports, Dashboard oder downstream Handoff bereitstellen. | Kompakte Transport- und Review-Artefakte. |

## Sequenzdiagramm

```mermaid
sequenceDiagram
    participant User as Operator/CI
    participant Engine as KVTCV7Engine
    participant Parser as Structured Parser
    participant Layers as Layer Builders
    participant Validator as Validation Suite
    participant Dash as Dashboard/Reports

    User->>Engine: compress(logs)
    Engine->>Parser: _parse_line(line)
    Parser-->>Engine: StructuredLogEvent
    Engine->>Layers: _build_header(events)
    Engine->>Layers: _build_middle(events)
    Engine->>Layers: _build_window(events)
    Engine->>Layers: _build_frame(...)
    Layers-->>Engine: CompressionResult
    User->>Validator: scripts/validate.py all
    Validator-->>Dash: Markdown/JSON evidence
    User->>Dash: industrial_dashboard.py --once or server
```

## Schichtenmodell

```mermaid
flowchart TB
    A[Raw technical logs]
    B[Structured events]
    C1[Header layer]
    C2[Middle family layer]
    C3[Window burst layer]
    C4[Frame dictionary + payload]
    Z[CompressionResult]

    A --> B
    B --> C1
    B --> C2
    B --> C3
    C1 --> C4
    C2 --> C4
    C3 --> C4
    C1 --> Z
    C2 --> Z
    C3 --> Z
    C4 --> Z
```

## Trust Boundaries

| Grenze | Risiko | Gegenmaßnahme |
| --- | --- | --- |
| Rohdaten → Parser | PII, FIN/VIN, Werkstattnotizen oder sensible Anlagenkontexte können in Rohlogs liegen. | KVTC am Edge ausführen; Sanitizing vor externem Handoff ergänzen. |
| Parser → Kompression | Seltene Alarme könnten von aggressiver Kompression verdeckt werden. | Sparse-Micro-Frame, Forensik-Gates, Golden-Corpus-Tests. |
| Kompression → LLM | Modell könnte Payload falsch interpretieren. | Audit-Layer mitgeben; keine Payload ohne Kontext als Vollrekonstruktion deklarieren. |
| Benchmark → Management-Aussage | Hohe Reduktion kann bei High-Entropy-Daten irreführend sein. | Top-Family-Coverage und Forensikmetriken gemeinsam berichten. |

## Repository-Mapping

```mermaid
flowchart LR
    Core[src/core/kvtc_v7.py]
    Bench[benchmarks]
    Validation[src/validation]
    Datasets[datasets/golden]
    Dashboard[dashboard]
    Reports[*.md reports]

    Core --> Bench
    Core --> Validation
    Datasets --> Validation
    Validation --> Reports
    Bench --> Reports
    Validation --> Dashboard
    Bench --> Dashboard
```
