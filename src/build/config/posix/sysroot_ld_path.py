# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This file takes two arguments, the relative location of the shell script that
# does the checking, and the name of the sysroot.

# TODO(brettw) the build/linux/sysroot_ld_path.sh script should be rewritten in
# Python in this file.

import sys
import os

def process_ld_so_conf(ld_so_conf):
  result = ''
  f = open(ld_so_conf)
  for line in fh.readlines():
    if line.startswith('include'):
      include_file = line[7:].strip()
      if not include_file.startswith('/'):
        include_file = os.path.join(os.path.dirname(ld_so_conf), include_file)
      result += process_ld_so_conf(include_file)
    elif line.startswith('/'):
      result += "-L%s -Wl,-rpath-link=%s " % (entry, entry)
  f.close()


def main():
  if len(sys.argv) != 2:
    print "Need one argument"
    sys.exit(1)

  sysroot = sys.argv[1]
  ld_so_conf = os.path.join(sysroot, 'etc', 'ld.so.conf')
  ld_so_conf_d = os.path.join(sysroot, 'etc', 'ld.so.conf.d')

  result = ''
  if os.path.isfile(ld_so_conf):
    result += process_ld_so_conf(ld_so_conf)
  elif os.path.isdir(ld_so_conf_d):
    for file in os.listdir(ld_so_conf_d):
      if file.endswith('.conf'):
        result += process_ld_so_conf(os.path.join(ld_so_conf_d, file))

  print '"' + result.strip() + '"'
  return 0


if __name__ == '__main__':
  sys.exit(main())

