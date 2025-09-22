import json
import os

import httpx
import pandas as pd
import pymupdf as fitz


def get_processing_time_from_docling(file_path):
    """Send PDF File to docling API"""
    url = "http://localhost:5001/v1alpha/convert/file"
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

    with httpx.Client(timeout=2000.0) as client:
        with open(file_path, "rb") as file:
            files = {"files": (os.path.basename(file_path), file, "application/pdf")}
            try:
                response = client.post(url, files=files, data={"parameters": json.dumps(parameters)})
                response.raise_for_status()
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
                client.close()


def save_pdf_batch(doc, start_page, end_page, batch_index, original_filename):
    """Save batch of pages as separate PDF"""
    batch_pdf_path = f"{os.path.splitext(original_filename)[0]}_batch_{batch_index}.pdf"
    batch_doc = fitz.open()

    for page_num in range(start_page, end_page):
        batch_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    batch_doc.save(batch_pdf_path)
    batch_doc.close()

    return batch_pdf_path


def get_pdf_info(file_path):
    """Extract information out of PDF"""
    doc = fitz.open(file_path)

    page_count = doc.page_count
    text_content = ""

    for page in doc:
        text_content += page.get_text() + "\n\n"

    doc.close()
    return page_count, text_content


def gather_file_info(directory, md_output_folder):
    """Collect information about all PDF files"""
    os.makedirs(md_output_folder, exist_ok=True)

    data = []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            file_size = os.path.getsize(file_path)
            page_count, text_content = get_pdf_info(file_path)

            if page_count > 10:
                doc = fitz.open(file_path)
                for batch_index in range(0, page_count, 5):
                    end_page = min(batch_index + 5, page_count)
                    batch_pdf_path = save_pdf_batch(doc, batch_index, end_page, batch_index // 5 + 1, filename)
                    processing_time = get_processing_time_from_docling(batch_pdf_path)

                    if processing_time is None:
                        print(f"Cannot retrieve execution time for {batch_pdf_path}.")
                        processing_time = "N/A"

                    md_filename = os.path.splitext(filename)[0] + f"_batch_{batch_index // 5 + 1}.md"
                    md_file_path = os.path.join(md_output_folder, md_filename)
                    with open(md_file_path, "w", encoding="utf-8") as md_file:
                        md_file.write(text_content)

                    data.append(
                        {
                            "Filename": filename,
                            "File Size (bytes)": file_size,
                            "Page Count": page_count,
                            "Text Content": md_filename,
                            "Processing Time (seconds)": processing_time,
                        }
                    )
                doc.close()
            else:
                processing_time = get_processing_time_from_docling(file_path)

                if processing_time is None:
                    print(f"Could not retrieve execution time for {filename}.")
                    processing_time = "N/A"

                md_filename = os.path.splitext(filename)[0] + ".md"
                md_file_path = os.path.join(md_output_folder, md_filename)
                with open(md_file_path, "w", encoding="utf-8") as md_file:
                    md_file.write(text_content)

                data.append(
                    {
                        "Filename": filename,
                        "File Size (bytes)": file_size,
                        "Page Count": page_count,
                        "Text Content": md_filename,
                        "Processing Time (seconds)": processing_time,
                    }
                )

    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    directory = "./test_files/"
    md_output_folder = "./md_output_pyPDF/"
    df = gather_file_info(directory, md_output_folder)
    df.to_csv("file_info.csv", sep=";", index=False)
