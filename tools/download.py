#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Run tasks."""
# Files
#   download.tasks : Default task file which contains download tasks to be performed
#
# Tasks
#   Task files contain a list named "task" to allow custom actions to be performed.
#   Tasks can run with the "runtasks" operation.
#
#   Each item in a "tasks" list is a dict, containing these two keys:
#     "action"   A list describing a command to run along with its arguments, if
#                any.  An action command will run at most one time per gclient
#                invocation, regardless of how many files matched the pattern.
#                The action is executed in the same directory as the .gclient
#                file.  If the first item in the list is the string "python",
#                the current Python interpreter (sys.executable) will be used
#                to run the command. If the list contains string
#                "$matching_files" it will be removed from the list and the list
#                will be extended by the list of matching files.
#     "name"     An optional string specifying the group to which a task belongs
#                for overriding and organizing.
#
#   Example:
#     tasks = [
#       { "action":  ["python", "image_indexer.py", "--all"]},
#       { "name": "gyp",
#         "action":  ["python", "src/build/gyp_chromium"]},
#     ]

__version__ = '0.7'

import copy
import json
import logging
import optparse
import os
import platform
import posixpath
import pprint
import re
import sys
import time
import urllib
import urlparse

import fix_encoding
import gclient_utils
import subcommand
import subprocess2
from third_party import colorama


class GClientKeywords(object):
  class VarImpl(object):
    def __init__(self, custom_vars, local_scope):
      self._custom_vars = custom_vars
      self._local_scope = local_scope

    def Lookup(self, var_name):
      """Implements the Var syntax."""
      if var_name in self._custom_vars:
        return self._custom_vars[var_name]
      elif var_name in self._local_scope.get("vars", {}):
        return self._local_scope["vars"][var_name]
      raise gclient_utils.Error("Var is not defined: %s" % var_name)


class TasksSettings(GClientKeywords):
  """Immutable configuration settings."""
  def __init__(
      self, custom_vars,
      custom_tasks, root_dir, tasks_file):
    GClientKeywords.__init__(self)

    # These are not mutable:
    self._root_dir = root_dir
    self._tasks_file = tasks_file

    self._custom_vars = custom_vars or {}
    self._custom_tasks = custom_tasks or []

    # Make any tasks_file path platform-appropriate.
    for sep in ['/', '\\']:
      self._tasks_file = self._tasks_file.replace(sep, os.sep)

  @property
  def root_dir(self):
    return self._root_dir

  @property
  def tasks_file(self):
    return self._tasks_file

  @property
  def custom_vars(self):
    return self._custom_vars.copy()

  @property
  def custom_tasks(self):
    return self._custom_tasks[:]


class Tasks(gclient_utils.WorkItem, TasksSettings):
  """Object that represents a task."""

  def __init__(self, name,
               custom_vars, custom_tasks, root_dir, tasks_file):
    gclient_utils.WorkItem.__init__(self, name)
    TasksSettings.__init__(
        self, custom_vars,
        custom_tasks, root_dir, tasks_file)

    self._tasks = []
    self.tasks_content = None
    self.ParseTasksFile()

  def ParseTasksFile(self):
    """Parses the tasks file for this tasks."""

    tasks_content = None
    use_strict = False
    filepath = os.path.join(self.root_dir, self.tasks_file)
    if not os.path.isfile(filepath):
      logging.info(
          'ParseTasksFile(%s): No %s file found at %s' % (
            self.name, self.tasks_file, filepath))
    else:
      tasks_content = gclient_utils.FileRead(filepath)
      logging.debug('ParseTasksFile(%s) read:\n%s' % (self.name, tasks_content))
      use_strict = 'use strict' in tasks_content.splitlines()[0]

    local_scope = {}
    if tasks_content:
      # One thing is unintuitive, vars = {} must happen before Var() use.
      var = self.VarImpl(self.custom_vars, local_scope)
      if use_strict:
        logging.info(
          'ParseTasksFile(%s): Strict Mode Enabled', self.name)
        global_scope = {
          '__builtins__': {'None': None},
          'Var': var.Lookup,
          'tasks_os': {},
        }
      else:
        global_scope = {
          'Var': var.Lookup,
          'tasks_os': {},
        }
      # Eval the content.
      try:
        exec(tasks_content, global_scope, local_scope)
      except SyntaxError, e:
        gclient_utils.SyntaxErrorToError(filepath, e)
      if use_strict:
        for key, val in local_scope.iteritems():
          if not isinstance(val, (dict, list, tuple, str)):
            raise gclient_utils.Error(
              'ParseTasksFile(%s): Strict mode disallows %r -> %r' %
              (self.name, key, val))

    # override named sets of tasks by the custom tasks
    tasks_to_run = []
    task_names_to_suppress = [c.get('name', '') for c in self.custom_tasks]
    for task in local_scope.get('tasks', []):
      if task.get('name', '') not in task_names_to_suppress:
        tasks_to_run.append(task)

    # add the replacements and any additions
    for task in self.custom_tasks:
      if 'action' in task:
        tasks_to_run.append(task)

    self.tasks_content = tasks_content
    self._tasks = tasks_to_run
    logging.info('ParseTasksFile(%s) done' % self.name)

  @staticmethod
  def GetTaskAction(task_dict):
    """Turns a parsed 'task' dict into an executable command."""
    logging.debug(task_dict)
    command = task_dict['action'][:]
    if command[0] == 'python':
      # If the task specified "python" as the first item, the action is a
      # Python script.  Run it by starting a new copy of the same
      # interpreter.
      command[0] = sys.executable
    return command

  def Run(self, command, args):
    if command != 'runtasks':
      print "No run tasks, only show task info"
      for task in self.tasks:
        print "Task '%s':\n  action: %s" % (task['name'], gclient_utils.CommandToStr(self.GetTaskAction(task)))
      return
    for task in self.tasks:
      try:
        start_time = time.time()
        action = self.GetTaskAction(task)
        gclient_utils.CheckCallAndFilterAndHeader(
            action, cwd=self.root_dir, always=True)
      except (gclient_utils.Error, subprocess2.CalledProcessError), e:
        # Use a discrete exit status code of 2 to indicate that a task action
        # failed.  Users of this script may wish to treat task action failures
        # differently from VC failures.
        print >> sys.stderr, 'Error: %s' % str(e)
        sys.exit(2)
      finally:
        elapsed_time = time.time() - start_time
        if elapsed_time > 5:
          print "Task '%s' took %.2f secs" % (task['name'], elapsed_time)

  @property
  @gclient_utils.lockedmethod
  def tasks(self):
    return tuple(self._tasks)

  def __str__(self):
    out = []
    for i in ('name',
              'custom_vars', 'tasks', 'tasks_file'):
      # First try the native property if it exists.
      if hasattr(self, '_' + i):
        value = getattr(self, '_' + i, False)
      else:
        value = getattr(self, i, False)
      if value:
        out.append('%s: %s' % (i, value))

    for d in self.tasks:
      out.extend(['  ' + x for x in str(d).splitlines()])
      out.append('')
    return '\n'.join(out)


