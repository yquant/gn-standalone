// Copyright 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "testing/gtest/include/gtest/gtest.h"

#include "example_lib.h"

TEST(StaticLibTest, Add) {
  int a = 123;
  int b = 321;
  EXPECT_EQ(a + b, example_lib_do_add(a, b));
}

