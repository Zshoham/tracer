#include <iostream>
#include <fstream>
#include <atomic>
#include <shared_mutex>

#include "tracer.hpp"

static std::array<trace_point, TRACE_BUFFER_SIZE> trace_buffer;
static std::atomic_size_t trace_buffer_index = 0;
static std::shared_mutex flush_mutex;

uint64_t time_ns() {
  struct timespec tv;
  clock_gettime(CLOCK_REALTIME, &tv);
  return tv.tv_sec * 1000000000 + tv.tv_nsec;
}

void trace_to_buffer(uint64_t location) {
  // here we do a shared lock since 
  // we allow concurrent trace calls (atomic index),
  // but we dont allow tracing and flushing concurrently.
  flush_mutex.lock_shared();
  size_t index = trace_buffer_index.fetch_add(1, std::memory_order_relaxed);
  trace_buffer[index % TRACE_BUFFER_SIZE] = {location, time_ns()};
  flush_mutex.unlock_shared();
  
  if (index > trace_buffer.max_size()) {
    flush_trace_buffer(trace_buffer);
  }
}

bool flush_trace_buffer(std::array<trace_point, TRACE_BUFFER_SIZE> &traces) {
    std::ofstream outFile("trace_output.tracer", std::ios::binary | std::ios::app);

    if (!outFile) {
        return false;  // Failed to open file
    }

    // here we do an exclusive lock since when we flush nothing 
    // else can touch the buffer.
    flush_mutex.lock();
    while (trace_buffer_index > 0) {
        size_t index = trace_buffer_index.fetch_sub(1, std::memory_order_relaxed);
        trace_point t = trace_buffer[index];
        outFile.write(reinterpret_cast<const char*>(&t), sizeof(trace_point));
    }
    flush_mutex.unlock();

    outFile.close();
    return true;
}


