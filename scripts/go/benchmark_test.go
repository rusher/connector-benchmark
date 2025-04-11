package main

import (
	"database/sql"
	"fmt"
	"os"
	"testing"

	_ "github.com/go-sql-driver/mysql"
)

func main() {
	res := testing.Benchmark(BenchmarkSelect1)
	fmt.Printf("%s\n%#[1]v\n", res)
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func initDB() *sql.DB {
	// Get database connection parameters from environment variables
	host := getEnv("TEST_DB_HOST", "localhost")
	port := getEnv("TEST_DB_PORT", "3306")
	user := getEnv("TEST_DB_USER", "root")
	password := getEnv("TEST_DB_PASSWORD", "")
	database := getEnv("TEST_DB_DATABASE", "bench")

	// Create DSN
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s", user, password, host, port, database)

	// Connect to database
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		fmt.Printf("Error connecting to database: %v\n", err)
		os.Exit(1)
	}

	// Set connection pool parameters
	db.SetMaxOpenConns(1)
	return db
}

// benchmarkSelect1 benchmarks a simple "SELECT 1" query
func BenchmarkSelect1(b *testing.B) {
	db := initDB()
	b.StartTimer()

	var result int
	for n := 0; n < b.N; n++ {
		err := db.QueryRow("SELECT 1").Scan(&result)
		if err != nil {
			b.Fatalf("Failed to query select 1: %v", err)
		}
	}
	b.StopTimer()
	db.Close()
}

func BenchmarkDo1(b *testing.B) {
	db := initDB()
	b.StartTimer()

	for n := 0; n < b.N; n++ {
		_, err := db.Exec("DO 1")
		if err != nil {
			b.Fatalf("Failed to query do 1: %v", err)
		}

	}
	b.StopTimer()
	db.Close()
}

func BenchmarkSelect1000Rows(b *testing.B) {
	db := initDB()
	b.StartTimer()

	for n := 0; n < b.N; n++ {
		rows, err := db.Query("SELECT * FROM 1000rows")
		if err != nil {
			b.Fatalf("Failed to query 1000rows: %v", err)
		}

		var id int
		var val string

		for rows.Next() {
			err = rows.Scan(&id, &val)
			if err != nil {
				rows.Close()
				b.Fatalf("Failed to scan row: %v", err)
			}
		}
		rows.Close()
	}
	b.StopTimer()
	db.Close()
}

func BenchmarkSelect100Int(b *testing.B) {
	db := initDB()
	b.StartTimer()

	for n := 0; n < b.N; n++ {
		rows, err := db.Query("SELECT * FROM test100")
		if err != nil {
			b.Fatalf("Failed to query test100: %v", err)
		}

		if rows.Next() {
			// Create a slice of pointers to int values
			var values [100]int
			// Create scan destinations
			scanArgs := make([]interface{}, 100)
			for i := range values {
				scanArgs[i] = &values[i]
			}

			// Scan the row into our values
			err = rows.Scan(scanArgs...)
			if err != nil {
				rows.Close()
				b.Fatalf("Failed to scan row: %v", err)
			}
		}
		rows.Close()
	}

	b.StopTimer()
	db.Close()
}

func BenchmarkDo1000Params(b *testing.B) {
	db := initDB()

	// Build the SQL string with 1000 parameters
	sql := "DO ?"
	for i := 1; i < 1000; i++ {
		sql += ",?"
	}

	// Prepare args slice with 1000 integers
	args := make([]interface{}, 1000)
	for i := 0; i < 1000; i++ {
		args[i] = i + 1
	}

	b.StartTimer()
	for n := 0; n < b.N; n++ {
		_, err := db.Exec(sql, args...)
		if err != nil {
			b.Fatalf("Failed to execute statement with 1000 params: %v", err)
		}
	}

	b.StopTimer()
	db.Close()
}

func BenchmarkDo1000ParamsBinary(b *testing.B) {
	db := initDB()

	// Build the SQL string with 1000 parameters
	sql := "DO ?"
	for i := 1; i < 1000; i++ {
		sql += ",?"
	}

	// Prepare args slice with 1000 integers
	args := make([]interface{}, 1000)
	for i := 0; i < 1000; i++ {
		args[i] = i + 1
	}

	b.StartTimer()
	// Prepare the statement once before the benchmark loop
	stmt, err := db.Prepare(sql)
	if err != nil {
		b.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for n := 0; n < b.N; n++ {
		_, err := stmt.Exec(args...)
		if err != nil {
			b.Fatalf("Failed to execute prepared statement with 1000 params: %v", err)
		}
	}

	b.StopTimer()
	db.Close()
}
