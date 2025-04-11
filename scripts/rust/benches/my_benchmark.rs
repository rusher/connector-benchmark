use criterion::{criterion_group, criterion_main, Criterion};
use mysql::*;
use mysql::prelude::*;
use sqlx::{mysql::MySqlPoolOptions, MySql, Pool, Row};
use tokio::runtime::Runtime;
use mysql_async::{Conn as AsyncConn, Pool as AsyncPool, Opts as AsyncOpts};
use mysql_async::prelude::*;


async fn create_connection_pool() -> Pool<MySql> {
    let db_port = std::env::var("TEST_DB_PORT").unwrap_or("3306".to_string());
    let db_database = std::env::var("TEST_DB_DATABASE").unwrap_or("bench".to_string());
    let db_user = std::env::var("TEST_DB_USER").unwrap_or("root".to_string());
    let db_host = std::env::var("TEST_DB_HOST").unwrap_or("127.0.0.1".to_string());
    let db_password = std::env::var("TEST_DB_PASSWORD").unwrap_or("".to_string());

    let connection_string = format!(
        "mysql://{}:{}@{}:{}/{}",
        db_user, db_password, db_host, db_port, db_database
    );

    MySqlPoolOptions::new()
        .max_connections(1) // Equivalent to single connection in the mysql crate benchmark
        .connect(&connection_string)
        .await
        .expect("Failed to create connection pool")
}

async fn create_mysql_async_conn() -> AsyncConn {
    let db_port = std::env::var("TEST_DB_PORT").unwrap_or("3306".to_string());
    let db_database = std::env::var("TEST_DB_DATABASE").unwrap_or("bench".to_string());
    let db_user = std::env::var("TEST_DB_USER").unwrap_or("root".to_string());
    let db_host = std::env::var("TEST_DB_HOST").unwrap_or("127.0.0.1".to_string());
    let db_password = std::env::var("TEST_DB_PASSWORD").unwrap_or("".to_string());

    let connection_string = format!(
        "mysql://{}:{}@{}:{}/{}?prefer_socket=false&stmt_cache_size=128",
        db_user, db_password, db_host, db_port, db_database
    );

    let opts = AsyncOpts::from_url(&connection_string).expect("Unable to parse connection string");
    AsyncConn::new(opts).await.expect("Failed to create async connection")
}

async fn create_mysql_async_pool() -> AsyncPool {
    let db_port = std::env::var("TEST_DB_PORT").unwrap_or("3306".to_string());
    let db_database = std::env::var("TEST_DB_DATABASE").unwrap_or("bench".to_string());
    let db_user = std::env::var("TEST_DB_USER").unwrap_or("root".to_string());
    let db_host = std::env::var("TEST_DB_HOST").unwrap_or("127.0.0.1".to_string());
    let db_password = std::env::var("TEST_DB_PASSWORD").unwrap_or("".to_string());

    let connection_string = format!(
        "mysql://{}:{}@{}:{}/{}?prefer_socket=false&stmt_cache_size=128",
        db_user, db_password, db_host, db_port, db_database
    );

    let opts = AsyncOpts::from_url(&connection_string).expect("Unable to parse connection string");
    AsyncPool::new(opts)
}

