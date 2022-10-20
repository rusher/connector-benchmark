module.exports.title = 'select 100 int/varchar(32) - BINARY';
module.exports.displaySql = 'select * FROM test100';
module.exports.requireExecute = true;
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.execute('select * FROM test100');
  deferred.resolve(res);
};
