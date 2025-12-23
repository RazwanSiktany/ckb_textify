import argparse
import sys
from pathlib import Path

from ckb_textify.core.pipeline import Pipeline
from ckb_textify.core.types import NormalizationConfig


def main():
    parser = argparse.ArgumentParser(
        description="🦁 ckb-textify: Advanced Kurdish Text Normalizer"
    )

    # Input/Output
    # 'nargs="?"' makes the argument optional. If missing, we check stdin.
    parser.add_argument("input", nargs="?", help="Input text file or raw string (reads from stdin if omitted)")
    parser.add_argument("-o", "--output", help="Output file path (optional)")

    # Flags to DISABLE features
    parser.add_argument("--no-numbers", action="store_true", help="Disable number conversion")
    parser.add_argument("--no-web", action="store_true", help="Disable URL/Email expansion")
    parser.add_argument("--no-phone", action="store_true", help="Disable Phone Number expansion")
    parser.add_argument("--no-units", action="store_true", help="Disable unit expansion")
    parser.add_argument("--no-tech", action="store_true", help="Disable technical IDs")
    parser.add_argument("--no-math", action="store_true", help="Disable math logic")
    parser.add_argument("--no-diacritics", action="store_true", help="Keep Arabic diacritics")

    # Flags to ENABLE specific behaviors
    parser.add_argument("--pause", action="store_true", help="Enable pause markers (|) for TTS rhythm")

    args = parser.parse_args()

    # 1. Load Input
    input_text = ""

    if args.input:
        # Case A: Argument provided (File path or Raw String)
        input_path = Path(args.input)
        if input_path.exists() and input_path.is_file():
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    input_text = f.read()
            except Exception as e:
                print(f"❌ Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # Treat argument as raw text
            input_text = args.input
    else:
        # Case B: No argument provided -> Read from STDIN
        if sys.stdin.isatty():
            # If run interactively without arguments and no pipe, show help
            parser.print_help()
            sys.exit(0)

        try:
            input_text = sys.stdin.read()
        except Exception as e:
            print(f"❌ Error reading from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Configure Pipeline
    config = NormalizationConfig(
        enable_numbers=not args.no_numbers,
        enable_web=not args.no_web,
        enable_phone=not args.no_phone,
        enable_units=not args.no_units,
        enable_technical=not args.no_tech,
        enable_math=not args.no_math,
        enable_diacritics=not args.no_diacritics,
        enable_pause_markers=args.pause,
        emoji_mode="remove"  # Default for CLI
    )

    pipeline = Pipeline(config)

    # 3. Process
    # We write logs to stderr so they don't corrupt the stdout stream if piping
    if args.output or sys.stderr.isatty():
        print(f"🔄 Processing...", file=sys.stderr)

    result = pipeline.normalize(input_text)

    # 4. Output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"✅ Saved to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Error writing file: {e}", file=sys.stderr)
    else:
        # Print to stdout
        print(result)


if __name__ == "__main__":
    main()