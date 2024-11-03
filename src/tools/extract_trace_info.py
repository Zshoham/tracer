import os
import re
import json
import shlex
import struct
import subprocess
from pathlib import Path
from argparse import ArgumentParser
from dataclasses import asdict, dataclass, field, is_dataclass

from fnvhash import fnv1a_32
from elftools.elf.elffile import ELFFile

FUNCTION_TRACE_SECTION_NAME = ".trace_info"
METHOD_TRACE_SECTION_NAME = ".trace_info_c"
MAPPING_SEPERATOR = b"\x00"
OBJDUMP_ADDRESS_REGEX = r"(?P<file>\S+)\s+(?P<line>\d+)\s+(?P<address>\w+).+"


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Path):
            return str(o)
        return super().default(o)


@dataclass
class BasicTracePoint:
    elf: Path
    trace_counter: int
    file: Path
    line: int
    message: str
    is_method: bool
    trace_id: int = field(init=False)
    file_hash: int = field(init=False)

    def __post_init__(self):
        self.file_hash = fnv1a_32(self.file.as_posix().encode())
        self.trace_id = struct.unpack(
            ">Q", struct.pack(">IHH", self.file_hash, self.line, self.trace_counter - 2)
        )[0]


@dataclass
class EnhancedTracePoint(BasicTracePoint):
    address: str
    signature: str
    namespace: list[str] = field(default_factory=list)
    classs: str | None = None

    def __post_init__(self):
        super().__post_init__()
        name_components = self.signature.split("::")[:-1]
        if self.is_method:
            self.classs = name_components[-1]
            name_components = name_components[:-1]

        if name_components:
            self.namespace = name_components

    @classmethod
    def from_basic(cls, basic: BasicTracePoint, address: str):
        return EnhancedTracePoint(
            elf=basic.elf,
            trace_counter=basic.trace_counter,
            file=basic.file,
            line=basic.line,
            message=basic.message,
            is_method=basic.is_method,
            address=address,
            signature=get_location_signature(basic.elf.as_posix(), address),
        )


def get_trace_section_data(
    elf_file, section, is_method: bool = False
) -> BasicTracePoint:
    mapping = section.data()
    parts = mapping.decode().split("$")
    trace_point = BasicTracePoint(
        elf_file, int(parts[0]), Path(parts[1]), int(parts[2]), parts[3], is_method
    )
    return trace_point


def get_location_signature(elf_path: str, address: str) -> str:
    signature, *_other = subprocess.check_output(
        shlex.split(f"addr2line -e {elf_path} -fC {address}"), text=True
    ).splitlines()
    return signature


def enhance_with_debug_info(
    elf_path: str, basic_traces: dict[int, BasicTracePoint]
) -> dict[int, EnhancedTracePoint]:
    enhanced_traces = {}
    address_regex = re.compile(OBJDUMP_ADDRESS_REGEX)
    objdump_output = subprocess.check_output(
        shlex.split(f"objdump --dwarf=decodedline {elf_path}"), text=True
    )
    location_address_map = {
        (a[0], int(a[1])): a[2] for a in address_regex.findall(objdump_output)
    }
    for id, trace in basic_traces.items():
        address = location_address_map[
            (os.path.basename(trace.file.as_posix()), trace.line)
        ]
        enhanced_traces[id] = EnhancedTracePoint.from_basic(trace, address)
    return enhanced_traces


def extract_trace_info(elf_file: Path, output_file: Path):
    basic_trace_info = {}
    with open(elf_file, "rb") as elf_fd:
        elf_data = ELFFile(elf_fd)
        for trace_section in (
            sec for sec in elf_data.iter_sections() if "trace_info" in sec.name
        ):
            trace_data = get_trace_section_data(elf_file, trace_section)
            basic_trace_info[trace_data.trace_id] = trace_data

    enhanced_trace_info = enhance_with_debug_info(elf_file.as_posix(), basic_trace_info)

    with open(output_file, "w+") as json_file:
        json.dump(enhanced_trace_info, json_file, cls=EnhancedJSONEncoder)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Extract tracer trace mappings from an elf file and write it to a file as json"
    )
    _ = parser.add_argument("elf_data", type=Path)
    _ = parser.add_argument("output_file", type=Path)

    args = parser.parse_args()
    extract_trace_info(args.elf_data, args.output_file)
