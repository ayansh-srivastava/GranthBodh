from io import BytesIO

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader


from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentBlock:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

class DocumentParser:

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> list[DocumentBlock]:
        reader = PdfReader(BytesIO(file_bytes))

        blocks = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if text and text.strip():
                blocks.append(
                    DocumentBlock(
                        text=text.strip(),
                        metadata={
                            "page": page_number,
                        },
                    )
                )

        return blocks

    @staticmethod
    def parse_docx(file_bytes: bytes) -> list[DocumentBlock]:
        document = Document(BytesIO(file_bytes))

        blocks = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                blocks.append(
                    DocumentBlock(
                        text=paragraph.text.strip(),
                        metadata={},
                    )
                )

        return blocks

    @staticmethod
    def parse_xlsx(file_bytes: bytes) -> list[DocumentBlock]:
        workbook = load_workbook(
            BytesIO(file_bytes),
            read_only=True,
            data_only=True,
        )

        blocks = []
        row_start = 1
        for index, worksheet in enumerate(workbook.worksheets, start=1):
            first_row = next(worksheet.iter_rows(values_only=True), None)

            rows = []

            for row_number, row in enumerate(worksheet.iter_rows(values_only=True), start=1):

                values = [
                    str(value)
                    for value in row
                    if value is not None
                ]

                if values:
                    rows.append(" | ".join(values))

                if len(rows) * len(rows[0]) > 1000:
                    blocks.append(
                        DocumentBlock(
                            text=f"Sheet: {worksheet.title}\n" + "\n" + first_row + "\n".join(rows),
                            metadata={
                                "sheet": index,
                                "rowStart": row_start,
                                "rowEnd": row_number,
                            },
                        )
                    )
                    rows = []
                    row_start = row_number + 1

        return blocks

    @classmethod
    def parse( cls, filename: str, file_bytes: bytes) -> list[DocumentBlock]:

        extension = filename.lower().split(".")[-1]

        if extension == "pdf":
            return cls.parse_pdf(file_bytes)

        if extension == "docx":
            return cls.parse_docx(file_bytes)

        if extension == "xlsx":
            return cls.parse_xlsx(file_bytes)

        raise ValueError(f"Unsupported file type: .{extension}")
