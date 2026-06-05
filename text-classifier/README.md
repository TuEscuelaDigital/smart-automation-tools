# Text Classifier

This project classifies customer text from a CSV file using the OpenAI Chat Completions API.

For each row, the script adds:

- `sentiment`: `positive`, `negative`, or `neutral`
- `category`: `support`, `sales`, `billing`, or `other`
- `confidence_note`: a short note explaining the classification confidence

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in this folder:

```bash
OPENAI_API_KEY=your_api_key_here
```

You can copy `.env.example` and replace the placeholder value.

## Input Format

The input CSV must include a header row and at least a column named `text`.

Example:

```csv
id,text
1,"I love how quickly your team solved my issue. The service was excellent."
2,"I was charged twice this month and need someone to fix my invoice."
```

Additional columns are preserved in the output.

## Output Format

By default, the output file is created beside the input file with `_classified` added to the filename.

For example:

```text
sample_input_classified.csv
```

The output CSV includes the original columns plus:

```csv
sentiment,category,confidence_note
```

If one row fails during classification, the script logs the error, writes an error note for that row, and continues processing the remaining rows.

## Usage

Run with the default output path:

```bash
python text_classifier.py sample_input.csv
```

Run with a custom output path:

```bash
python text_classifier.py sample_input.csv --output results.csv
```
