use mysql::*;
use mysql::prelude::*;
use std::env;

#[derive(Debug, PartialEq, Eq)]
struct Payment {
    customer_id: i32,
    amount: i32,
    account_name: Option<String>,
}


fn main() -> std::result::Result<(), Box<dyn std::error::Error>> {
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
//             .tcp_port(Some(DB_PORT))
            .ip_or_hostname(Some(DB_HOST));
    let mut conn = Conn::new(opts)?;
//
//     // Let's create a table for payments.
//     conn.query_drop(
//         r"CREATE TEMPORARY TABLE payment (
//             customer_id int not null,
//             amount int not null,
//             account_name text
//         )")?;
//
//     let payments = vec![
//         Payment { customer_id: 1, amount: 2, account_name: None },
//         Payment { customer_id: 3, amount: 4, account_name: Some("foo".into()) },
//         Payment { customer_id: 5, amount: 6, account_name: None },
//         Payment { customer_id: 7, amount: 8, account_name: None },
//         Payment { customer_id: 9, amount: 10, account_name: Some("bar".into()) },
//     ];
//
//     // Now let's insert payments to the database
//     conn.exec_batch(
//         r"INSERT INTO payment (customer_id, amount, account_name)
//           VALUES (:customer_id, :amount, :account_name)",
//         payments.iter().map(|p| params! {
//             "customer_id" => p.customer_id,
//             "amount" => p.amount,
//             "account_name" => &p.account_name,
//         })
//     )?;
//
//     // Let's select payments from database. Type inference should do the trick here.
//     let selected_payments = conn
//         .query_map(
//             "SELECT customer_id, amount, account_name from payment",
//             |(customer_id, amount, account_name)| {
//                 Payment { customer_id, amount, account_name }
//             },
//         )?;
//
//     // Let's make sure, that `payments` equals to `selected_payments`.
//     // Mysql gives no guaranties on order of returned rows
//     // without `ORDER BY`, so assume we are lucky.
//     assert_eq!(payments, selected_payments);
//     println!("Yay!");

    Ok(())
}