module.exports.title = 'select 1000 rows';
module.exports.displaySql = 'select * from 1000 rows (int + string(32))';
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.query("select * from 1000rows");
  deferred.resolve(res);
};
