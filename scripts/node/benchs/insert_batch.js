const basechars = '123456789abcdefghijklmnop\\Z';
const chars = basechars.split('');
chars.push('😎');
chars.push('🌶');
chars.push('🎤');
chars.push('🥂');

function randomString(length) {
  let result = '';
  for (let i = length; i > 0; --i) result += chars[Math.round(Math.random() * (chars.length - 1))];
  return result;
}
sqlInsert = 'INSERT INTO perfTestTextBatch(t0) VALUES (?)';

module.exports.title =
  "100 * insert 100 characters using batch method (for mariadb) or loop for other driver (batch doesn't exists)";
module.exports.displaySql = 'INSERT INTO perfTestTextBatch VALUES (?)';
const iterations = 100;
module.exports.benchFct = async function (conn, type, deferred) {
  const params = [randomString(100)];
  // console.log(connType.desc);
  if (type !== 'mariadb') {
    //other driver doesn't have bulk method
    let ended = 0;
    for (let i = 0; i < iterations; i++) {
      const rows = await conn.query(sqlInsert, params);
      if (++ended === iterations) {
        deferred.resolve(rows);
      }
    }
  } else {
    //use batch capability
    const totalParams = new Array(iterations);
    for (let i = 0; i < iterations; i++) {
      totalParams[i] = params;
    }
    const rows = await conn.batch(sqlInsert, totalParams);
    deferred.resolve(rows);
  }
};

module.exports.initFct = async function (conn) {
  const sqlTable =
    "CREATE TABLE perfTestTextBatch (id MEDIUMINT NOT NULL AUTO_INCREMENT,t0 text, PRIMARY KEY (id)) COLLATE='utf8mb4_unicode_ci'";
  try {
    await Promise.all([
      conn.query('DROP TABLE IF EXISTS perfTestTextBatch'),
      conn.query("INSTALL SONAME 'ha_blackhole'"),
      conn.query(sqlTable + ' ENGINE = BLACKHOLE')
    ]);
  } catch (err) {
    await Promise.all([conn.query('DROP TABLE IF EXISTS perfTestTextBatch'), conn.query(sqlTable)]);
  }
};

module.exports.onComplete = async function (conn) {
  await conn.query('TRUNCATE TABLE perfTestTextBatch');
};
