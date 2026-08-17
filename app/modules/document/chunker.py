from __future__ import annotations

import spacy
from google import genai
from app.modules.document.data_model import Element, DocumentBlock
from app.core.config import settings

# Gemini token counter
class GeminiTokenCounter:
    # Uses Gemini's own tokenizer through the official count_tokens API.
    # info: gemini-embedding-001 has a 2048-token input limit.
    MODEL_NAME = "gemini-embedding-001"

    def __init__(
        self,
        api_key: str,
        cache_enabled: bool = True,
    ):
        self.client = genai.Client(api_key=api_key)
        self.cache_enabled = cache_enabled
        self._cache: dict[str, int] = {}

    def count(self, text: str) -> int:
        text = text.strip()

        if not text:
            return 0

        if self.cache_enabled and text in self._cache:
            return self._cache[text]

        response = self.client.models.count_tokens(
            model=self.MODEL_NAME,
            contents=text,
        )

        token_count = response.total_tokens

        if self.cache_enabled:
            self._cache[text] = token_count

        return token_count


# Sentence splitting
class SentenceSplitter:
    # Lightweight sentence splitting using spaCy.

    def __init__(self):
        self.nlp = spacy.blank("en")

        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

    def split(self, text: str) -> list[str]:
        text = text.strip()

        if not text:
            return []

        doc = self.nlp(text)

        return [
            sentence.text.strip()
            for sentence in doc.sents
            if sentence.text.strip()
        ]

