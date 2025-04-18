// SPDX-License-Identifier: LGPL-2.1-or-later
// Copyright (c) 2012-2014 Monty Program Ab
// Copyright (c) 2015-2021 MariaDB Corporation Ab

package org.java.connector;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.Properties;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

@State(Scope.Benchmark)
@Warmup(iterations = 7, timeUnit = TimeUnit.SECONDS, time = 1)
@Measurement(iterations = 7, timeUnit = TimeUnit.SECONDS, time = 1)
@Fork(value = 5)
@Threads(value = 1)
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
public class Common {

  // conf
  public static final String host = getEnv("TEST_DB_HOST", "localhost");
  public static final int port = Integer.parseInt(getEnv("TEST_DB_PORT", "3306"));
  public static final String username = getEnv("TEST_DB_USER", "root");
  public static final String password = getEnv("TEST_DB_PASSWORD", "");
  public static final String database = getEnv("TEST_DB_DATABASE", "testj");
  public static final String other = getEnv("TEST_DB_OTHER", "");
  public static final boolean useSSL = Boolean.parseBoolean(getEnv("TEST_USE_SSL", "false"));

  public static String getEnv(String key, String defaultValue) {
    String env = System.getenv(key);
    if (env != null) return env;
    return defaultValue;
  }

  @State(Scope.Thread)
  public static class MyState {

    // connections
    protected Connection connectionText;
    protected Connection connectionTextRewrite;

    protected Connection connectionBinary;

    protected Connection connectionBinaryNoPipeline;
    protected Connection connectionBinaryNoCache;

    @Param({"mysql", "mariadb"})
    String driver;

    @Setup(Level.Trial)
    public void createConnections() throws Exception {

      String className;
      switch (driver) {
        case "mysql":
          className = "com.mysql.cj.jdbc.Driver";
          break;
        case "mariadb":
          className = "org.mariadb.jdbc.Driver";
          break;
        default:
          throw new RuntimeException("wrong param");
      }
      try {
        String jdbcBase =
            "jdbc:%s://%s:%s/%s?user=%s&password=%s&sslMode=%s&useServerPrepStmts=%s&cachePrepStmts=%s&serverTimezone=UTC%s";
        String jdbcUrlText =
            String.format(
                jdbcBase,
                driver,
                host,
                port,
                database,
                username,
                password,
                useSSL ? "REQUIRED" : "DISABLED",
                false,
                true,
                "&useBulkStmts=false" + other);
        String jdbcUrlBinary =
            String.format(
                jdbcBase,
                driver,
                host,
                port,
                database,
                username,
                password,
                useSSL ? "REQUIRED" : "DISABLED",
                true,
                true,
                "&useBulkStmts=true" + other);

        connectionText =
            ((java.sql.Driver) Class.forName(className).getDeclaredConstructor().newInstance())
                .connect(jdbcUrlText, new Properties());
        String jdbcUrlTextRewrite =
            String.format(
                jdbcBase,
                driver,
                host,
                port,
                database,
                username,
                password,
                useSSL ? "REQUIRED" : "DISABLED",
                false,
                false,
                "&rewriteBatchedStatements=true&useBulkStmts=false" + other);
        connectionTextRewrite =
            ((java.sql.Driver) Class.forName(className).getDeclaredConstructor().newInstance())
                .connect(jdbcUrlTextRewrite, new Properties());
        connectionBinary =
            ((java.sql.Driver) Class.forName(className).getDeclaredConstructor().newInstance())
                .connect(jdbcUrlBinary, new Properties());

        String jdbcUrlBinaryNoCache =
            String.format(
                jdbcBase,
                driver,
                host,
                port,
                database,
                username,
                password,
                useSSL ? "REQUIRED" : "DISABLED",
                true,
                false,
                "&prepStmtCacheSize=0" + other);

        connectionBinaryNoCache =
            ((java.sql.Driver) Class.forName(className).getDeclaredConstructor().newInstance())
                .connect(jdbcUrlBinaryNoCache, new Properties());

        String jdbcUrlBinaryNoCacheNoPipeline =
            String.format(
                jdbcBase,
                driver,
                host,
                port,
                database,
                username,
                password,
                useSSL ? "REQUIRED" : "DISABLED",
                true,
                true,
                "&prepStmtCacheSize=0&cachePrepStmts=false&disablePipeline=true" + other);
        connectionBinaryNoPipeline =
            ((java.sql.Driver) Class.forName(className).getDeclaredConstructor().newInstance())
                .connect(jdbcUrlBinaryNoCacheNoPipeline, new Properties());
      } catch (SQLException e) {
        e.printStackTrace();
        throw new RuntimeException(e);
      }
    }

    @TearDown(Level.Trial)
    public void doTearDown() throws SQLException {
      connectionText.close();
      connectionBinary.close();
      connectionTextRewrite.close();
      connectionBinaryNoCache.close();
      connectionBinaryNoPipeline.close();
    }
  }
}
