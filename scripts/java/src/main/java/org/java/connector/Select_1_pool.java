// SPDX-License-Identifier: LGPL-2.1-or-later
// Copyright (c) 2012-2014 Monty Program Ab
// Copyright (c) 2015-2025 MariaDB Corporation Ab

package org.java.connector;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;
import java.lang.management.ManagementFactory;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.stream.IntStream;
import javax.management.JMX;
import javax.management.MBeanServer;
import javax.management.ObjectName;
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.infra.Blackhole;

public class Select_1_pool extends Common {

  @Benchmark
  public void select1Pool(MyPoolState state, Blackhole blackHole) throws InterruptedException {
    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
      executeSelect1(state, executor, blackHole);
    }
  }

  private void executeSelect1(MyPoolState state, ExecutorService executor, Blackhole blackHole)
      throws InterruptedException {
    IntStream.range(0, state.numberOfTasks)
        .forEach(
            i ->
                executor.submit(
                    () -> {
                      try (var conn = state.pool.getConnection()) {
                        try (Statement stmt = conn.createStatement()) {
                          try (ResultSet rs = stmt.executeQuery("SELECT 1")) {
                            rs.next();
                            blackHole.consume(rs.getInt(1));
                          }
                        }
                      } catch (SQLException e) {
                        throw new RuntimeException(e);
                      }
                    }));
    executor.shutdown();
    executor.awaitTermination(1, TimeUnit.MINUTES);
  }

  @State(Scope.Benchmark)
  public static class MyPoolState {

    protected HikariDataSource pool;

    @Param({"mariadb", "mysql"})
    String driver;

    @Param({"100"})
    int numberOfTasks;

    @Param({"16"})
    int numberOfConnection;

    @Setup(Level.Trial)
    public void createConnections() throws Exception {

      HikariConfig config = new HikariConfig();
      config.setDriverClassName(
          ("mariadb".equals(driver) ? "org.mariadb.jdbc.Driver" : "com.mysql.cj.jdbc.Driver"));
      config.setJdbcUrl(String.format("jdbc:%s://%s:%s/%s", driver, host, port, database));
      config.setUsername(username);
      config.setPassword(password);

      // in order to compare the same thing with mysql and mariadb driver
      config.addDataSourceProperty("sslMode", "DISABLED");
      config.addDataSourceProperty("serverTimezone", "UTC");

      config.setMaximumPoolSize(numberOfConnection);
      config.setPoolName("benchmark-pool");
      config.setRegisterMbeans(true);
      pool = new HikariDataSource(config);

      // Wait for pool to initialize all connections
      for (int i = 0; i < 100; i++) {
        MBeanServer mBeanServer = ManagementFactory.getPlatformMBeanServer();
        ObjectName poolName = new ObjectName("com.zaxxer.hikari:type=Pool (benchmark-pool)");
        HikariPoolMXBean poolProxy =
            JMX.newMXBeanProxy(mBeanServer, poolName, HikariPoolMXBean.class);
        System.out.println(
            "Total Connections: " + poolProxy.getTotalConnections() + " after " + (i * 0.1) + "s)");
        if (poolProxy.getTotalConnections() == numberOfConnection) break;
        Thread.sleep(100);
      }
    }

    @TearDown(Level.Trial)
    public void doTearDown() throws SQLException {
      pool.close();
    }
  }
}
