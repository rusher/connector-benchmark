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

func initDB(interpolateParams bool) *sql.DB {
	// Get database connection parameters from environment variables
	host := getEnv("TEST_DB_HOST", "localhost")
	port := getEnv("TEST_DB_PORT", "3306")
	user := getEnv("TEST_DB_USER", "root")
	password := getEnv("TEST_DB_PASSWORD", "")
	database := getEnv("TEST_DB_DATABASE", "bench")
	interpolateParamsStr := "0"
	if interpolateParams {
	    interpolateParamsStr = "1"
	}
	// Create DSN
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?interpolateParams=%s", user, password, host, port, database, interpolateParamsStr)

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
	db := initDB(false)
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
	db := initDB(false)
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
	db := initDB(false)
	b.StartTimer()

	for n := 0; n < b.N; n++ {
		rows, err := db.Query("SELECT * FROM 1000rows WHERE 1 = ?", 1)
		if err != nil {
			b.Fatalf("Failed to query 1000rows: %v", err)
		}

		var id int64
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

func BenchmarkSelect1000RowsBinary(b *testing.B) {
	db := initDB(false)
	b.StartTimer()

	stmt, err := db.Prepare("SELECT * FROM 1000rows WHERE 1 = ?")
	if err != nil {
		b.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()
	for n := 0; n < b.N; n++ {
		rows, err := stmt.Query(1)
		if err != nil {
			b.Fatalf("Failed to query 1000rows: %v", err)
		}

		var id int64
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
	db := initDB(false)
	b.StartTimer()

	for n := 0; n < b.N; n++ {
		rows, err := db.Query("SELECT * FROM test100")
		if err != nil {
			b.Fatalf("Failed to query test100: %v", err)
		}

		if rows.Next() {
			// Create a slice of pointers to int values
			var values [100]int64
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

func BenchmarkSelect100IntBinary(b *testing.B) {
	db := initDB(false)
	b.StartTimer()
	stmt, err := db.Prepare("SELECT * FROM test100")
	if err != nil {
		b.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for n := 0; n < b.N; n++ {
		rows, err := stmt.Query()
		if err != nil {
			b.Fatalf("Failed to query test100: %v", err)
		}

		if rows.Next() {
			// Create a slice of pointers to int values
			var values [100]int64
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
	db := initDB(true)

	// Build the SQL string with 1000 parameters
	sql := "DO ?"
	var i int64
    for i = 1; i < 1000; i++ {
        sql += ",?"
    }

    // Prepare args slice with 1000 integers
    args := make([]interface{}, 1000)
    for i = 0; i < 1000; i++ {
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
	db := initDB(false)

	// Build the SQL string with 1000 parameters
	sql := "DO ?"
    var i int64
    for i = 1; i < 1000; i++ {
        sql += ",?"
    }

    // Prepare args slice with 1000 integers
    args := make([]interface{}, 1000)
    for i = 0; i < 1000; i++ {
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

// BenchmarkSelect1Pool benchmarks SELECT 1 with a connection pool
// Uses 16 connections and 100 concurrent goroutines
func BenchmarkSelect1Pool(b *testing.B) {
	host := getEnv("TEST_DB_HOST", "localhost")
	port := getEnv("TEST_DB_PORT", "3306")
	user := getEnv("TEST_DB_USER", "root")
	password := getEnv("TEST_DB_PASSWORD", "")
	database := getEnv("TEST_DB_DATABASE", "bench")

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s", user, password, host, port, database)

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		b.Fatalf("Error connecting to database: %v", err)
	}
	defer db.Close()

	// Configure connection pool
	db.SetMaxOpenConns(16)
	db.SetMaxIdleConns(16)

	const numTasks = 100

	b.ResetTimer()
	for n := 0; n < b.N; n++ {
		// Create a channel to synchronize goroutines
		done := make(chan bool, numTasks)

		// Launch 100 concurrent queries
		for i := 0; i < numTasks; i++ {
			go func() {
				var result int
				err := db.QueryRow("SELECT 1").Scan(&result)
				if err != nil {
					b.Errorf("Failed to query select 1: %v", err)
				}
				done <- true
			}()
		}

		// Wait for all goroutines to complete
		for i := 0; i < numTasks; i++ {
			<-done
		}
	}
}
