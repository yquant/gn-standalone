@echo off
:: Copyright 2013 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

:: This is required with cygwin only.
PATH=%~dp0;%PATH%

set DEPOT_TOOLS_WIN_TOOLCHAIN=0

%~dp0\..\src\buildtools\win\gn.exe %*
