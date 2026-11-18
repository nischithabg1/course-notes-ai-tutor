"""Command-line entry point: `python -m app.cli --help`."""
import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="course-notes-ai-tutor", description="Students use a simple command-line tutor that learned from their course notes, completing sentences and offering short explanations on concepts to aid revision.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hello", help="check that everything is wired up")
    # TODO: add your own commands here as you work through the milestones.
    args = parser.parse_args(argv)
    if args.command == "hello":
        print("Course Notes AI Tutor is ready. Open README.md for your milestones.")


if __name__ == "__main__":
    main()
