"""
Text reader with support for multiple formats and full provenance tracking.

Supports reading from:
- Plain text files (.txt)
- PDF documents (.pdf)
- Word documents (.docx)
- JSON files (.json)
- Web APIs
- Raw strings
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import re

from .models import Provenance, ExtractionMethod


class TextSegment:
    """
    A segment of text with full provenance information.

    Represents a contiguous piece of text with metadata about its origin.
    """

    def __init__(
        self,
        text: str,
        provenance: Provenance,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.provenance = provenance
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"TextSegment(text='{self.text[:50]}...', source={self.provenance.source_file})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "provenance": self.provenance.to_dict(),
            "metadata": self.metadata,
        }


class TextReader:
    """
    Multi-format text reader with provenance tracking.

    Reads text from various sources while maintaining full traceability
    of where each piece of text came from.
    """

    def __init__(self, default_extractor_version: str = "1.0.0"):
        """
        Initialize TextReader.

        Args:
            default_extractor_version: Version identifier for extraction method
        """
        self.default_extractor_version = default_extractor_version

    def read_file(
        self,
        file_path: Union[str, Path],
        encoding: str = "utf-8",
        segment_by: str = "paragraph"  # paragraph, line, sentence, or None
    ) -> List[TextSegment]:
        """
        Read a file and return text segments with provenance.

        Args:
            file_path: Path to the file
            encoding: Text encoding (default: utf-8)
            segment_by: How to segment the text (paragraph, line, sentence, None)

        Returns:
            List of TextSegment objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If unsupported file format
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            return self._read_txt(file_path, encoding, segment_by)
        elif suffix == ".json":
            return self._read_json(file_path, encoding, segment_by)
        elif suffix == ".pdf":
            return self._read_pdf(file_path, segment_by)
        elif suffix in [".docx", ".doc"]:
            return self._read_docx(file_path, segment_by)
        else:
            # Try reading as plain text
            try:
                return self._read_txt(file_path, encoding, segment_by)
            except Exception as e:
                raise ValueError(f"Unsupported file format: {suffix}. Error: {e}")

    def _read_txt(
        self,
        file_path: Path,
        encoding: str,
        segment_by: str
    ) -> List[TextSegment]:
        """Read plain text file."""
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        return self._segment_text(
            content,
            file_path,
            "file",
            segment_by
        )

    def _read_json(
        self,
        file_path: Path,
        encoding: str,
        segment_by: str
    ) -> List[TextSegment]:
        """
        Read JSON file.

        Expects JSON in format:
        {
            "documents": [
                {"text": "...", "metadata": {...}},
                ...
            ]
        }
        or just a list of strings.
        """
        with open(file_path, "r", encoding=encoding) as f:
            data = json.load(f)

        segments = []

        if isinstance(data, list):
            # List of strings
            for i, text in enumerate(data):
                if isinstance(text, str):
                    provenance = Provenance(
                        source_file=str(file_path),
                        source_type="file",
                        section=f"item_{i}",
                        extraction_method=ExtractionMethod.AUTOMATIC,
                        extraction_timestamp=datetime.now(),
                        extractor_version=self.default_extractor_version,
                        raw_text=text,
                    )
                    segments.append(TextSegment(text, provenance))

        elif isinstance(data, dict) and "documents" in data:
            # Structured format
            for i, doc in enumerate(data["documents"]):
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})

                provenance = Provenance(
                    source_file=str(file_path),
                    source_type="file",
                    section=f"document_{i}",
                    extraction_method=ExtractionMethod.AUTOMATIC,
                    extraction_timestamp=datetime.now(),
                    extractor_version=self.default_extractor_version,
                    raw_text=text,
                )

                segment = TextSegment(text, provenance, metadata)
                segments.append(segment)

        else:
            # Try to extract text from any "text" or "content" fields
            text = data.get("text") or data.get("content") or json.dumps(data)
            return self._segment_text(text, file_path, "file", segment_by)

        return segments

    def _read_pdf(self, file_path: Path, segment_by: str) -> List[TextSegment]:
        """
        Read PDF file.

        Note: Requires PyPDF2 or pdfplumber to be installed.
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required to read PDF files. "
                "Install it with: pip install PyPDF2"
            )

        segments = []

        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)

            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()

                if not text.strip():
                    continue

                # Create segments for this page
                page_segments = self._segment_text(
                    text,
                    file_path,
                    "file",
                    segment_by,
                    page=page_num
                )

                segments.extend(page_segments)

        return segments

    def _read_docx(self, file_path: Path, segment_by: str) -> List[TextSegment]:
        """
        Read Word document.

        Note: Requires python-docx to be installed.
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required to read Word documents. "
                "Install it with: pip install python-docx"
            )

        doc = Document(file_path)
        segments = []

        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()

            if not text:
                continue

            provenance = Provenance(
                source_file=str(file_path),
                source_type="file",
                section=f"paragraph_{i}",
                extraction_method=ExtractionMethod.AUTOMATIC,
                extraction_timestamp=datetime.now(),
                extractor_version=self.default_extractor_version,
                raw_text=text,
            )

            segments.append(TextSegment(text, provenance))

        return segments

    def read_string(
        self,
        text: str,
        source_name: str = "string",
        segment_by: str = "paragraph"
    ) -> List[TextSegment]:
        """
        Read text from a string with provenance tracking.

        Args:
            text: The text to read
            source_name: Name to identify the source
            segment_by: How to segment the text

        Returns:
            List of TextSegment objects
        """
        return self._segment_text(text, source_name, "string", segment_by)

    def read_api_response(
        self,
        response_data: Dict[str, Any],
        source_url: str,
        text_field: str = "text"
    ) -> List[TextSegment]:
        """
        Read text from an API response.

        Args:
            response_data: The API response data (dict)
            source_url: The API endpoint URL
            text_field: The field containing the text

        Returns:
            List of TextSegment objects
        """
        segments = []

        # Handle list of items
        if isinstance(response_data, list):
            for i, item in enumerate(response_data):
                if isinstance(item, dict) and text_field in item:
                    text = item[text_field]

                    provenance = Provenance(
                        source_url=source_url,
                        source_type="api",
                        section=f"item_{i}",
                        extraction_method=ExtractionMethod.AUTOMATIC,
                        extraction_timestamp=datetime.now(),
                        extractor_version=self.default_extractor_version,
                        raw_text=text,
                    )

                    # Extract other fields as metadata
                    metadata = {k: v for k, v in item.items() if k != text_field}
                    segments.append(TextSegment(text, provenance, metadata))

        # Handle single dict
        elif isinstance(response_data, dict):
            if text_field in response_data:
                text = response_data[text_field]

                provenance = Provenance(
                    source_url=source_url,
                    source_type="api",
                    extraction_method=ExtractionMethod.AUTOMATIC,
                    extraction_timestamp=datetime.now(),
                    extractor_version=self.default_extractor_version,
                    raw_text=text,
                )

                metadata = {k: v for k, v in response_data.items() if k != text_field}
                segments.append(TextSegment(text, provenance, metadata))

        return segments

    def _segment_text(
        self,
        text: str,
        source: Union[str, Path],
        source_type: str,
        segment_by: Optional[str],
        page: Optional[int] = None
    ) -> List[TextSegment]:
        """
        Segment text into smaller pieces with provenance.

        Args:
            text: The text to segment
            source: Source identifier (file path, URL, etc.)
            source_type: Type of source (file, string, api)
            segment_by: How to segment (paragraph, line, sentence, None)
            page: Optional page number (for PDFs)

        Returns:
            List of TextSegment objects
        """
        if segment_by is None:
            # Return entire text as one segment
            provenance = Provenance(
                source_file=str(source) if source_type == "file" else None,
                source_url=str(source) if source_type in ["api", "url"] else None,
                source_type=source_type,
                page=page,
                extraction_method=ExtractionMethod.AUTOMATIC,
                extraction_timestamp=datetime.now(),
                extractor_version=self.default_extractor_version,
                raw_text=text,
            )
            return [TextSegment(text, provenance)]

        segments = []

        if segment_by == "line":
            lines = text.split("\n")
            for i, line in enumerate(lines, start=1):
                if not line.strip():
                    continue

                provenance = Provenance(
                    source_file=str(source) if source_type == "file" else None,
                    source_url=str(source) if source_type in ["api", "url"] else None,
                    source_type=source_type,
                    line_start=i,
                    line_end=i,
                    page=page,
                    section=f"line_{i}",
                    extraction_method=ExtractionMethod.AUTOMATIC,
                    extraction_timestamp=datetime.now(),
                    extractor_version=self.default_extractor_version,
                    raw_text=line,
                )
                segments.append(TextSegment(line.strip(), provenance))

        elif segment_by == "paragraph":
            # Split by double newlines
            paragraphs = re.split(r"\n\s*\n", text)
            current_line = 1

            for i, para in enumerate(paragraphs, start=1):
                if not para.strip():
                    continue

                line_count = para.count("\n") + 1

                provenance = Provenance(
                    source_file=str(source) if source_type == "file" else None,
                    source_url=str(source) if source_type in ["api", "url"] else None,
                    source_type=source_type,
                    line_start=current_line,
                    line_end=current_line + line_count - 1,
                    page=page,
                    section=f"paragraph_{i}",
                    extraction_method=ExtractionMethod.AUTOMATIC,
                    extraction_timestamp=datetime.now(),
                    extractor_version=self.default_extractor_version,
                    raw_text=para,
                )

                segments.append(TextSegment(para.strip(), provenance))
                current_line += line_count + 1  # +1 for the blank line

        elif segment_by == "sentence":
            # Simple sentence splitting (can be improved with proper NLP)
            sentences = re.split(r"[.!?]+\s+", text)

            for i, sentence in enumerate(sentences, start=1):
                if not sentence.strip():
                    continue

                provenance = Provenance(
                    source_file=str(source) if source_type == "file" else None,
                    source_url=str(source) if source_type in ["api", "url"] else None,
                    source_type=source_type,
                    page=page,
                    section=f"sentence_{i}",
                    extraction_method=ExtractionMethod.AUTOMATIC,
                    extraction_timestamp=datetime.now(),
                    extractor_version=self.default_extractor_version,
                    raw_text=sentence,
                )

                segments.append(TextSegment(sentence.strip(), provenance))

        return segments

    def read_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        encoding: str = "utf-8",
        segment_by: str = "paragraph"
    ) -> List[TextSegment]:
        """
        Read multiple files and combine segments.

        Args:
            file_paths: List of file paths to read
            encoding: Text encoding
            segment_by: How to segment the text

        Returns:
            Combined list of TextSegment objects from all files
        """
        all_segments = []

        for file_path in file_paths:
            try:
                segments = self.read_file(file_path, encoding, segment_by)
                all_segments.extend(segments)
            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                continue

        return all_segments
