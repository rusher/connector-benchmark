module.exports.title = 'select 1000 rows - rowsAsArray';
module.exports.displaySql = 'select * from 1000 rows (int + string(32)) - rowsAsArray';
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.query({sql:"select seq, 'abcdefghijabcdefghijabcdefghijaa' from seq_1_to_1000", rowsAsArray:true});
  deferred.resolve(res);
};
