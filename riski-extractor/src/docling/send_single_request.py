import asyncio  # Um die asynchrone Funktion auszuführen
import json
import os

import httpx


async def main():
    async with httpx.AsyncClient(timeout=2000.0) as async_client:
        url = "http://localhost:5001/v1alpha/convert/file"
        parameters = {
            "from_formats": ["docx", "pptx", "html", "image", "pdf", "asciidoc", "md", "xlsx"],
            "to_formats": ["md", "json", "html", "text", "doctags"],
            "image_export_mode": "placeholder",
            "do_ocr": True,
            "force_ocr": False,
            "ocr_engine": "tesseract_cli",
            "ocr_lang": ["de"],
            "pdf_backend": "dlparse_v2",
            "table_mode": "fast",
            "abort_on_error": False,
            "return_as_file": False,
        }

        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "docs/5925887.pdf")

        # Öffnen Sie die Datei in einem Kontextmanager, um sicherzustellen, dass sie geschlossen wird.
        with open(file_path, "rb") as file:
            files = {
                "files": ("docs/5925887.pdf", file, "application/pdf"),
            }

            response = await async_client.post(url, files=files, data={"parameters": json.dumps(parameters)})
            assert response.status_code == 200, "Response should be 200 OK"

            data = response.json()
            print(data)  # Ausgabe der Antwortdaten


# Starten Sie die Hauptfunktion
if __name__ == "__main__":
    asyncio.run(main())
