@echo off
:: Copyright 2013 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

:: This is required with cygwin only.
PATH=%~dp0;%PATH%

if "%DEPOT_TOOLS_WIN_TOOLCHAIN%" == "" set DEPOT_TOOLS_WIN_TOOLCHAIN=0

set GN_STANDALONE=%~dp0\win\gn_standalone.exe
set GN=%~dp0\..\src\buildtools\win\gn.exe

if exist %GN_STANDALONE% set GN=%GN_STANDALONE%

%GN% %*
