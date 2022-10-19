module.exports.title = 'select 1000 rows - BINARY';
module.exports.displaySql = 'select * from 1000 rows (int + string(32)) - BINARY';
module.exports.requireExecute = true;
module.exports.benchFct = async function (conn, type, deferred) {
  const res = await conn.execute("select seq, 'abcdefghijabcdefghijabcdefghijaa' from seq_1_to_1000");
  deferred.resolve(res);
};
