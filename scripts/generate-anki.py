#!/usr/bin/env python3
"""Generate a Polish Anki deck from a JSON card list."""

import argparse
import html
import json
import re
import sys
from pathlib import Path

import genanki


MODEL_ID = 1948572201
DECK_ID = 1948572202
MEDIA_DIR = Path("anki/media")
OUTPUT_DIR = Path("out")

CSS = """
/* === SOLARIZED LIGHT THEME - MINIMAL === */
.card {
    font-family: 'Futura PT', Arial, sans-serif;
    font-size: 18px;
    text-align: center;
    color: #073642;
}
.word {
    font-family: 'Custom Georgia', Georgia, serif;
    font-size: 32px;
    font-weight: bold;
    color: #cb4b16;
    margin: 20px 0;
    letter-spacing: 0.3px;
}
hr {
    border: 0;
    border-top: 1px solid #93a1a1;
    margin: 20px auto;
    width: 92%;
}
.definition {
    font-family: 'Futura PT', Arial, sans-serif;
    font-size: 20px;
    color: #2aa198;
    margin: 15px 0;
    line-height: 1.4;
    text-align: left;
}
.example {
    font-family: 'Custom Georgia', Georgia, serif;
    font-size: 16px;
    font-style: italic;
    color: #586e75;
    margin: 20px 0;
    line-height: 1.5;
    text-align: left;
    padding-left: 15px;
    border-left: 2px solid #93a1a1;
}
.example strong {
    font-weight: bold;
}
.image-wrapper {
    display: flex;
    justify-content: center;
}
.card-image {
    max-width: 350px;
    width: 85%;
    height: auto;
    margin: 20px 0;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    display: block;
}
.card-image[src=""] {
    display: none !important;
}
"""

MODEL = genanki.Model(
    MODEL_ID,
    "Polish Vocabulary",
    fields=[
        {"name": "Word"},
        {"name": "Definition"},
        {"name": "ExampleSentence"},
        {"name": "Image"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": '<div class="word">{{Word}}</div>',
            "afmt": """
{{FrontSide}}
<hr>
<div class="definition">{{Definition}}</div>
<div class="example">{{ExampleSentence}}</div>
{{#Image}}<div class="image-wrapper"><img class="card-image" src="{{Image}}"></div>{{/Image}}
""",
        }
    ],
    css=CSS,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Polish Anki package from a JSON card list.",
        epilog="""JSON example:
[
  {
    "id": "v0001",
    "lesson": "0001",
    "word": "dziękuję",
    "definition": "wyrażam wdzięczność",
    "example": "Bardzo **dziękuję** za pomoc.",
    "image": "dziekuje.jpg"
  }
]

id, lesson, word, definition, and example are required strings. id is an
immutable note identity. image is optional and must name a file in anki/media/.
Use **text** in an example for bold emphasis.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("cards", type=Path, help="JSON file containing an array of cards")
    parser.add_argument(
        "--deck",
        default="Polish::Course",
        help="deck name (default: Polish::Course)",
    )
    return parser.parse_args()


def read_cards(path):
    try:
        cards = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Card file does not exist: {path}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}")

    if not isinstance(cards, list) or not cards:
        raise ValueError("Card file must contain a non-empty JSON array.")
    return cards


def required_string(card, field, index):
    value = card.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Card {index}: '{field}' must be a non-empty string.")
    return value


def format_example(value):
    escaped = html.escape(value)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def media_file(value, index):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"Card {index}: 'image' must be a filename.")

    filename = Path(value)
    if filename.name != value:
        raise ValueError(f"Card {index}: 'image' must be a filename without a path.")

    path = MEDIA_DIR / filename
    if not path.is_file():
        raise ValueError(f"Card {index}: image does not exist: {path}")
    return path


def output_path():
    OUTPUT_DIR.mkdir(exist_ok=True)
    candidate = OUTPUT_DIR / "output.apkg"
    number = 2
    while candidate.exists():
        candidate = OUTPUT_DIR / f"output-{number}.apkg"
        number += 1
    return candidate


def main():
    args = parse_args()
    deck = genanki.Deck(DECK_ID, args.deck)
    media_files = []

    seen_ids = set()
    for index, card in enumerate(read_cards(args.cards), start=1):
        if not isinstance(card, dict):
            raise ValueError(f"Card {index} must be an object.")

        note_id = required_string(card, "id", index).strip()
        lesson = required_string(card, "lesson", index).strip()
        if note_id in seen_ids:
            raise ValueError(f"Card {index}: duplicate id '{note_id}'.")
        seen_ids.add(note_id)

        word = required_string(card, "word", index)
        definition = required_string(card, "definition", index)
        example = required_string(card, "example", index)
        image = media_file(card.get("image"), index)

        deck.add_note(
            genanki.Note(
                model=MODEL,
                guid=genanki.guid_for("polish-vocabulary", note_id),
                fields=[
                    html.escape(word),
                    html.escape(definition),
                    format_example(example),
                    image.name if image else "",
                ],
                tags=[f"lesson::{lesson}"],
            )
        )
        if image:
            media_files.append(str(image))

    package = genanki.Package(deck)
    package.media_files = media_files
    destination = output_path()
    package.write_to_file(destination)
    print(f"Wrote {destination}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
