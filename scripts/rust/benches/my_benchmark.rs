use criterion::{criterion_group, criterion_main, Criterion};
use mysql::*;
use mysql::prelude::*;
use core::time::Duration;


fn criterion_benchmark(c: &mut Criterion) {

    let mut group = c.benchmark_group("bench");
    group
        .warm_up_time(std::time::Duration::from_secs(5))
        .measurement_time(std::time::Duration::from_secs(20));

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

    group.bench_function("do 1", |b| b.iter(|| {
        let _ = conn.query_drop("DO 1");
        conn.last_insert_id();
    }));

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


    group.bench_function("select 1", |b| b.iter(|| {
        let val: Row = conn.query_first("SELECT 1, null").unwrap().expect("REASON");
        for column in val.columns_ref() {
            column.name_str();
        }
        val.unwrap();
    }));


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
        return selected_rest;
    }));


    group.bench_function("select 1000 rows binary", |b| b.iter(|| {
        let selected_rest = conn.exec_map("select * from 1000rows", (),
                                           |(id, val)| {
                                               ResRow {id, val}
                                           },
        );
        return selected_rest;
    }));

}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);