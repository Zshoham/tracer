#include <iostream>
#include <fstream>

#include "tracer.hpp"

static std::array<trace_point, TRACE_BUFFER_SIZE> trace_buffer;
static size_t trace_buffer_index = 0;

uint64_t time_ns() {
  struct timespec tv;
  clock_gettime(CLOCK_REALTIME, &tv);
  return tv.tv_sec * 1000000000 + tv.tv_nsec;
}

void trace_to_buffer(uint64_t location) {
  trace_buffer[trace_buffer_index++] = {location, time_ns()};
  if (trace_buffer_index > trace_buffer.max_size()) {
    flush_trace_buffer(trace_buffer);
  }
}

bool flush_trace_buffer(std::array<trace_point, TRACE_BUFFER_SIZE> &traces) {
    std::ofstream outFile("trace_output.bin", std::ios::binary | std::ios::app);

    if (!outFile) {
        return false;  // Failed to open file
    }

    while (trace_buffer_index > 0) {
        trace_point t = trace_buffer[trace_buffer_index--];
        outFile.write(reinterpret_cast<const char*>(&t), sizeof(trace_point));
    }

    outFile.close();
    return true;
}


