from argparse import ArgumentParser
from pathlib import Path

from tools.extract_trace_info import extract_trace_info
# from tools.cli.parse_trace import parse_trace_points

def build(args):
    extract_trace_info(args.elf_data, args.output_file)

    print(f"build {args}")

def convert(args):
    print(f"convert {args}")

def main():
    parser = ArgumentParser(
        description="Tracer CLI tool to help work with trace data generated by tracer"
    )
    subparsers = parser.add_subparsers(title="subcommands", description="valid subcommands")
    build_parser = subparsers.add_parser('build', help="build a json file from the trace mappings sections in an elf file.")
    build_parser.set_defaults(func=build)
    _ = build_parser.add_argument("elf_data", type=Path)
    _ = build_parser.add_argument("output_file", type=Path)

    convert_parser = subparsers.add_parser('convert', help="convert a trace file genertead by tracer into a usable format.")
    convert_parser.set_defaults(func=convert)
    _ = convert_parser.add_argument("mapping", default=None ,type=Path)
    _ = convert_parser.add_argument("trace_file", type=Path)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()