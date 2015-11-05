#include "example_shlib.h"

extern "C" {

EXAMPLE_SHLIB_EXPORT int example_shlib_do_add(int a, int b) {
  return a + b;
}

}
