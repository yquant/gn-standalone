@echo off
:: Copyright (c) 2012 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

:: This is required with cygwin only.
PATH=%~dp0;%PATH%

set TaskFile="download_%1.tasks"

if not exist "%TaskFile%" (
  echo Usage: %~n0 ^<task^>
  echo ^<task^> is the download task to be run.
  echo Example: %~n0 gn
  goto :EOF
)

:: Defer control.
python "%~dp0\download.py" runtasks --tasksfile %TaskFile%
