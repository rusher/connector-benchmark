using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Text;
using System.Threading.Tasks;
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Columns;
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Diagnosers;
using BenchmarkDotNet.Environments;
using BenchmarkDotNet.Exporters;
using BenchmarkDotNet.Exporters.Json;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Running;
using BenchmarkDotNet.Validators;
using MySqlConnector;
using MySql.Data.MySqlClient;

namespace Benchmark;

class Program
{
	static void Main()
	{
		var customConfig = ManualConfig
			.Create(DefaultConfig.Instance)
			.AddValidator(JitOptimizationsValidator.FailOnError)
			.AddDiagnoser(MemoryDiagnoser.Default)
			.AddColumn(StatisticColumn.AllStatistics)
			.AddJob(Job.Default.WithRuntime(CoreRuntime.Core70))
			.AddExporter(JsonExporter.Brief);

		var summary = BenchmarkRunner.Run<MySqlClient>(customConfig);
		Console.WriteLine(summary);
	}
}

public class MySqlClient
{


	[Params("MySql.Data", "MySqlConnector")]
	public string Library { get; set; }

	[GlobalSetup]
	public void GlobalSetup()
	{
		var mySqlData = new MySql.Data.MySqlClient.MySqlConnection(s_connectionString);
		mySqlData.Open();
		m_connections.Add("MySql.Data", mySqlData);

		var mySqlConnector = new MySqlConnector.MySqlConnection(s_connectionString);
		mySqlConnector.Open();
		m_connections.Add("MySqlConnector", mySqlConnector);

		Connection = m_connections[Library];
	}

	[GlobalCleanup]
	public void GlobalCleanup()
	{
		foreach (var connection in m_connections.Values)
			connection.Dispose();
		m_connections.Clear();
		MySqlConnector.MySqlConnection.ClearAllPools();
		MySql.Data.MySqlClient.MySqlConnection.ClearAllPools();
	}

	private static String do1000Param;
	static MySqlClient()
	{
		StringBuilder sb = new StringBuilder("do ?");
		for (int i = 1; i < 1000; i++) {
			sb.Append(",?");
		}
		do1000Param = sb.ToString();
	}

	[Benchmark]
	public async Task<int> ExecuteDo1()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "do 1";
		return await cmd.ExecuteNonQueryAsync();
	}

	[Benchmark]
	public async Task<int> Select1()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "Select 1";
		return (int) await cmd.ExecuteScalarAsync();
	}



	[Benchmark]
	public async Task<int[]> Select100ColText()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "select * FROM test100";
        using var reader = await cmd.ExecuteReaderAsync();
        int[] val = new int[100];
        await reader.ReadAsync();
        for (int i = 0; i < 100; i++) {
            val[i] = reader.GetInt32(i);
        }
        return val;
	}

	[Benchmark]
	public async Task<int[]> Select100ColBinary()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "select * FROM test100";
		cmd.Prepare();
        using var reader = await cmd.ExecuteReaderAsync();
        int[] val = new int[100];
        await reader.ReadAsync();
        for (int i = 0; i < 100; i++) {
            val[i] = reader.GetInt32(i);
        }
        return val;
	}


	[Benchmark]
	public async Task<int> Select1000rowsText()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "select * from 1000rows";
        using var reader = await cmd.ExecuteReaderAsync();
        int val = 0;
        while (await reader.ReadAsync())
        {
            val = reader.GetInt32(0);
            reader.GetString(1);
        }

        return val;
	}

	[Benchmark]
	public async Task<int> Select1000rowsBinary()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = "select * from 1000rows";
		cmd.Prepare();
        using var reader = await cmd.ExecuteReaderAsync();
        int val = 0;
        while (await reader.ReadAsync())
        {
            val = reader.GetInt32(0);
            reader.GetString(1);
        }

        return val;
	}

	[Benchmark]
	public async Task<int> ExecuteDo1000PrepareParamMySql()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = do1000Param;
		cmd.Prepare();
        for (int i = 1; i <= 1000; i++) {
          var param = new MySql.Data.MySqlClient.MySqlParameter();
          param.Value = i;
          cmd.Parameters.Add(param);
        }
		return await cmd.ExecuteNonQueryAsync();
	}

	[Benchmark]
	public async Task<int> ExecuteDo1000ParamMySql()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = do1000Param;
        for (int i = 1; i <= 1000; i++) {
          var param = new MySql.Data.MySqlClient.MySqlParameter();
          param.Value = i;
          cmd.Parameters.Add(param);
        }
		return await cmd.ExecuteNonQueryAsync();
	}

	[Benchmark]
	public async Task<int> ExecuteDo1000ParamComm()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = do1000Param;
        for (int i = 1; i <= 1000; i++) {
          cmd.Parameters.Add(new MySqlConnector.MySqlParameter() { Value = 100 });
        }
		return await cmd.ExecuteNonQueryAsync();
	}

	[Benchmark]
	public async Task<int> ExecuteDo1000PrepareParamCommPrepare()
	{
		using var cmd = Connection.CreateCommand();
		cmd.CommandText = do1000Param;
		cmd.Prepare();
        for (int i = 1; i <= 1000; i++) {
          cmd.Parameters.Add(new MySqlConnector.MySqlParameter() { Value = 100 });
        }
		return await cmd.ExecuteNonQueryAsync();
	}

	private DbConnection Connection { get; set; }

	// TODO: move to config file
	static string s_connectionString = "server=127.0.0.1;user id=root;port=3306;ssl mode=none;Use Affected Rows=true;Connection Reset=false;Default Command Timeout=0;AutoEnlist=false;database=bench;";

	Dictionary<string, DbConnection> m_connections = new Dictionary<string, DbConnection>();
}
