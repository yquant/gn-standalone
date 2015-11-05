#include <iostream>

#include "example_lib.h"
#include "example_shlib.h"

void usage()
{
  std::cout << "Usage: example_app <number1> <number2>" << std::endl;
  exit(-1);
}

int main(int argc, const char* argv[])
{
  if (argc < 3)
    usage();

  int num1 = atoi(argv[1]);
  int num2 = atoi(argv[2]);
  if ((num1 == 0 && argv[1][0] != '0') ||(num2 == 0 && argv[2][0] != '0'))
    usage();

  int ret = num1 + num2;
  int ret1 = example_lib_do_add(num1, num2);
  int ret2 = example_shlib_do_add(num1, num2);

  std::cout << "Add result should be " << ret << std::endl
            << "  static lib add result is " << ret1 << std::endl
            << "  shared lib add result is " << ret2 << std::endl;

  return 0;
}
