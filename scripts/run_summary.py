#!/usr/bin/env python3
"""
Offline summarization CLI tool.

Runs the summarization pipeline on existing transcript files without
a live session. Used for:
- Iterating on prompts
- A/B testing different configurations
- Validating improvements against psychologist annotations
- Re-processing old transcripts with updated pipeline

Usage (must run with the server venv):
    # Run all 3 levels on a transcript file
    server/venv/bin/python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --all-levels

    # Run a specific level
    server/venv/bin/python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --level clinical

    # Specify output file
    server/venv/bin/python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --all-levels --output summary.txt
"""

import argparse
import asyncio
import os
import sys
import re
from pathlib import Path

# Add server directory to path for imports
server_dir = Path(__file__).parent.parent / 'server'
sys.path.insert(0, str(server_dir))

from dotenv import load_dotenv
load_dotenv(server_dir / '.env')

from src.config import config, SUMMARY_LEVELS
from src.services.summarization import SummarizationService


def parse_transcript_file(filepath: str) -> list:
    """
    Parse a transcript file into the token buffer format expected by
    the summarization pipeline.

    Supports two formats:
    1. Raw text with speaker labels: "דובר א׳: text..."
    2. Timestamped format: "[MM:SS] דובר א׳: text..."

    Returns a list of token dicts with 'text', 'speaker', 'timestamp' keys.
    """
    tokens = []
    current_speaker = 'Unknown'
    current_timestamp_ms = 0
    timestamp_increment_ms = 5000  # 5 seconds between tokens if no timestamps

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip header lines (contain metadata like date, patient name)
        if any(line.startswith(prefix) for prefix in ['תמלול', 'מטופל', 'תאריך', 'שעה', 'משך']):
            continue

        # Try to extract timestamp: [MM:SS]
        ts_match = re.match(r'\[(\d{1,2}):(\d{2})\]\s*(.*)', line)
        if ts_match:
            minutes = int(ts_match.group(1))
            seconds = int(ts_match.group(2))
            current_timestamp_ms = (minutes * 60 + seconds) * 1000
            line = ts_match.group(3)

        # Try to extract speaker label
        # Hebrew format: "דובר א׳: text" or "דובר X: text"
        speaker_match = re.match(r'(דובר\s+\S+)[:\s]+(.*)', line)
        if speaker_match:
            current_speaker = speaker_match.group(1)
            line = speaker_match.group(2)

        # English format: "Speaker A: text"
        en_speaker_match = re.match(r'(Speaker\s+\S+)[:\s]+(.*)', line)
        if en_speaker_match:
            current_speaker = en_speaker_match.group(1)
            line = en_speaker_match.group(2)

        if line.strip():
            tokens.append({
                'text': line.strip(),
                'speaker': current_speaker,
                'timestamp': current_timestamp_ms,
            })
            current_timestamp_ms += timestamp_increment_ms

    return tokens


async def run_summary(
    transcript_path: str,
    patient_name: str,
    levels: list,
    output_path: str | None = None,
) -> str:
    """Run summarization and return the result content."""
    # Parse transcript
    tokens = parse_transcript_file(transcript_path)
    if not tokens:
        print("Error: No tokens parsed from transcript file.")
        sys.exit(1)

    print(f"Parsed {len(tokens)} tokens from transcript")
    print(f"Patient: {patient_name}")
    print(f"Levels: {', '.join(levels)}")

    # Get session start time from first token
    session_start_ms = tokens[0].get('timestamp', 0)

    # Initialize summarization service
    service = SummarizationService(config.summarization)

    # Run summarization
    print("\nRunning summarization...")
    result = await service.summarize_all_levels(
        transcript_buffer=tokens,
        session_start_ms=session_start_ms,
        patient_name=patient_name,
        level_names=levels,
    )

    if not result.success:
        print(f"\nSummarization failed!")
        if result.error_report:
            print(result.error_report)
        sys.exit(1)

    # Build output
    output_lines = [
        f"סיכום פגישה טיפולית",
        f"מטופל/ת: {patient_name}",
        f"",
    ]

    for level_result in result.level_results:
        output_lines.append(f"---")
        output_lines.append(f"")
        output_lines.append(f"**{level_result.level_label_he}**")
        output_lines.append(f"")
        output_lines.append(level_result.content)
        output_lines.append(f"")

    output_lines.append(f"---")
    output_lines.append(f"נוצר באמצעות AI")

    content = '\n'.join(output_lines)

    # Print cost summary
    print(f"\nResults:")
    for lr in result.level_results:
        print(f"  {lr.level_label_he}: {lr.chunk_count} chunks, ${lr.cost_usd:.4f}")
    print(f"  Total: ${result.total_cost_usd:.4f}")

    # Save output
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nSaved to: {output_path}")
    else:
        # Default output path: same dir as transcript, with _summary suffix
        default_output = Path(transcript_path).stem + '_summary.txt'
        with open(default_output, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nSaved to: {default_output}")

    return content


def main():
    parser = argparse.ArgumentParser(
        description='Run offline summarization on transcript files'
    )
    parser.add_argument(
        '--transcript', '-t',
        required=True,
        help='Path to transcript file'
    )
    parser.add_argument(
        '--patient', '-p',
        required=True,
        help='Patient name'
    )
    parser.add_argument(
        '--level', '-l',
        choices=['quick', 'standard', 'clinical'],
        help='Run a specific summary level'
    )
    parser.add_argument(
        '--all-levels', '-a',
        action='store_true',
        help='Run all 3 summary levels'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: {transcript_name}_summary.txt)'
    )

    args = parser.parse_args()

    # Determine which levels to run
    if args.all_levels:
        levels = ['quick', 'standard', 'clinical']
    elif args.level:
        levels = [args.level]
    else:
        levels = ['standard']  # Default

    # Validate transcript file exists
    if not os.path.exists(args.transcript):
        print(f"Error: Transcript file not found: {args.transcript}")
        sys.exit(1)

    # Run
    asyncio.run(run_summary(
        transcript_path=args.transcript,
        patient_name=args.patient,
        levels=levels,
        output_path=args.output,
    ))


if __name__ == '__main__':
    main()