class LClient(Tasks):
  """Object that represent a lclient tasks."""

  def __init__(self, options):
    Tasks.__init__(self, None, None, None,
                        options.root_dir, options.tasks_filename)
    self._options = options


#### lclient commands.


def CMDruntasks(parser, args):
  """Runs tasks."""
  (options, args) = parser.parse_args(args)
  client = LClient(options)
  if options.verbose:
    # Print out the tasks file.  This is longer than if we just printed the
    # client dict, but more legible, and it might contain helpful comments.
    print(client.tasks_content)
  return client.Run('runtasks', args)


def CMDtaskinfo(parser, args):
  """Outputs the tasks that would be run by `lclient runtasks`."""
  (options, args) = parser.parse_args(args)
  client = LClient(options)
  client.Run(None, [])
  return 0


class OptionParser(optparse.OptionParser):
  root_dir_default = os.path.dirname(os.path.realpath(__file__))
  tasksfile_default = os.environ.get('TASKS_FILE', 'download.tasks')

  def __init__(self, **kwargs):
    optparse.OptionParser.__init__(
        self, version='%prog ' + __version__, **kwargs)

    self.add_option(
        '-v', '--verbose', action='count', default=0,
        help='Produces additional output for diagnostics. Can be used up to '
             'three times for more logging info.')
    self.add_option(
        '--rootdir', dest='root_dir',
        help='Specify an alternate root dir')
    self.add_option(
        '--tasksfile', dest='tasks_filename',
        help='Specify an alternate tasks file')

  def parse_args(self, args=None, values=None):
    """Integrates standard options processing."""
    options, args = optparse.OptionParser.parse_args(self, args, values)
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        level=levels[min(options.verbose, len(levels) - 1)],
        format='%(module)s(%(lineno)d) %(funcName)s:%(message)s')
    if (options.tasks_filename and
        options.tasks_filename != os.path.basename(options.tasks_filename)):
      self.error('--tasksfile target must be a filename, not a path')
    if not options.root_dir:
      options.root_dir = self.root_dir_default
    if not options.tasks_filename:
      options.tasks_filename = self.tasksfile_default
    return (options, args)


def disable_buffering():
  # Make stdout auto-flush so buildbot doesn't kill us during lengthy
  # operations. Python as a strong tendency to buffer sys.stdout.
  sys.stdout = gclient_utils.MakeFileAutoFlush(sys.stdout)
  # Make stdout annotated with the thread ids.
  sys.stdout = gclient_utils.MakeFileAnnotated(sys.stdout)


def Main(argv):
  """Doesn't parse the arguments here, just find the right subcommand to
  execute."""
  if sys.hexversion < 0x02060000:
    print >> sys.stderr, (
        '\nYour python version %s is unsupported, please upgrade.\n' %
        sys.version.split(' ', 1)[0])
    return 2
  if not sys.executable:
    print >> sys.stderr, (
        '\nPython cannot find the location of it\'s own executable.\n')
    return 2
  fix_encoding.fix_encoding()
  disable_buffering()
  colorama.init()
  dispatcher = subcommand.CommandDispatcher(__name__)
  try:
    return dispatcher.execute(OptionParser(), argv)
  except KeyboardInterrupt:
    gclient_utils.GClientChildren.KillAllRemainingChildren()
    raise
  except (gclient_utils.Error, subprocess2.CalledProcessError), e:
    print >> sys.stderr, 'Error: %s' % str(e)
    return 1
  finally:
    gclient_utils.PrintWarnings()


if '__main__' == __name__:
  sys.exit(Main(sys.argv[1:]))

# vim: ts=2:sw=2:tw=80:et:
