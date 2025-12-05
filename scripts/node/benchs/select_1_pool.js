// SPDX-License-Identifier: LGPL-2.1-or-later
// Copyright (c) 2012-2014 Monty Program Ab
// Copyright (c) 2015-2025 MariaDB Corporation Ab

'use strict';

const assert = require('assert');

module.exports.title = 'SELECT 1 - pool (16 connections, 100 concurrent)';
module.exports.displaySql = 'SELECT 1 (pooled)';
module.exports.requiresPool = true;
module.exports.poolSize = 16;
module.exports.concurrentTasks = 100;

/**
 * Benchmark SELECT 1 with connection pool
 * Uses a pool of 16 connections to execute 100 concurrent SELECT 1 queries
 */
module.exports.benchFct = async function (pool, type, deferred) {
  const promises = [];
  
  // Execute 100 concurrent SELECT 1 queries
  for (let i = 0; i < module.exports.concurrentTasks; i++) {
    promises.push(
      pool.query('SELECT 1')
    );
  }
  
  await Promise.all(promises);
  deferred.resolve();
};
