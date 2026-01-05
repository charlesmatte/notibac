#!/usr/bin/env python3
"""
Script to parse waste collection calendar PDFs and extract dates to JSON.
Uses Claude's vision API to analyze the calendar images.

Usage:
    python parse_calendars.py 2026

Requires ANTHROPIC_API_KEY environment variable or in .env file.
"""

import argparse
import asyncio
import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

ROOT_DIR = Path("calendars")

EXTRACTION_PROMPT = """Analyze this waste collection calendar PDF and extract ALL collection dates for the year shown.

The calendar uses these icons to mark collection days:
- Green trash bin icon (bac vert) = DÉCHETS (garbage)
- Blue recycling icon (bac bleu) = RÉCUPÉRATION (recycling)
- Brown compost bin icon (bac brun) = COMPOST
- Leaf/plant icon = RÉSIDUS VERTS (yard waste) - typically spring/fall only
- Christmas tree icon = ARBRES DE NOËL (Christmas trees) - January only
- Orange dumpster icon = ENCOMBRANTS (bulky_waste) - marked as "SEMAINE DES ENCOMBRANTS"

Look at EVERY month carefully and identify ALL dates that have each icon type.

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{
  "garbage": ["YYYY-MM-DD", ...],
  "recycling": ["YYYY-MM-DD", ...],
  "compost": ["YYYY-MM-DD", ...],
  "yard_waste": ["YYYY-MM-DD", ...],
  "christmas_trees": ["YYYY-MM-DD", ...],
  "bulky_waste": ["YYYY-MM-DD", ...]
}

Important:
- Use ISO 8601 date format (YYYY-MM-DD)
- Include ALL dates for the entire year
- If a collection type has no dates, use an empty array []
- Return ONLY the JSON, no other text"""


def extract_sector_info(filename: str) -> dict:
    """Extract sector number and type from PDF filename."""
    # Examples:
    # 01-Cal-gmr-2026.pdf -> sector 1, avec compost
    # 01-sans-Cal-gmr-2026.pdf -> sector 1, sans compost
    # 12-evain-Cal-gmr-2026.pdf -> sector 12 Évain Nord, avec compost
    # 14a-Granada-Cal-gmr-2026.pdf -> sector 14A Granada, avec compost
    # 14ab-Granada-sans-Cal-gmr-2026.pdf -> sector 14AB Granada, sans compost
    # 21-22-Cloutier-Rollet-Sans-Cal-gmr-2026.pdf -> sectors 21-22, sans compost
    # 24-25-26-Clericy-Destor-Mont-Brun-Sans-Cal-gmr-2026.pdf -> sectors 24-25-26, sans compost

    name = filename.lower()
    has_compost = "-sans-" not in name and not name.startswith("sans")

    # Extract sector number(s) and optional location name
    # Pattern handles: XX, XX-YY, XX-YY-ZZ, XXa, XXb, XXab
    match = re.match(r"^(\d+(?:-\d+)*[ab]*)(?:-([a-z][a-z-]*?))?-(?:sans-)?cal", name)

    if match:
        sector_id = match.group(1)
        location = match.group(2)

        # Build sector name
        # Remove trailing letters for display
        sector_num = re.sub(r"[ab]+$", "", sector_id)
        suffix_match = re.search(r"([ab]+)$", sector_id)
        suffix = suffix_match.group(1).upper() if suffix_match else ""

        if sector_num.count("-") > 0:
            sector_name = f"Secteurs {sector_num}"
        else:
            sector_name = f"Secteur {sector_num}"

        if suffix:
            sector_name += suffix

        if location and location not in ["cal", "gmr"]:
            # Capitalize location name
            loc_name = location.replace("-", " ").title()
            sector_name += f" - {loc_name}"

        return {
            "sector": sector_id,
            "sector_name": sector_name,
            "has_compost": has_compost,
        }

    return {
        "sector": "unknown",
        "sector_name": filename,
        "has_compost": has_compost,
    }


def generate_output_filename(pdf_filename: str) -> str:
    """Generate JSON output filename from PDF filename."""
    # 01-Cal-gmr-2026.pdf -> sector-01-avec-compost.json
    # 01-sans-Cal-gmr-2026.pdf -> sector-01-sans-compost.json

    info = extract_sector_info(pdf_filename)
    compost_suffix = "avec-compost" if info["has_compost"] else "sans-compost"
    return f"sector-{info['sector'].zfill(2)}-{compost_suffix}.json"


async def parse_pdf_with_claude(pdf_path: Path, year: str) -> dict:
    """Send PDF to Claude API and extract collection dates."""
    client = anthropic.Anthropic()

    # Read PDF as base64
    with open(pdf_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    # Extract JSON from response
    response_text = message.content[0].text

    # Try to parse as JSON directly
    try:
        collections = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            collections = json.loads(json_match.group(1))
        else:
            raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")

    return collections


async def process_pdf(pdf_path: Path, output_dir: Path, year: str) -> str:
    """Process a single PDF and save JSON output."""
    filename = pdf_path.name
    print(f"Processing: {filename}")

    try:
        # Extract sector info
        sector_info = extract_sector_info(filename)

        # Parse PDF with Claude
        collections = await parse_pdf_with_claude(pdf_path, year)

        # Build full JSON structure
        result = {
            "sector": sector_info["sector"],
            "sector_name": sector_info["sector_name"],
            "year": int(year),
            "has_compost": sector_info["has_compost"],
            "collections": collections,
        }

        # Generate output filename
        output_filename = generate_output_filename(filename)
        output_path = output_dir / output_filename

        # Save JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"  -> Saved to {output_path}")
        return output_filename

    except Exception as e:
        print(f"  -> Error: {e}")
        return None


async def main(year: str):
    """Parse all PDFs for the given year."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        print("Set it in your .env file or as an environment variable")
        return

    input_dir = ROOT_DIR / year
    output_dir = input_dir / "json"

    if not input_dir.exists():
        print(f"Error: Directory {input_dir} does not exist")
        print(f"Run 'python download_calendars.py {year}' first")
        return

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Find all PDF files
    pdf_files = sorted(input_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {input_dir}")

    if not pdf_files:
        print("No PDF files found")
        return

    # Process each PDF
    successful = []
    for pdf_path in pdf_files:
        result = await process_pdf(pdf_path, output_dir, year)
        if result:
            successful.append(result)

    print(f"\nComplete! Successfully parsed {len(successful)}/{len(pdf_files)} files")
    print(f"JSON files saved to {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse waste collection calendar PDFs to JSON"
    )
    parser.add_argument(
        "year",
        type=str,
        help="The year to parse calendars for (e.g., 2026)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.year))
