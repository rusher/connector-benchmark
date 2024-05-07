use criterion::{criterion_group, criterion_main, Criterion};
use mysql::*;
use mysql::prelude::*;
use atoi::*;

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
            .ip_or_hostname(Some(DB_HOST));
    let mut conn = Conn::new(opts).expect("Connection");

    c.bench_function("do 1", |b| b.iter(|| {
        conn.query_drop("DO 1");
    }));

    c.bench_function("select 1", |b| b.iter(|| {
        let val: Row = conn.query_first("SELECT 1, null").unwrap().expect("REASON");;
        for column in val.columns_ref() {
            column.name_str();
        }
        val.unwrap();
    }));
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);