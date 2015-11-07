// Copyright 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "testing/gtest/include/gtest/gtest.h"

#include "example_shlib.h"

TEST(SharedLibTest, Add) {
  int a = 234;
  int b = 456;
  EXPECT_EQ(a + b, example_shlib_do_add(a, b));
}

