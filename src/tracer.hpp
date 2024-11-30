#include <array>
#include <cstdint>
#include <string_view>

#define TRACE_BUFFER_SIZE 1024
#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)

constexpr uint32_t fnv1a_hash(std::string_view str) {
  // fnv1a implementation adapted from:
  // http://www.isthe.com/chongo/src/fnv/hash_32a.c
  constexpr uint32_t fnv_prime = 0x01000193;
  uint32_t result = 0x811c9dc5;
  for (char c : str) {
    result ^= (uint32_t)c;
    result *= fnv_prime;
  }
  return result;
}

struct trace_id {
  union {
    uint64_t id;
    struct {
      uint32_t file_hash;
      uint16_t line_number;
      uint16_t trace_counter;
    } id_struct;
  };
};

struct trace_point {
  trace_id location;
  uint64_t timestamp;
};

uint64_t time_ns();
bool flush_trace_buffer(std::array<trace_point, TRACE_BUFFER_SIZE> &traces);
void trace_to_buffer(uint64_t location);

#define GCUID()                                                                \
  (((uint64_t)fnv1a_hash(__FILE__) << 32) + ((uint16_t)__LINE__ << 16) +       \
   (uint16_t)__COUNTER__)
#define MAKE_TRACE_MAPPING(message)                                            \
  TOSTRING(__COUNTER__) "$" __FILE__ "$" TOSTRING(__LINE__) "$" message

#define TRACE(message)                                                         \
  do {                                                                         \
    uint64_t traceid = GCUID();                                                \
    static const char trace_mapping[]                                          \
        __attribute__((section(".trace_info" TOSTRING(__COUNTER__)), used)) =  \
            MAKE_TRACE_MAPPING(message);                                       \
    trace_to_buffer(traceid);                                                  \
  } while (0)
