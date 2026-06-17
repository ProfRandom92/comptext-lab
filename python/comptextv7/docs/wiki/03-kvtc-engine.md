# 03 — KVTC Engine

## Engine Contract

Die öffentliche Kern-API ist bewusst klein: `KVTCV7Engine.compress(logs)` nimmt einen String oder ein Iterable von Zeilen entgegen und liefert ein `CompressionResult`. Dieses Resultat enthält Tokenzahlen, Reduktionsquote, die vier KVTC-Schichten, das transportierbare Payload-Textfeld und die intern geparsten Events.

## Interne Datenobjekte

```mermaid
classDiagram
    class StructuredLogEvent {
      +int line_no
      +str raw
      +datetime? timestamp
      +str severity
      +str ecu
      +tuple codes
      +Mapping fields
      +str consonant_signature
      +str fingerprint
    }
    class HeaderLayer {
      +int event_count
      +str source_fingerprint
      +str? first_timestamp
      +str? last_timestamp
      +Mapping severity_counts
      +Mapping code_counts
    }
    class MiddleLayer {
      +tuple families
      +Mapping family_counts
    }
    class WindowLayer {
      +int window_seconds
      +tuple bursts
    }
    class FrameLayer {
      +Mapping dictionary
      +str payload
    }
    class CompressionResult {
      +int original_tokens
      +int compressed_tokens
      +float compression_ratio
      +float reduction_percent
      +str text
    }
    CompressionResult --> HeaderLayer
    CompressionResult --> MiddleLayer
    CompressionResult --> WindowLayer
    CompressionResult --> FrameLayer
    CompressionResult --> StructuredLogEvent
```

## Four-Layer-Sandwich

| Layer | Zweck | Typische Inhalte | Review-Frage |
| --- | --- | --- | --- |
| Header | Laufweite Metadaten und Inventar. | Eventanzahl, Hash, Zeitbereich, Severity- und Code-Zählung. | Passt die Quelle, der Zeitraum und die Alarmverteilung? |
| Middle | Häufigste Diagnosefamilien. | `ECU:severity:primary-code:signature:fields`. | Welche Muster dominieren den Logstrom? |
| Window | Zeitliche Burst-Struktur. | Fensterbucket mit Familienzählung. | Wann clustern Fehler oder Alarme? |
| Frame | Kompakter Transport. | Dictionary plus JSON-Payload oder Micro-Frame. | Ist der Payload klein, stabil und auditierbar? |

## Kompressionslogik

```mermaid
flowchart TD
    A[Line]
    B{Timestamp?}
    C{Severity?}
    D{ECU/module/source?}
    E{Codes?}
    F[Key-value fields]
    G[Remove low-entropy prefixes]
    H[Extreme consonant map]
    I[Family key]
    J[Header / Middle / Window]
    K{Tiny heterogeneous packet?}
    L[Sparse micro-frame]
    M[Dictionary JSON frame]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K
    K -- yes --> L
    K -- no --> M
```

## Extreme Consonant Mapping v2

Die Signaturbildung reduziert natürliche Sprache aggressiv und schützt gleichzeitig diagnostisch relevante Anker:

- OBD/DTC/SPN/FMI-Codes bleiben als hochentropische Diagnoseanker erhalten.
- Domänenbegriffe wie `temperature`, `pressure`, `voltage`, `brake` oder `diagnostic` werden in stabile Kurzformen überführt.
- Messwerte können exakt erhalten oder im Familienmodus zu Einheitsslots wie `#C`, `#V`, `#BAR` generalisiert werden.
- Kontextfelder wie `ecu`, `module` und `source` werden separat geführt, damit sie Familien nicht doppelt aufblähen.

## Sparse Micro-Frame

Für bis zu drei heterogene Ereignisse kann ein vollständiger JSON-Frame mehr Metadaten als Nutzen erzeugen. In diesem Fall nutzt die Engine eine deterministische Micro-Frame-Repräsentation, während Header, Middle und Events im `CompressionResult` weiterhin auditierbar bleiben.

```mermaid
stateDiagram-v2
    [*] --> FullFrameCandidate
    FullFrameCandidate --> SparseMicroFrame: events <= 3 and every family count == 1
    FullFrameCandidate --> JsonDictionaryFrame: repeated families or larger batch
    SparseMicroFrame --> [*]
    JsonDictionaryFrame --> [*]
```

## Beispiel-Payload-Typen

| Typ | Wann | Form |
| --- | --- | --- |
| Dictionary JSON Frame | Wiederholte oder größere strukturierte Logmengen. | Kompaktes JSON mit `v`, `h`, `d`, `m`, `w`. |
| Sparse Micro-Frame | Sehr kleine heterogene Triage-Pakete. | Pipe-getrennte Kurzform mit Event-Synopsis. |

## Erweiterungsleitlinien

1. Neue Parser-Regeln müssen deterministisch sein.
2. Neue Domänenbegriffe gehören in eine stabile Mapping-Tabelle und brauchen Regressionstests.
3. Nie Alarme, Severity, Zeitstempel oder Event-Reihenfolge abschwächen.
4. Änderungen an Frame-Format oder Tokenzählung müssen Golden-Corpus-, Replay- und Forensik-Erwartungen aktualisieren.
5. Neue Daten-Domänen sollten eigene Golden-Fixtures erhalten, statt bestehende Fixtures in-place zu ändern.
