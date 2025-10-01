from typing import List

from src.data_models import File


def download_and_persist_files(files: List[File]):
    for file in files:
        if not file.content:  # or checksum does not macthc:
            # get content als blob
            # add blob to file
            # add size to file
            # add checksum to file
            # save file to database
            pass


def _blob_checksum():
    pass
