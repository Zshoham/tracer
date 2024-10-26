import struct
from dataclasses import dataclass, field
from typing import List


@dataclass
class TraceId:
    """
    Represents the trace_id structure with its union of fields.
    """

    _raw_id: int
    file_hash: int = field(init=False)
    line_number: int = field(init=False)
    trace_counter: int = field(init=False)

    def __post_init__(self):
        raw_bytes = struct.pack("<Q", self._raw_id)
        self.file_hash, self.line_number, self.trace_counter = struct.unpack(
            "<IHH", raw_bytes
        )

    def __repr__(self) -> str:
        return f"TraceId(file_hash={hex(self.file_hash)}, line_number={self.line_number}, trace_counter={self.trace_counter})"


@dataclass
class TracePoint:
    """Represents a trace_point structure."""

    location: TraceId
    timestamp: int


def parse_trace_points(binary_data: bytes) -> List[TracePoint]:
    """
    Parse a byte array containing multiple trace_point structures.

    Args:
        binary_data: Bytes object containing the binary data

    Returns:
        List of TracePoint objects
    """
    format_string = "<QQ"  # Two uint64_t fields
    stride = struct.calcsize(format_string)

    trace_points = []

    # Parse the binary data in chunks
    for i in range(0, len(binary_data), stride):
        chunk = binary_data[i : i + stride]
        if len(chunk) < stride:
            break

        location_id, timestamp = struct.unpack(format_string, chunk)

        trace_point = TracePoint(
            location=TraceId(_raw_id=location_id), timestamp=timestamp
        )
        trace_points.append(trace_point)

    return trace_points