# Token aware chunker
class TokenAwareChunker:

    def __init__(
        self
    ):

        token_counter: GeminiTokenCounter = GeminiTokenCounter(
            api_key=settings.GEMINI_API_KEY,
        )
        sentence_splitter: SentenceSplitter = SentenceSplitter()
        target_tokens: int = 900
        max_tokens: int = 1000
        overlap_sentences: int = 2

        # gemini embedding 001:  at most 2048 input tokens,
        if max_tokens >= 2048:
            raise ValueError(
                "max_tokens must stay below the "
                "2048-token input limit of "
                "gemini-embedding-001."
            )

        if target_tokens >= max_tokens:
            raise ValueError(
                "target_tokens must be smaller "
                "than max_tokens."
            )

        self.token_counter = token_counter

        self.sentence_splitter = (
            sentence_splitter
            or SentenceSplitter()
        )

        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.overlap_sentences = overlap_sentences

    # Main chunking method

    def chunk(
        self,
        elements: list[Element],
        doc_metadata: dict[str, Any],
    ) -> list[DocumentBlock]:

        blocks: list[DocumentBlock] = []

        buffer: list[Element] = []

        current_section_path: list[str] = []

        carry_over_text = ""

        def flush() -> None:

            nonlocal buffer
            nonlocal carry_over_text

            if not buffer:
                return

            body_text = "\n\n".join(
                element.text
                for element in buffer
            )

            if carry_over_text:
                full_text = (
                    f"{carry_over_text}\n\n"
                    f"{body_text}"
                ).strip()
            else:
                full_text = body_text

            breadcrumb = " > ".join(
                current_section_path
            )

            final_text = (
                f"{breadcrumb}\n\n"
                f"{full_text}"
                if breadcrumb
                else full_text
            )

            blocks.append(
                DocumentBlock(
                    text=final_text,
                    metadata=self._merge_metadata(
                        buffer_elements=buffer,
                        doc_metadata=doc_metadata,
                        section_path=current_section_path,
                        chunk_index=len(blocks),
                    ),
                )
            )

            carry_over_text = (
                self._tail_sentences(
                    body_text,
                    self.overlap_sentences,
                )
            )

            buffer = []

        # Walk elements
        for element in elements:

            # Heading
            if element.element_type == "heading":

                if buffer:
                    flush()

                if element.level:

                    current_section_path = (
                        element.section_path
                        + [element.text]
                    )

                continue

            element_text = element.text

            breadcrumb = " > ".join(
                current_section_path
            )

            if breadcrumb:
                contextual_text = (
                    f"{breadcrumb}\n\n"
                    f"{element_text}"
                )
            else:
                contextual_text = element_text

            element_tokens = (
                self.token_counter.count(
                    contextual_text
                )
            )

            # Oversized element
            if (
                element_tokens
                > self.max_tokens
            ):

                if buffer:
                    flush()

                sub_elements = (
                    self._split_oversized(
                        element
                    )
                )

                for sub_element in sub_elements:

                    breadcrumb = " > ".join(
                        current_section_path
                    )

                    sub_text = sub_element.text

                    final_text = (
                        f"{breadcrumb}\n\n"
                        f"{sub_text}"
                        if breadcrumb
                        else sub_text
                    )

                    blocks.append(
                        DocumentBlock(
                            text=final_text,
                            metadata=self._merge_metadata(
                                buffer_elements=[
                                    sub_element
                                ],
                                doc_metadata=doc_metadata,
                                section_path=current_section_path,
                                chunk_index=len(blocks),
                            ),
                        )
                    )

                carry_over_text = ""
                continue

            # Check exceed target?
            if buffer:

                candidate_body = (
                    "\n\n".join(
                        e.text
                        for e in buffer
                    )
                    + "\n\n"
                    + element.text
                )

                candidate_text = (
                    f"{breadcrumb}\n\n"
                    f"{candidate_body}"
                    if breadcrumb
                    else candidate_body
                )

                candidate_tokens = (
                    self.token_counter.count(
                        candidate_text
                    )
                )

                if (
                    candidate_tokens
                    > self.target_tokens
                ):
                    flush()

            buffer.append(element)

        # Final buffer
        flush()

        return blocks

    # Split oversized element
    def _split_oversized(
        self,
        element: Element,
    ) -> list[Element]:

        if element.element_type == "table":
            return self._split_table(element)

        sentences = (
            self.sentence_splitter.split(
                element.text
            )
        )

        if not sentences:
            return [element]

        chunks: list[Element] = []

        current_sentences: list[str] = []

        # No API count for every partial candidate here.
        # We accumulate using the exact Gemini token counter
        # over the candidate sentence block.

        for sentence in sentences:

            candidate = (
                " ".join(
                    current_sentences
                    + [sentence]
                )
            )

            breadcrumb = " > ".join(
                element.section_path
            )

            candidate_with_context = (
                f"{breadcrumb}\n\n"
                f"{candidate}"
                if breadcrumb
                else candidate
            )

            candidate_tokens = (
                self.token_counter.count(
                    candidate_with_context
                )
            )

            if (
                candidate_tokens
                > self.max_tokens
                and current_sentences
            ):

                chunks.append(
                    Element(
                        text=" ".join(
                            current_sentences
                        ),
                        element_type=(
                            element.element_type
                        ),
                        level=element.level,
                        section_path=(
                            element.section_path.copy()
                        ),
                        location=(
                            element.location.copy()
                        ),
                    )
                )

                current_sentences = [
                    sentence
                ]

            else:
                current_sentences.append(
                    sentence
                )

        if current_sentences:

            chunks.append(
                Element(
                    text=" ".join(
                        current_sentences
                    ),
                    element_type=(
                        element.element_type
                    ),
                    level=element.level,
                    section_path=(
                        element.section_path.copy()
                    ),
                    location=(
                        element.location.copy()
                    ),
                )
            )

        return chunks or [element]

    # Split table
    def _split_table(
        self,
        element: Element,
    ) -> list[Element]:

        lines = element.text.split("\n")

        if (
            len(lines) < 3
            or not lines[0].startswith("|")
        ):
            return [element]

        header = lines[0]
        separator = lines[1]
        rows = lines[2:]

        chunks: list[Element] = []

        current_rows: list[str] = []

        for row in rows:

            candidate_rows = (
                current_rows
                + [row]
            )

            table_text = "\n".join(
                [
                    header,
                    separator,
                    *candidate_rows,
                ]
            )

            breadcrumb = " > ".join(
                element.section_path
            )

            contextual_table = (
                f"{breadcrumb}\n\n"
                f"{table_text}"
                if breadcrumb
                else table_text
            )

            candidate_tokens = (
                self.token_counter.count(
                    contextual_table
                )
            )

            if (
                candidate_tokens
                > self.max_tokens
                and current_rows
            ):

                chunk_text = "\n".join(
                    [
                        header,
                        separator,
                        *current_rows,
                    ]
                )

                chunks.append(
                    Element(
                        text=chunk_text,
                        element_type="table",
                        level=element.level,
                        section_path=(
                            element.section_path.copy()
                        ),
                        location=(
                            element.location.copy()
                        ),
                    )
                )

                current_rows = [row]

            else:
                current_rows.append(row)

        if current_rows:

            chunks.append(
                Element(
                    text="\n".join(
                        [
                            header,
                            separator,
                            *current_rows,
                        ]
                    ),
                    element_type="table",
                    level=element.level,
                    section_path=(
                        element.section_path.copy()
                    ),
                    location=(
                        element.location.copy()
                    ),
                )
            )

        return chunks or [element]

    # Sentence overlap
    def _tail_sentences(
        self,
        text: str,
        n: int,
    ) -> str:

        sentences = (
            self.sentence_splitter.split(
                text
            )
        )

        if not sentences:
            return ""

        return " ".join(
            sentences[-n:]
        )

    # Metadata
    @staticmethod
    def _merge_metadata(
        buffer_elements: list[Element],
        doc_metadata: dict[str, Any],
        section_path: list[str],
        chunk_index: int,
    ) -> dict[str, Any]:

        pages = [
            element.location.get("page")
            for element in buffer_elements
            if element.location.get("page")
            is not None
        ]

        row_starts = [
            element.location.get("row_start")
            for element in buffer_elements
            if element.location.get("row_start")
            is not None
        ]

        row_ends = [
            element.location.get("row_end")
            for element in buffer_elements
            if element.location.get("row_end")
            is not None
        ]

        sheet_names = {
            element.location.get(
                "sheet_name"
            )
            for element in buffer_elements
            if element.location.get(
                "sheet_name"
            )
        }

        content_types = sorted(
            {
                element.element_type
                for element in buffer_elements
            }
        )

        metadata = dict(doc_metadata)

        metadata.update(
            {
                "chunk_id": (
                    f"{doc_metadata.get('doc_id', 'doc')}"
                    f"::chunk_{chunk_index}"
                ),
                "section_path": (
                    section_path.copy()
                ),
                "content_types": (
                    content_types
                ),
            }
        )

        if pages:
            metadata["page_start"] = min(pages)
            metadata["page_end"] = max(pages)

        if row_starts and row_ends:
            metadata["row_start"] = min(
                row_starts
            )
            metadata["row_end"] = max(
                row_ends
            )

        if sheet_names:
            metadata["sheet_name"] = (
                next(iter(sheet_names))
                if len(sheet_names) == 1
                else sorted(sheet_names)
            )

        return metadata
