#!/usr/bin/env python
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Runs multiple commands concated with '&&'.

This script exists to avoid using complex shell commands in
gcc_toolchain.gni's tool("solink_module") and tool("link"), in case the host 
running the compiler does not have a POSIX-like shell (e.g. Windows).
"""

import argparse
import os
import subprocess
import sys


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('command', nargs='+',
                      help='Linking command')
  args = parser.parse_args()

  cmd = []
  for index in range(len(args.command) + 1):
    if index == len(args.command) or args.command[index] == '&&':
      result = subprocess.call(cmd)
      if result != 0:
        return result
      cmd = []
    else:
      cmd.append(args.command[index])

  return result


if __name__ == "__main__":
  sys.exit(main())
