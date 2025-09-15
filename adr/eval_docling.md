# Findings from the evaluation of Docling

## Performance

- Processing initially takes **10–40 seconds per document**, depending on the size of the document.
- Recommendation: Scrape and process all documents completely once.
- After that, only perform **iterative processing** when documents change to save time.

## Challenges

### 1. Tables in landscape format

- Problems with recognizing and processing tables that are in landscape format.
- This is particularly critical if they are only included as **images** (e.g., site plans).

### 2. Text recognition (OCR)

- **Transposed letters** in OCR:
  - `I` is recognized as `l`
  - `i` is also recognized as `l`
- This leads to **inaccuracies in text recognition**, especially with proper names or technical terms.

### 3. Handwritten entries

- Problems with recognizing **handwritten content**, in particular:
  - When several **checkboxes are next to each other** (e.g., in BV applications)
  - Recognizing whether fields are activated or empty is often prone to errors

### 4. Structure and layout recognition

- Difficulties with **correct document structuring**:
  - Headings, paragraphs, or columns are not recognized correctly
  - Layout-dependent information (e.g., footnotes, margin notes) is lost

### 5. Images without embedded text

- Site plans, maps, or schematic representations usually consist only of pixel images
- No text recognition possible without additional manual annotation
