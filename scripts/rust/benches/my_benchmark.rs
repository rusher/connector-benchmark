use criterion::{criterion_group, criterion_main, Criterion};
use mysql::*;
use mysql::prelude::*;


fn criterion_benchmark(c: &mut Criterion) {

    let DB_PORT = std::env::var("TEST_DB_PORT").unwrap_or("3306".to_string());
    let DB_DATABASE = std::env::var("TEST_DB_DATABASE").unwrap_or("bench".to_string());
    let DB_USER = std::env::var("TEST_DB_USER").unwrap_or("root".to_string());
    let DB_HOST = std::env::var("TEST_DB_HOST").unwrap_or("127.0.0.1".to_string());
    let DB_PASSWORD = std::env::var("TEST_DB_PASSWORD").unwrap_or("".to_string());

    let opts =
        OptsBuilder::new()
            .user(Some(DB_USER))
            .db_name(Some(DB_DATABASE))
            .pass(Some(DB_PASSWORD))
            .tcp_port(DB_PORT.parse::<u16>().unwrap())
            .ip_or_hostname(Some(DB_HOST))
            .prefer_socket(false);
    let mut conn = Conn::new(opts).expect("Connection");

    c.bench_function("do 1", |b| b.iter(|| {
        conn.query_drop("DO 1");
        conn.last_insert_id();
    }));

    let mut doparam: String = "DO ?".to_owned();
    let addParam: &str = ",?";
    for i in 1..1000 {
        doparam.push_str(addParam);
    }
    let finalDo1000 : &str = &doparam[..];
    c.bench_function("do 1000 param", |b| b.iter(|| {
        conn.exec_drop(finalDo1000, (0..1000).collect::<Vec<i32>>(),);
        conn.last_insert_id();
    }));


    c.bench_function("select 1", |b| b.iter(|| {
        let val: Row = conn.query_first("SELECT 1, null").unwrap().expect("REASON");;
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

    c.bench_function("select 1000 rows", |b| b.iter(|| {

        let selected_rest = conn.query_map("select * from 1000rows",
            |(id, val)| {
                ResRow {id, val}
            },
        );
        return selected_rest;
    }));

}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);