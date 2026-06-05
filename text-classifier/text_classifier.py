import argparse
import csv
import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = """
Classify each customer text into:
- sentiment: one of positive, negative, neutral
- category: one of support, sales, billing, other
- confidence_note: a short explanation of the classification confidence

Return only a JSON object with these keys:
sentiment, category, confidence_note
""".strip()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classify texts from a CSV file using the OpenAI API."
    )
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output CSV file. Defaults to '<input>_classified.csv'.",
    )
    return parser.parse_args()


def default_output_path(input_path):
    base, extension = os.path.splitext(input_path)
    return f"{base}_classified{extension or '.csv'}"


def classify_text(client, text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    return {
        "sentiment": result.get("sentiment", "neutral"),
        "category": result.get("category", "other"),
        "confidence_note": result.get("confidence_note", ""),
    }


def validate_result(result):
    allowed_sentiments = {"positive", "negative", "neutral"}
    allowed_categories = {"support", "sales", "billing", "other"}

    sentiment = result.get("sentiment", "neutral")
    category = result.get("category", "other")

    if sentiment not in allowed_sentiments:
        result["sentiment"] = "neutral"
        result["confidence_note"] = append_note(
            result.get("confidence_note", ""),
            f"Invalid sentiment '{sentiment}' was replaced with neutral.",
        )

    if category not in allowed_categories:
        result["category"] = "other"
        result["confidence_note"] = append_note(
            result.get("confidence_note", ""),
            f"Invalid category '{category}' was replaced with other.",
        )

    return result


def append_note(existing_note, extra_note):
    if not existing_note:
        return extra_note
    return f"{existing_note} {extra_note}"


def process_csv(input_path, output_path, client):
    with open(input_path, "r", newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)

        if not reader.fieldnames:
            raise ValueError("Input CSV is empty or missing a header row.")

        if "text" not in reader.fieldnames:
            raise ValueError('Input CSV must include a column called "text".')

        output_fieldnames = list(reader.fieldnames)
        for field in ("sentiment", "category", "confidence_note"):
            if field not in output_fieldnames:
                output_fieldnames.append(field)

        with open(output_path, "w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=output_fieldnames)
            writer.writeheader()

            for row_number, row in enumerate(reader, start=2):
                text = row.get("text", "")

                try:
                    classification = validate_result(classify_text(client, text))
                except Exception as error:
                    logging.exception("Failed to classify row %s: %s", row_number, error)
                    classification = {
                        "sentiment": "",
                        "category": "",
                        "confidence_note": f"Classification failed: {error}",
                    }

                row.update(classification)
                writer.writerow(row)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    args = parse_args()
    output_path = args.output or default_output_path(args.input_csv)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    process_csv(args.input_csv, output_path, client)
    logging.info("Wrote classified results to %s", output_path)


if __name__ == "__main__":
    main()
