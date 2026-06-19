"""OmniTreasury AI — Data Upload module.

Provides a lightweight HTTP upload server and file processing utilities
for ingesting SWIFT MT103, CSV, JSON, and PDF transaction documents
directly from the dashboard without manual file placement.
"""

from src.upload.file_processor import FileProcessor, UploadedFile
from src.upload.upload_server import UploadServer, run_upload_server

__all__ = ["FileProcessor", "UploadedFile", "UploadServer", "run_upload_server"]
