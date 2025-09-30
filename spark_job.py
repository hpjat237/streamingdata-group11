from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, sum, count, hour
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pymongo import MongoClient
import pytz

# Khởi tạo Spark session
spark = SparkSession.builder \
    .appName("NorthwindETL") \
    .config("spark.mongodb.output.uri", "mongodb://mongodb:27017/northwind") \
    .config("spark.jars", "/opt/bitnami/spark/jars/spark-streaming-kafka-0-10_2.12-3.4.0.jar,/opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.4.0.jar,/opt/bitnami/spark/jars/kafka-clients-3.4.0.jar") \
    .getOrCreate()

# Schema cho Kafka messages
schema = StructType([
    StructField("payload", StructType([
        StructField("before", StringType(), True),
        StructField("after", StringType(), True),
        StructField("op", StringType(), True),
        StructField("ts_ms", StringType(), True)
    ]))
])

# Đọc từ Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "cdc.public.orders,cdc.public.order_details") \
    .option("startingOffsets", "earliest") \
    .load()

# Parse JSON từ Kafka
df = df.selectExpr("CAST(value AS STRING) as json") \
       .select(from_json(col("json"), schema).alias("data")) \
       .select("data.payload.after", "data.payload.op")

# Schema cho orders và order_details
order_schema = StructType([
    StructField("order_id", IntegerType()),
    StructField("customer_id", StringType()),
    StructField("order_date", TimestampType())
])
order_detail_schema = StructType([
    StructField("order_id", IntegerType()),
    StructField("product_id", IntegerType()),
    StructField("unit_price", DoubleType()),
    StructField("quantity", IntegerType()),
    StructField("discount", DoubleType())
])

orders_df = df.where(col("op") == "c") \
             .select(from_json(col("after"), order_schema).alias("order")) \
             .select("order.*") \
             .filter(col("order_id").isNotNull())  # Loại bỏ null
order_details_df = df.where(col("op") == "c") \
                    .select(from_json(col("after"), order_detail_schema).alias("detail")) \
                    .select("detail.*") \
                    .filter(col("order_id").isNotNull())  # Loại bỏ null

# Join và tính toán
joined_df = orders_df.join(order_details_df, "order_id", "inner") \
                    .withColumn("revenue", col("unit_price") * col("quantity") * (1 - col("discount"))) \
                    .withColumn("hour", hour(col("order_date")))

# Thêm watermark dựa trên order_date
joined_df = joined_df.withWatermark("order_date", "30 minutes")

# Aggregation: Tổng doanh thu và số đơn hàng theo giờ
agg_df = joined_df.groupBy("hour", "customer_id") \
                 .agg(sum("revenue").alias("total_revenue"),
                      count("order_id").alias("order_count"))

# Lưu dữ liệu thô vào MongoDB
def save_to_mongo(df, epoch_id):
    client = MongoClient("mongodb://mongodb:27017/")
    db = client["northwind"]
    for row in df.collect():
        db["raw_orders"].insert_one({
            "order_id": row.order_id,
            "customer_id": row.customer_id,
            "order_date": row.order_date.isoformat() if row.order_date else None
        })
        db["raw_order_details"].insert_one({
            "order_id": row.order_id,
            "product_id": row.product_id,
            "unit_price": row.unit_price,
            "quantity": row.quantity,
            "discount": row.discount
        })
    client.close()

raw_query = joined_df.writeStream \
    .foreachBatch(save_to_mongo) \
    .option("checkpointLocation", "/app/spark-checkpoint/raw") \
    .start()

# Lưu aggregation vào MongoDB
def save_agg_to_mongo(df, epoch_id):
    client = MongoClient("mongodb://mongodb:27017/")
    db = client["northwind"]
    for row in df.collect():
        db["aggregated_revenue"].insert_one({
            "hour": row.hour,
            "customer_id": row.customer_id,
            "total_revenue": row.total_revenue,
            "order_count": row.order_count
        })
    client.close()

agg_query = agg_df.writeStream \
    .foreachBatch(save_agg_to_mongo) \
    .option("checkpointLocation", "/app/spark-checkpoint/agg") \
    .start()

spark.streams.awaitAnyTermination()