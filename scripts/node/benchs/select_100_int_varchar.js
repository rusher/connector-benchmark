module.exports.title = 'select 100 int/varchar(32)';
module.exports.displaySql = 'select * FROM test100';
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.query('select * FROM test100');
  deferred.resolve(res);
};
