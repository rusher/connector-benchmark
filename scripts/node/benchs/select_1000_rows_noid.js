module.exports.title = 'select 1000 rows - rowsAsArray';
module.exports.displaySql = 'select * from 1000 rows (int + string(32)) - rowsAsArray';
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.query({sql:"select * from 1000rows", rowsAsArray:true});
  deferred.resolve(res);
};