fn criterion_benchmark(c: &mut Criterion) {

    let mut group = c.benchmark_group("bench");
    group
        .warm_up_time(std::time::Duration::from_secs(5))
        .measurement_time(std::time::Duration::from_secs(20));

    let runtime = Runtime::new().expect("Failed to create Tokio runtime");
    
    let db_port = std::env::var("TEST_DB_PORT").unwrap_or("3306".to_string());
    let db_database = std::env::var("TEST_DB_DATABASE").unwrap_or("bench".to_string());
    let db_user = std::env::var("TEST_DB_USER").unwrap_or("root".to_string());
    let db_host = std::env::var("TEST_DB_HOST").unwrap_or("127.0.0.1".to_string());
    let db_password = std::env::var("TEST_DB_PASSWORD").unwrap_or("".to_string());
    let opts =
        OptsBuilder::new()
            .user(Some(db_user))
            .db_name(Some(db_database))
            .pass(Some(db_password))
            .tcp_port(db_port.parse::<u16>().unwrap())
            .ip_or_hostname(Some(db_host))
            .prefer_socket(false)
            .stmt_cache_size(128);
    let mut conn = Conn::new(opts).expect("Connection");
    let pool = runtime.block_on(create_connection_pool());
    let asyncPool = runtime.block_on(create_mysql_async_pool());


    // DO 1 benchmark
    group.bench_function("do 1", |b| b.iter(|| {
        let _ = conn.query_drop("DO 1");
        conn.last_insert_id();
    }));

    group.bench_function("sqlx do 1", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let _ = sqlx::query("DO 1").execute(&pool).await.unwrap();
            })
        })
    });

    group.bench_function("mysql_async do 1", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let _ = mysql_async::prelude::Queryable::query_drop(&mut conn, "DO 1").await.unwrap();
                drop(conn);
            })
        })
    });

    let mut do_param: String = "DO ?".to_owned();
    let add_param: &str = ",?";
    for _i in 1..1000 {
        do_param.push_str(add_param);
    }
    let final_do1000 : &str = &do_param[..];
    group.bench_function("do 1000 param", |b| b.iter(|| {
        let _ = conn.exec_drop(final_do1000, (0..1000).collect::<Vec<i32>>(),);
        conn.last_insert_id();
    }));
    group.bench_function("sqlx do 1000 param", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut query = sqlx::query(&do_param);
                for i in 0..1000 {
                    query = query.bind(i);
                }
                let _ = query.execute(&pool).await.unwrap();
            })
        })
    });

    group.bench_function("mysql_async do 1000 param", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let params: Vec<i32> = (0..1000).collect();
                let _ = mysql_async::prelude::Queryable::exec_drop(&mut conn, final_do1000, params).await.unwrap();
                drop(conn);
            })
        })
    });

    group.bench_function("select 1", |b| b.iter(|| {
        let val: mysql::Row = conn.query_first("SELECT 1, null").unwrap().expect("REASON");
        for column in val.columns_ref() {
            column.name_str();
        }
        val.unwrap();
    }));

    group.bench_function("sqlx select 1", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let row: (i32, Option<String>) = sqlx::query_as("SELECT 1, null")
                    .fetch_one(&pool)
                    .await
                    .unwrap();
                row
            })
        })
    });

    group.bench_function("mysql_async select 1", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let result: (i32, Option<String>) = mysql_async::prelude::Queryable::query_first(&mut conn, "SELECT 1, null").await.unwrap().unwrap();
                drop(conn);
                result.0
            })
        })
    });

    #[derive(Debug, PartialEq, Eq)]
    struct ResRow {
        id: i32,
        val: Option<String>,
    }

    group.bench_function("select 1000 rows", |b| b.iter(|| {
        let selected_rest = conn.query_map("select * from 1000rows",
            |(id, val)| {
                ResRow {id, val}
            },
        );
        selected_rest
    }));
    #[derive(Debug, sqlx::FromRow)]
    struct ResRow2 {
        id: i32,
        val: Option<String>,
    }
    group.bench_function("sqlx select 1000 rows", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let rows: Vec<ResRow2> = sqlx::query_as("SELECT * FROM 1000rows")
                    .fetch_all(&pool)
                    .await
                    .unwrap();
                rows
            })
        })
    });

    group.bench_function("mysql_async select 1000 rows", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let rows: Vec<ResRow> = mysql_async::prelude::Queryable::query_map(
                    &mut conn,
                    "select * from 1000rows",
                    |(id, val)| {
                        ResRow {id, val}
                    },
                ).await.unwrap();
                drop(conn);
                rows
            })
        })
    });

    group.bench_function("select 1000 rows binary", |b| b.iter(|| {
        let selected_rest = conn.exec_map("select * from 1000rows", (),
                                           |(id, val)| {
                                               ResRow {id, val}
                                           },
        );
        selected_rest
    }));

    group.bench_function("mysql_async select 1000 rows binary", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let rows: Vec<ResRow> = mysql_async::prelude::Queryable::exec_map(
                    &mut conn,
                    "select * from 1000rows",
                    (),
                    |(id, val)| {
                        ResRow {id, val}
                    },
                ).await.unwrap();
                drop(conn);
                rows
            })
        })
    });

    #[derive(Debug)]
    struct Row100Columns {
        col1: i32,
        col2: i32,
        col3: i32,
        col4: i32,
        col5: i32,
        col6: i32,
        col7: i32,
        col8: i32,
        col9: i32,
        col10: i32,
        col11: i32,
        col12: i32,
        col13: i32,
        col14: i32,
        col15: i32,
        col16: i32,
        col17: i32,
        col18: i32,
        col19: i32,
        col20: i32,
        col21: i32,
        col22: i32,
        col23: i32,
        col24: i32,
        col25: i32,
        col26: i32,
        col27: i32,
        col28: i32,
        col29: i32,
        col30: i32,
        col31: i32,
        col32: i32,
        col33: i32,
        col34: i32,
        col35: i32,
        col36: i32,
        col37: i32,
        col38: i32,
        col39: i32,
        col40: i32,
        col41: i32,
        col42: i32,
        col43: i32,
        col44: i32,
        col45: i32,
        col46: i32,
        col47: i32,
        col48: i32,
        col49: i32,
        col50: i32,
        col51: i32,
        col52: i32,
        col53: i32,
        col54: i32,
        col55: i32,
        col56: i32,
        col57: i32,
        col58: i32,
        col59: i32,
        col60: i32,
        col61: i32,
        col62: i32,
        col63: i32,
        col64: i32,
        col65: i32,
        col66: i32,
        col67: i32,
        col68: i32,
        col69: i32,
        col70: i32,
        col71: i32,
        col72: i32,
        col73: i32,
        col74: i32,
        col75: i32,
        col76: i32,
        col77: i32,
        col78: i32,
        col79: i32,
        col80: i32,
        col81: i32,
        col82: i32,
        col83: i32,
        col84: i32,
        col85: i32,
        col86: i32,
        col87: i32,
        col88: i32,
        col89: i32,
        col90: i32,
        col91: i32,
        col92: i32,
        col93: i32,
        col94: i32,
        col95: i32,
        col96: i32,
        col97: i32,
        col98: i32,
        col99: i32,
        col100: i32,
    }

    group.bench_function("select 100 int columns", |b| b.iter(|| {
        let result = conn.query_iter("SELECT * FROM test100").unwrap();
        let mut rows = Vec::new();

        for row_result in result {
            if let Ok(row) = row_result {
                let cols = Row100Columns {
                    col1: row.get(0).unwrap_or(0),
                    col2: row.get(1).unwrap_or(0),
                    col3: row.get(2).unwrap_or(0),
                    col4: row.get(3).unwrap_or(0),
                    col5: row.get(4).unwrap_or(0),
                    col6: row.get(5).unwrap_or(0),
                    col7: row.get(6).unwrap_or(0),
                    col8: row.get(7).unwrap_or(0),
                    col9: row.get(8).unwrap_or(0),
                    col10: row.get(9).unwrap_or(0),
                    col11: row.get(10).unwrap_or(0),
                    col12: row.get(11).unwrap_or(0),
                    col13: row.get(12).unwrap_or(0),
                    col14: row.get(13).unwrap_or(0),
                    col15: row.get(14).unwrap_or(0),
                    col16: row.get(15).unwrap_or(0),
                    col17: row.get(16).unwrap_or(0),
                    col18: row.get(17).unwrap_or(0),
                    col19: row.get(18).unwrap_or(0),
                    col20: row.get(19).unwrap_or(0),
                    col21: row.get(20).unwrap_or(0),
                    col22: row.get(21).unwrap_or(0),
                    col23: row.get(22).unwrap_or(0),
                    col24: row.get(23).unwrap_or(0),
                    col25: row.get(24).unwrap_or(0),
                    col26: row.get(25).unwrap_or(0),
                    col27: row.get(26).unwrap_or(0),
                    col28: row.get(27).unwrap_or(0),
                    col29: row.get(28).unwrap_or(0),
                    col30: row.get(29).unwrap_or(0),
                    col31: row.get(30).unwrap_or(0),
                    col32: row.get(31).unwrap_or(0),
                    col33: row.get(32).unwrap_or(0),
                    col34: row.get(33).unwrap_or(0),
                    col35: row.get(34).unwrap_or(0),
                    col36: row.get(35).unwrap_or(0),
                    col37: row.get(36).unwrap_or(0),
                    col38: row.get(37).unwrap_or(0),
                    col39: row.get(38).unwrap_or(0),
                    col40: row.get(39).unwrap_or(0),
                    col41: row.get(40).unwrap_or(0),
                    col42: row.get(41).unwrap_or(0),
                    col43: row.get(42).unwrap_or(0),
                    col44: row.get(43).unwrap_or(0),
                    col45: row.get(44).unwrap_or(0),
                    col46: row.get(45).unwrap_or(0),
                    col47: row.get(46).unwrap_or(0),
                    col48: row.get(47).unwrap_or(0),
                    col49: row.get(48).unwrap_or(0),
                    col50: row.get(49).unwrap_or(0),
                    col51: row.get(50).unwrap_or(0),
                    col52: row.get(51).unwrap_or(0),
                    col53: row.get(52).unwrap_or(0),
                    col54: row.get(53).unwrap_or(0),
                    col55: row.get(54).unwrap_or(0),
                    col56: row.get(55).unwrap_or(0),
                    col57: row.get(56).unwrap_or(0),
                    col58: row.get(57).unwrap_or(0),
                    col59: row.get(58).unwrap_or(0),
                    col60: row.get(59).unwrap_or(0),
                    col61: row.get(60).unwrap_or(0),
                    col62: row.get(61).unwrap_or(0),
                    col63: row.get(62).unwrap_or(0),
                    col64: row.get(63).unwrap_or(0),
                    col65: row.get(64).unwrap_or(0),
                    col66: row.get(65).unwrap_or(0),
                    col67: row.get(66).unwrap_or(0),
                    col68: row.get(67).unwrap_or(0),
                    col69: row.get(68).unwrap_or(0),
                    col70: row.get(69).unwrap_or(0),
                    col71: row.get(70).unwrap_or(0),
                    col72: row.get(71).unwrap_or(0),
                    col73: row.get(72).unwrap_or(0),
                    col74: row.get(73).unwrap_or(0),
                    col75: row.get(74).unwrap_or(0),
                    col76: row.get(75).unwrap_or(0),
                    col77: row.get(76).unwrap_or(0),
                    col78: row.get(77).unwrap_or(0),
                    col79: row.get(78).unwrap_or(0),
                    col80: row.get(79).unwrap_or(0),
                    col81: row.get(80).unwrap_or(0),
                    col82: row.get(81).unwrap_or(0),
                    col83: row.get(82).unwrap_or(0),
                    col84: row.get(83).unwrap_or(0),
                    col85: row.get(84).unwrap_or(0),
                    col86: row.get(85).unwrap_or(0),
                    col87: row.get(86).unwrap_or(0),
                    col88: row.get(87).unwrap_or(0),
                    col89: row.get(88).unwrap_or(0),
                    col90: row.get(89).unwrap_or(0),
                    col91: row.get(90).unwrap_or(0),
                    col92: row.get(91).unwrap_or(0),
                    col93: row.get(92).unwrap_or(0),
                    col94: row.get(93).unwrap_or(0),
                    col95: row.get(94).unwrap_or(0),
                    col96: row.get(95).unwrap_or(0),
                    col97: row.get(96).unwrap_or(0),
                    col98: row.get(97).unwrap_or(0),
                    col99: row.get(98).unwrap_or(0),
                    col100: row.get(99).unwrap_or(0),
                };
                rows.push(cols);
            }
        }

        rows
    }));

    // Define structure for 100 column queries
    #[derive(Debug, sqlx::FromRow)]
    struct Row100Columns2 {
        i1: i32, i2: i32, i3: i32, i4: i32, i5: i32,
        i6: i32, i7: i32, i8: i32, i9: i32, i10: i32,
        i11: i32, i12: i32, i13: i32, i14: i32, i15: i32,
        i16: i32, i17: i32, i18: i32, i19: i32, i20: i32,
        i21: i32, i22: i32, i23: i32, i24: i32, i25: i32,
        i26: i32, i27: i32, i28: i32, i29: i32, i30: i32,
        i31: i32, i32: i32, i33: i32, i34: i32, i35: i32,
        i36: i32, i37: i32, i38: i32, i39: i32, i40: i32,
        i41: i32, i42: i32, i43: i32, i44: i32, i45: i32,
        i46: i32, i47: i32, i48: i32, i49: i32, i50: i32,
        i51: i32, i52: i32, i53: i32, i54: i32, i55: i32,
        i56: i32, i57: i32, i58: i32, i59: i32, i60: i32,
        i61: i32, i62: i32, i63: i32, i64: i32, i65: i32,
        i66: i32, i67: i32, i68: i32, i69: i32, i70: i32,
        i71: i32, i72: i32, i73: i32, i74: i32, i75: i32,
        i76: i32, i77: i32, i78: i32, i79: i32, i80: i32,
        i81: i32, i82: i32, i83: i32, i84: i32, i85: i32,
        i86: i32, i87: i32, i88: i32, i89: i32, i90: i32,
        i91: i32, i92: i32, i93: i32, i94: i32, i95: i32,
        i96: i32, i97: i32, i98: i32, i99: i32, i100: i32,
    }

    // SELECT 100 columns benchmark
    group.bench_function("sqlx select 100 int columns", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let rows: Vec<Row100Columns2> = sqlx::query_as("SELECT * FROM test100")
                    .fetch_all(&pool)
                    .await
                    .unwrap();
                rows
            })
        })
    });

    // MySQL_async SELECT 100 columns benchmark
    group.bench_function("mysql_async select 100 int columns", |b| {
        b.iter(|| {
            runtime.block_on(async {
                let mut conn = asyncPool.get_conn().await.unwrap();
                let rows: Vec<Row100Columns> = mysql_async::prelude::Queryable::query_map(
                    &mut conn,
                    "SELECT * FROM test100",
                    |row: mysql_async::Row| {
                        Row100Columns {
                            col1: row.get::<i32, _>("i1").unwrap_or(0),
                            col2: row.get::<i32, _>("i2").unwrap_or(0),
                            col3: row.get::<i32, _>("i3").unwrap_or(0),
                            col4: row.get::<i32, _>("i4").unwrap_or(0),
                            col5: row.get::<i32, _>("i5").unwrap_or(0),
                            col6: row.get::<i32, _>("i6").unwrap_or(0),
                            col7: row.get::<i32, _>("i7").unwrap_or(0),
                            col8: row.get::<i32, _>("i8").unwrap_or(0),
                            col9: row.get::<i32, _>("i9").unwrap_or(0),
                            col10: row.get::<i32, _>("i10").unwrap_or(0),
                            col11: row.get::<i32, _>("i11").unwrap_or(0),
                            col12: row.get::<i32, _>("i12").unwrap_or(0),
                            col13: row.get::<i32, _>("i13").unwrap_or(0),
                            col14: row.get::<i32, _>("i14").unwrap_or(0),
                            col15: row.get::<i32, _>("i15").unwrap_or(0),
                            col16: row.get::<i32, _>("i16").unwrap_or(0),
                            col17: row.get::<i32, _>("i17").unwrap_or(0),
                            col18: row.get::<i32, _>("i18").unwrap_or(0),
                            col19: row.get::<i32, _>("i19").unwrap_or(0),
                            col20: row.get::<i32, _>("i20").unwrap_or(0),
                            col21: row.get::<i32, _>("i21").unwrap_or(0),
                            col22: row.get::<i32, _>("i22").unwrap_or(0),
                            col23: row.get::<i32, _>("i23").unwrap_or(0),
                            col24: row.get::<i32, _>("i24").unwrap_or(0),
                            col25: row.get::<i32, _>("i25").unwrap_or(0),
                            col26: row.get::<i32, _>("i26").unwrap_or(0),
                            col27: row.get::<i32, _>("i27").unwrap_or(0),
                            col28: row.get::<i32, _>("i28").unwrap_or(0),
                            col29: row.get::<i32, _>("i29").unwrap_or(0),
                            col30: row.get::<i32, _>("i30").unwrap_or(0),
                            col31: row.get::<i32, _>("i31").unwrap_or(0),
                            col32: row.get::<i32, _>("i32").unwrap_or(0),
                            col33: row.get::<i32, _>("i33").unwrap_or(0),
                            col34: row.get::<i32, _>("i34").unwrap_or(0),
                            col35: row.get::<i32, _>("i35").unwrap_or(0),
                            col36: row.get::<i32, _>("i36").unwrap_or(0),
                            col37: row.get::<i32, _>("i37").unwrap_or(0),
                            col38: row.get::<i32, _>("i38").unwrap_or(0),
                            col39: row.get::<i32, _>("i39").unwrap_or(0),
                            col40: row.get::<i32, _>("i40").unwrap_or(0),
                            col41: row.get::<i32, _>("i41").unwrap_or(0),
                            col42: row.get::<i32, _>("i42").unwrap_or(0),
                            col43: row.get::<i32, _>("i43").unwrap_or(0),
                            col44: row.get::<i32, _>("i44").unwrap_or(0),
                            col45: row.get::<i32, _>("i45").unwrap_or(0),
                            col46: row.get::<i32, _>("i46").unwrap_or(0),
                            col47: row.get::<i32, _>("i47").unwrap_or(0),
                            col48: row.get::<i32, _>("i48").unwrap_or(0),
                            col49: row.get::<i32, _>("i49").unwrap_or(0),
                            col50: row.get::<i32, _>("i50").unwrap_or(0),
                            col51: row.get::<i32, _>("i51").unwrap_or(0),
                            col52: row.get::<i32, _>("i52").unwrap_or(0),
                            col53: row.get::<i32, _>("i53").unwrap_or(0),
                            col54: row.get::<i32, _>("i54").unwrap_or(0),
                            col55: row.get::<i32, _>("i55").unwrap_or(0),
                            col56: row.get::<i32, _>("i56").unwrap_or(0),
                            col57: row.get::<i32, _>("i57").unwrap_or(0),
                            col58: row.get::<i32, _>("i58").unwrap_or(0),
                            col59: row.get::<i32, _>("i59").unwrap_or(0),
                            col60: row.get::<i32, _>("i60").unwrap_or(0),
                            col61: row.get::<i32, _>("i61").unwrap_or(0),
                            col62: row.get::<i32, _>("i62").unwrap_or(0),
                            col63: row.get::<i32, _>("i63").unwrap_or(0),
                            col64: row.get::<i32, _>("i64").unwrap_or(0),
                            col65: row.get::<i32, _>("i65").unwrap_or(0),
                            col66: row.get::<i32, _>("i66").unwrap_or(0),
                            col67: row.get::<i32, _>("i67").unwrap_or(0),
                            col68: row.get::<i32, _>("i68").unwrap_or(0),
                            col69: row.get::<i32, _>("i69").unwrap_or(0),
                            col70: row.get::<i32, _>("i70").unwrap_or(0),
                            col71: row.get::<i32, _>("i71").unwrap_or(0),
                            col72: row.get::<i32, _>("i72").unwrap_or(0),
                            col73: row.get::<i32, _>("i73").unwrap_or(0),
                            col74: row.get::<i32, _>("i74").unwrap_or(0),
                            col75: row.get::<i32, _>("i75").unwrap_or(0),
                            col76: row.get::<i32, _>("i76").unwrap_or(0),
                            col77: row.get::<i32, _>("i77").unwrap_or(0),
                            col78: row.get::<i32, _>("i78").unwrap_or(0),
                            col79: row.get::<i32, _>("i79").unwrap_or(0),
                            col80: row.get::<i32, _>("i80").unwrap_or(0),
                            col81: row.get::<i32, _>("i81").unwrap_or(0),
                            col82: row.get::<i32, _>("i82").unwrap_or(0),
                            col83: row.get::<i32, _>("i83").unwrap_or(0),
                            col84: row.get::<i32, _>("i84").unwrap_or(0),
                            col85: row.get::<i32, _>("i85").unwrap_or(0),
                            col86: row.get::<i32, _>("i86").unwrap_or(0),
                            col87: row.get::<i32, _>("i87").unwrap_or(0),
                            col88: row.get::<i32, _>("i88").unwrap_or(0),
                            col89: row.get::<i32, _>("i89").unwrap_or(0),
                            col90: row.get::<i32, _>("i90").unwrap_or(0),
                            col91: row.get::<i32, _>("i91").unwrap_or(0),
                            col92: row.get::<i32, _>("i92").unwrap_or(0),
                            col93: row.get::<i32, _>("i93").unwrap_or(0),
                            col94: row.get::<i32, _>("i94").unwrap_or(0),
                            col95: row.get::<i32, _>("i95").unwrap_or(0),
                            col96: row.get::<i32, _>("i96").unwrap_or(0),
                            col97: row.get::<i32, _>("i97").unwrap_or(0),
                            col98: row.get::<i32, _>("i98").unwrap_or(0),
                            col99: row.get::<i32, _>("i99").unwrap_or(0),
                            col100: row.get::<i32, _>("i100").unwrap_or(0),
                        }
                    },
                ).await.unwrap();
                
                drop(conn);
                rows
            })
        })
    });
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);