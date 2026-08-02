from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from pypdf import PdfReader


DEFAULT_PDF_PATH = Path("data/nutrition_textbook.pdf")
DEFAULT_OUTPUT_PATH = Path(
    "data/nutrition_textbook_metadata.json"
)

EXPECTED_SHA256 = (
    "5ff1c343c625908c30e16b423004233d6"
    "bbd9a0578d2376cc33c7a75e38e5dd1"
)


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Record metadata for the frozen NutriChat "
            "textbook corpus."
        )
    )

    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--download-date",
        type=str,
        default=None,
        help=(
            "Actual PDF download date in YYYY-MM-DD "
            "format. Omit when unknown."
        ),
    )

    args = parser.parse_args()

    pdf_path = args.pdf

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Textbook PDF not found: {pdf_path.resolve()}"
        )

    sha256 = calculate_sha256(pdf_path)
    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    file_size = pdf_path.stat().st_size

    if sha256 != EXPECTED_SHA256:
        raise ValueError(
            "The textbook PDF does not match the frozen "
            "NutriChat corpus.\n"
            f"Expected: {EXPECTED_SHA256}\n"
            f"Found:    {sha256}\n"
            "Do not replace the original PDF without "
            "creating a new corpus and experiment version."
        )

    if page_count != 894:
        raise ValueError(
            f"Expected 894 PDF pages, found {page_count}."
        )

    metadata = {
        "corpus_id": "nutrichat_human_nutrition_louisiana_frozen_v1",
        "title": "Human Nutrition",
        "edition": "Louisiana Edition",
        "authors": [
            "Melissa Johnson",
            "Latoya Paul",
            "Charlene Shunick",
            "Alin Basgul Yigiter"
        ],
        "editor": "Kelly Kingrey-Edwards",
        "source_url": "https://louis.pressbooks.pub/nutrition/",
        "download_date": args.download_date,
        "metadata_recorded_date": date.today().isoformat(),
        "local_filename": pdf_path.name,
        "local_path": pdf_path.as_posix(),
        "sha256": sha256,
        "file_size_bytes": file_size,
        "pdf_page_count": page_count,
        "pdf_export_type": (
            "Record Digital PDF or Print PDF if known; "
            "otherwise leave unspecified"
        ),
        "page_number_mapping": {
            "python_pdf_indexing": "zero-based",
            "python_formula": (
                "printed_page = zero_based_pdf_index - 19"
            ),
            "viewer_formula": (
                "printed_page = one_based_pdf_viewer_page - 20"
            ),
            "first_numbered_page": {
                "pdf_viewer_page": 21,
                "zero_based_pdf_index": 20,
                "printed_textbook_page": 1
            },
            "configured_python_offset": -19
        },
        "license": {
            "name": (
                "Creative Commons "
                "Attribution-NonCommercial-ShareAlike "
                "4.0 International"
            ),
            "identifier": "CC BY-NC-SA 4.0",
            "license_url": (
                "https://creativecommons.org/"
                "licenses/by-nc-sa/4.0/"
            ),
            "note": "Except where otherwise noted."
        },
        "redistributed_in_public_repository": False,
        "notes": (
            "This exact PDF was used to build the retrieval "
            "corpus and evaluate page-level retrieval."
        )
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Frozen textbook metadata created")
    print("=" * 50)
    print("PDF:", pdf_path)
    print("SHA-256:", sha256)
    print("Pages:", page_count)
    print("Bytes:", file_size)
    print("Metadata:", args.output)


if __name__ == "__main__":
    main()