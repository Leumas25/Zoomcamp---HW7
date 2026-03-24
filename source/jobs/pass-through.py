from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def create_processed_events_sink_postgres(t_env):
    table_name = 'processed_events'
    sink_ddl = f"""
    CREATE TABLE {table_name} (
        PULocationID int,
        DOLocationID int,
        trip_distance float,
        total_amount float,
        pickup_datetime timestamp
        ) with (
        'connector' = 'jdbc',
        'url' = 'jdbc:postgresql://postgres:5432/postgres',
        'table-name' = '{table_name}',
        'username' = 'postgres',
        'password' = 'postgres',
        'driver' = 'org.postgresql.Driver'
    );
    """ 
    t_env.execute_sql(sink_ddl)
    return table_name

def create_events_source_kafka(t_env):
    table_name = "events"
    source_ddl = f"""
    CREATE TABLE {table_name} (
        PULocationID int,
        DOLocationID int,
        trip_distance float,
        total_amount float,
        lpep_pickup_datetime bigint
        ) WITH (
            'connector' = 'kafka',
            'properties.bootstrap.servers' = 'redpanda:29092',
            'topic' = 'green_trips',
            'scan.startup.mode' = 'latest-offset',
            'properties.auto.offset.reset' = 'latest',
            'format' = 'json'
        );
    """
    t_env.execute_sql(source_ddl)
    return table_name

def log_processing():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10 * 1000)

    # Set up the table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    try:

        source_table = create_events_source_kafka(t_env)
        postgres_sink = create_processed_events_sink_postgres(t_env)

        t_env.execute_sql(f"""
        INSERT INTO {postgres_sink}
        SELECT 
            PULocationID,
            DOLocationID,
            trip_distance,
            total_amount,
            TO_TIMESTAMP_LTZ(lpep_pickup_datetime, 3) as pickup_datetime
        FROM {source_table} 
        """).wait()

    except Exception as e:
        print("Writing to sink failed", str(e))

if __name__ == "__main__":
    log_processing()