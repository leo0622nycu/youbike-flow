import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, expr
from pyspark.sql.types import (
    StructType, StructField, StringType,
    DoubleType, IntegerType, TimestampType
)

KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC           = "youbike_raw"
PG_URL          = "jdbc:postgresql://postgres:5432/youbike"
PG_PROPS        = {
    "user":     os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "driver":   "org.postgresql.Driver"     # ← 一定要加
}

schema = StructType([
    StructField("sno", StringType()),
    StructField("sna", StringType()),
    StructField("tot", IntegerType()),
    StructField("sbi", IntegerType()),
    StructField("bemp", IntegerType()),
    StructField("lat", DoubleType()),
    StructField("lng", DoubleType()),
    StructField("mday", TimestampType())
])

spark = SparkSession.builder.appName("YouBikeStream").getOrCreate()

raw = (
    spark.readStream.format("kafka")
         .option("kafka.bootstrap.servers", "kafka:9092")
         .option("subscribe", TOPIC)
         .option("startingOffsets", "latest")
         .load()
)

json_df = (
    raw.selectExpr("CAST(value AS STRING) AS json")
        .select(from_json(col("json"), schema).alias("data"))
        .select("data.*")
        .withColumn("ingested_at", expr("current_timestamp()"))
)

def write_to_pg(df, batch_id):
    df.write \
      .format("jdbc") \
      .option("url", PG_URL) \
      .option("dbtable", "inventory_stage") \
      .option("user", PG_PROPS["user"]) \
      .option("password", PG_PROPS["password"]) \
      .option("driver", PG_PROPS["driver"]) \
      .mode("append") \
      .save()

query = (
    json_df.writeStream
          .foreachBatch(write_to_pg)
          .option("checkpointLocation", "/spark_ckpt/youbike_stream")
          .trigger(processingTime="10 seconds")
          .start()
)

query.awaitTermination()
print("DEBUG:", os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))