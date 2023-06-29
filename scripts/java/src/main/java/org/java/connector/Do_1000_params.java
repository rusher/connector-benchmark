// SPDX-License-Identifier: LGPL-2.1-or-later
// Copyright (c) 2012-2014 Monty Program Ab
// Copyright (c) 2015-2021 MariaDB Corporation Ab

package org.java.connector;

import java.sql.PreparedStatement;
import org.openjdk.jmh.annotations.Benchmark;

public class Do_1000_params extends Common {

  private static final String sql;

  static {
    StringBuilder sb = new StringBuilder("do ?");
    for (int i = 1; i < 1000; i++) {
      sb.append(",?");
    }
    sql = sb.toString();
  }

  @Benchmark
  public int text(MyState state) throws Throwable {
    try (PreparedStatement st = state.connectionText.prepareStatement(sql)) {
      for (int i = 1; i <= 1000; i++) {
        st.setInt(i, i);
      }
      return st.executeUpdate();
    }
  }

  @Benchmark
  public int binary(MyState state) throws Throwable {
    try (PreparedStatement st = state.connectionBinary.prepareStatement(sql)) {
      for (int i = 1; i <= 1000; i++) {
        st.setInt(i, i);
      }
      return st.executeUpdate();
    }
  }
}
