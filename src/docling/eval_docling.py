import json
import os

import fitz  # PyMuPDF
import httpx
import pandas as pd


def get_processing_time_from_docling(file_path):
    """Sendet die PDF-Datei an die docling API und gibt die Verarbeitungszeit zurück."""
    url = "http://localhost:5001/v1alpha/convert/file"  # Passen Sie die URL an
    parameters = {
        "from_formats": ["pdf"],
        "to_formats": ["md"],
        "image_export_mode": "placeholder",
        "do_ocr": True,
        "force_ocr": False,
        "ocr_engine": "easyocr",
        "ocr_lang": ["en"],
        "pdf_backend": "dlparse_v2",
        "table_mode": "fast",
        "abort_on_error": False,
        "return_as_file": False,
    }

    with httpx.Client(timeout=120.0) as async_client:
        with open(file_path, "rb") as file:
            files = {"files": (os.path.basename(file_path), file, "application/pdf")}  # Korrektur hier
            try:
                response = async_client.post(url, files=files, data={"parameters": json.dumps(parameters)})
                response.raise_for_status()  # Raise an exception for bad status codes
                return response.json().get("processing_time", None)
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e} - {e.response.text}")
                return None
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print(f"Raw response: {response.text}")
                return None
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return None
            finally:
                async_client.close()


def save_pdf_batch(doc, start_page, end_page, batch_index, original_filename):
    """Speichert einen Batch von Seiten als separate PDF-Datei."""
    batch_pdf_path = f"{os.path.splitext(original_filename)[0]}_batch_{batch_index}.pdf"
    batch_doc = fitz.open()  # Neues leeres PDF-Dokument

    for page_num in range(start_page, end_page):
        batch_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    batch_doc.save(batch_pdf_path)
    batch_doc.close()

    return batch_pdf_path


def get_pdf_info(file_path):
    """Extrahiert Informationen aus einer PDF-Datei und gibt den Text zurück."""
    doc = fitz.open(file_path)

    page_count = doc.page_count  # Seitenanzahl
    text_content = ""

    for page in doc:  # Durchlaufe alle Seiten und extrahiere den Text
        text_content += page.get_text() + "\n\n"  # Textinhalt, Seiten mit doppeltem Zeilenumbruch trennen

    doc.close()
    return page_count, text_content


def gather_file_info(directory):
    """Sammelt Informationen über alle PDF-Dateien in einem Verzeichnis."""
    data = []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            file_size = os.path.getsize(file_path)  # Dateigröße in Bytes
            page_count, text_content = get_pdf_info(file_path)

            # Überprüfen Sie die Seitenanzahl und verarbeiten Sie sie nach Bedarf
            if page_count > 10:
                # Splitten der PDF in Chargen von 5 Seiten
                doc = fitz.open(file_path)
                for batch_index in range(0, page_count, 5):
                    end_page = min(batch_index + 5, page_count)
                    batch_pdf_path = save_pdf_batch(doc, batch_index, end_page, batch_index // 5 + 1, filename)

                    # Holen Sie sich die Verarbeitungszeit von der docling-API
                    processing_time = get_processing_time_from_docling(batch_pdf_path)

                    # Überprüfen Sie, ob die Verarbeitungszeit erhalten wurde
                    if processing_time is None:
                        print(f"Verarbeitungszeit für {batch_pdf_path} konnte nicht abgerufen werden.")
                        processing_time = "N/A"  # Setzen Sie einen Platzhalter, wenn die API fehlschlägt

                    # Speichern Sie den Textinhalt in einer .md-Datei
                    md_filename = os.path.splitext(filename)[0] + f"_batch_{batch_index // 5 + 1}.md"
                    md_file_path = os.path.join(directory, md_filename)
                    with open(md_file_path, "w", encoding="utf-8") as md_file:
                        md_file.write(text_content)

                    # Füge die gesammelten Informationen zur Liste hinzu
                    data.append(
                        {
                            "Filename": filename,
                            "File Size (bytes)": file_size,
                            "Page Count": page_count,
                            "Text Content": md_filename,  # Nur den Dateinamen der Markdown-Datei hinzufügen
                            "Processing Time (seconds)": processing_time,
                        }
                    )
                doc.close()
            else:
                # Wenn die PDF weniger als oder gleich 10 Seiten hat, verarbeiten Sie sie als Ganzes
                processing_time = get_processing_time_from_docling(file_path)

                # Überprüfen Sie, ob die Verarbeitungszeit erhalten wurde
                if processing_time is None:
                    print(f"Verarbeitungszeit für {filename} konnte nicht abgerufen werden.")
                    processing_time = "N/A"

                # Speichern Sie den Textinhalt in einer .md-Datei
                md_filename = os.path.splitext(filename)[0] + ".md"
                md_file_path = os.path.join(directory, md_filename)
                with open(md_file_path, "w", encoding="utf-8") as md_file:
                    md_file.write(text_content)

                # Füge die gesammelten Informationen zur Liste hinzu
                data.append(
                    {
                        "Filename": filename,
                        "File Size (bytes)": file_size,
                        "Page Count": page_count,
                        "Text Content": md_filename,
                        "Processing Time (seconds)": processing_time,
                    }
                )

    # Erstelle ein DataFrame aus den gesammelten Daten
    df = pd.DataFrame(data)
    return df


# Hauptfunktion
if __name__ == "__main__":
    directory = "./docs/"  # Geben Sie hier den Pfad zu Ihrem Ordner an
    df = gather_file_info(directory)

    # Speichern Sie das DataFrame in einer CSV-Datei mit Semikolon als Trennzeichen
    df.to_csv("file_info.csv", sep=";", index=False, quoting=pd.io.common.csv.QUOTE_NONNUMERIC)
