#ifndef EXAMPLE_SHLIB_H_
#define EXAMPLE_SHLIB_H_

#if defined(WIN32)

 #if defined(EXAMPLE_SHLIB_IMPLEMENTATION)
  #define EXAMPLE_SHLIB_EXPORT __declspec(dllexport)
  #define EXAMPLE_SHLIB_EXPORT_PRIVATE __declspec(dllexport)
 #else
  #define EXAMPLE_SHLIB_EXPORT __declspec(dllimport)
  #define EXAMPLE_SHLIB_EXPORT_PRIVATE __declspec(dllimport)
 #endif  // defined(EXAMPLE_SHLIB_IMPLEMENTATION)
 
#else  // defined(WIN32)

 #if defined(EXAMPLE_SHLIB_IMPLEMENTATION)
  #define EXAMPLE_SHLIB_EXPORT __attribute__((visibility("default")))
  #define EXAMPLE_SHLIB_EXPORT_PRIVATE __attribute__((visibility("default")))
 #else
  #define EXAMPLE_SHLIB_EXPORT
  #define EXAMPLE_SHLIB_EXPORT_PRIVATE
 #endif  // defined(EXAMPLE_SHLIB_IMPLEMENTATION)
 
#endif  // !defined(WIN32)

extern "C" {
  EXAMPLE_SHLIB_EXPORT int example_shlib_do_add(int a, int b);
}

#endif // EXAMPLE_SHLIB_H_
