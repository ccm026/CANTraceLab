"""Command-line entry point for milestone 1."""

import argparse

from .trace import load_frames, summarize


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an offline CAN trace")
    parser.add_argument("file", help="Path to .log, .asc or .blf CAN trace")
    args = parser.parse_args()
    try:
        frames = load_frames(args.file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    stats = summarize(frames)
    print(f"Frames: {stats['frames']}")
    print(f"Unique CAN IDs: {stats['unique_ids']}")
    print(f"Duration: {stats['duration_s']} seconds")
    print("First frames:")
    for frame in frames[:10]:
        print(
            f"  {frame.timestamp:.6f} {frame.channel or '-':8} "
            f"0x{frame.arbitration_id:X}  {frame.data.hex(' ').upper()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
