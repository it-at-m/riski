# Erkenntnisse bei der Evaluation von Docling

## Performance

- Die Verarbeitung dauert initial **10–40 Sekunden pro Dokument** abhängig von der Größe des Dokumnets
- Empfehlung: Einmaliges vollständiges Scrapen und Verarbeiten aller Dokumente.
- Danach nur noch **iterative Verarbeitung**, wenn sich Dokumente ändern, um Zeit zu sparen.

## Herausforderungen

### 1. Tabellen im Querformat
- Probleme bei der Erkennung und Verarbeitung von Tabellen, die im Querformat (landscape) vorliegen.
- Besonders kritisch, wenn diese nur als **Bild** eingebunden sind (z. B. Lagepläne).

### 2. Texterkennung (OCR)
- **Vertauschte Buchstaben** bei der OCR:
  - `I` wird als `l` erkannt
  - `i` wird ebenfalls als `l` erkannt
- Dies führt zu **Ungenauigkeiten bei der Texterfassung**, speziell bei Eigennamen oder technischen Begriffen.

### 3. Handschriftliche Einträge
- Probleme bei der Erkennung von **handschriftlichen Inhalten**, insbesondere:
  - Wenn mehrere **Ankreuzfelder nebeneinander** stehen (z. B. in BV-Anträgen)
  - Erkennung, ob Felder aktiviert oder leer sind, ist oft fehleranfällig

### 4. Struktur- und Layout-Erkennung
- Schwierigkeiten bei der **korrekten Gliederung von Dokumenten**:
  - Überschriften, Absätze oder Spalten nicht korrekt erkannt
  - Layoutabhängige Informationen (z. B. Fußnoten, Randtexte) gehen verloren

### 7. Bilder ohne eingebetteten Text
- Lagepläne, Karten oder schematische Darstellungen bestehen meist nur aus Pixelbildern
- Keine Texterkennung möglich ohne zusätzliche manuelle Annotation
