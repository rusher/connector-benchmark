'use strict';

const fs = require('fs');
const createBenchSuite = require('./common-bench');
const res = {};

const launchBench = async function (path) {
  const bench = require('./benchs/select_1000_rows_execute.js');
  const suite = await createBenchSuite(bench, res);
  suite.run();
};

fs.access('./benchs', async function (err) {
  if (err) {
    fs.access('./benchmarks/benchs', async function (err) {
      await launchBench('./benchmarks/benchs');
    });
  } else {
    await launchBench('./benchs');
  }
});
