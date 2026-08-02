
import re
from tqdm.auto import tqdm
from spacy.lang.en import English


def add_sentences_to_pages(pages: list[dict]) -> list[dict]:
    nlp = English()
    nlp.add_pipe("sentencizer")

    for item in tqdm(pages, desc="Sentence splitting"):
        item["sentences"] = [str(sentence) for sentence in nlp(item["text"]).sents]
        item["page_sentence_count_spacy"] = len(item["sentences"])

    return pages


def clean_chunk(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\.([A-Z])", r". \1", text)
    return text.strip()


def add_chunk_stats(chunk: dict, text: str) -> dict:
    chunk["chunk_char_count"] = len(text)
    chunk["chunk_word_count"] = len(text.split())
    chunk["chunk_token_count"] = len(text) / 4
    return chunk


def sentence_window_chunks(
    pages: list[dict],
    window_size: int,
    stride: int,
    strategy_name: str,
) -> list[dict]:
    chunks = []

    for item in tqdm(pages, desc=strategy_name):
        sentences = item.get("sentences", [])

        for start in range(0, len(sentences), stride):
            sentence_group = sentences[start:start + window_size]

            if not sentence_group:
                continue

            text = clean_chunk(" ".join(sentence_group))

            chunk = {
                "strategy": strategy_name,
                "page_number": item["page_number"],
                "sentence_chunk": text,
                "embedding_text": (
                    f"Nutrition textbook passage. Page {item['page_number']}.\n\n{text}"
                ),
            }

            chunks.append(add_chunk_stats(chunk, text))

    return chunks


def word_window_chunks(
    pages: list[dict],
    chunk_words: int,
    overlap_words: int,
    strategy_name: str,
) -> list[dict]:
    chunks = []
    step = max(1, chunk_words - overlap_words)

    for item in tqdm(pages, desc=strategy_name):
        words = item["text"].split()

        for start in range(0, len(words), step):
            word_group = words[start:start + chunk_words]

            if not word_group:
                continue

            text = clean_chunk(" ".join(word_group))

            chunk = {
                "strategy": strategy_name,
                "page_number": item["page_number"],
                "sentence_chunk": text,
                "embedding_text": (
                    f"Nutrition textbook passage. Page {item['page_number']}.\n\n{text}"
                ),
            }

            chunks.append(add_chunk_stats(chunk, text))

    return chunks


def build_chunks(pages: list[dict], strategy_name: str) -> list[dict]:
    if strategy_name == "sentence_15_no_overlap":
        return sentence_window_chunks(
            pages=pages,
            window_size=15,
            stride=15,
            strategy_name="sentence_15_no_overlap",
        )

    if strategy_name == "sentence_10_overlap_5":
        return sentence_window_chunks(
            pages=pages,
            window_size=10,
            stride=5,
            strategy_name="sentence_10_overlap_5",
        )

    if strategy_name == "sentence_8_overlap_4":
        return sentence_window_chunks(
            pages=pages,
            window_size=8,
            stride=4,
            strategy_name="sentence_8_overlap_4",
        )

    if strategy_name == "sentence_6_overlap_3":
        return sentence_window_chunks(
            pages=pages,
            window_size=6,
            stride=3,
            strategy_name="sentence_6_overlap_3",
        )

    if strategy_name == "word_180_overlap_40":
        return word_window_chunks(
            pages=pages,
            chunk_words=180,
            overlap_words=40,
            strategy_name="word_180_overlap_40",
        )

    if strategy_name == "word_280_overlap_60":
        return word_window_chunks(
            pages=pages,
            chunk_words=280,
            overlap_words=60,
            strategy_name="word_280_overlap_60",
        )

    raise ValueError(f"Unknown chunking strategy: {strategy_name}")


def filter_chunks_by_min_tokens(
    chunks: list[dict],
    min_token_length: int,
) -> list[dict]:
    return [
        chunk
        for chunk in chunks
        if chunk["chunk_token_count"] > min_token_length
    ]


def add_chunk_ids(chunks: list[dict]) -> list[dict]:
    for idx, chunk in enumerate(chunks):
        chunk["chunk_id"] = idx

    return chunks
