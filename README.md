# Hệ thống ETL Thời gian thực với Northwind Database

![Banner](https://via.placeholder.com/800x200.png?text=ETL+Thời+gian+thực+với+Northwind+Database)  
*Hình ảnh minh họa hệ thống (thay thế bằng hình ảnh thực tế nếu có)*

## 🚀 Mục tiêu dự án

Xây dựng hệ thống **ETL (Extract, Transform, Load) thời gian thực** sử dụng **Northwind sample database** (MySQL) để:
- **Extract**: Bắt các thay đổi (INSERT, UPDATE, DELETE) từ các bảng `customers`, `orders`, `order_details` bằng **Debezium CDC**.
- **Transform**: Xử lý, làm sạch, và tính toán aggregation (tổng doanh thu theo ngày, số đơn hàng theo khách hàng) bằng **Spark Structured Streaming**.
- **Load**: Lưu dữ liệu đã xử lý vào **HDFS** dưới dạng Parquet.

**Yêu cầu chức năng**:
- Theo dõi thay đổi trên bảng `customers`, `orders`, `order_details`.
- Làm sạch dữ liệu (loại bỏ null, xử lý duplicate).
- Tính toán:
  - Tổng doanh thu (`order_details.quantity * order_details.unit_price`) theo ngày.
  - Số đơn hàng theo khách hàng.
- Lưu kết quả vào HDFS với các partition theo ngày.
- Tùy chọn: Dashboard Grafana hiển thị tổng doanh thu theo thời gian thực.

**Thời gian**: 4 tuần (30/09/2025 - 28/10/2025)  
**Nhóm**: 5 thành viên

---

## 📑 Mục lục

- [📋 Mô tả hệ thống](#-mô-tả-hệ-thống)
- [🔹 Luồng dữ liệu](#-luồng-dữ liệu)
- [📋 Cấu trúc dự án](#-cấu-trúc-dự-án)
- [🔹 Yêu cầu](#-yêu-cầu)
- [📥 Cài đặt và chạy demo](#-cài-đặt-và-chạy-demo)
  - [Cài đặt môi trường](#cài-đặt-môi-trường)
  - [Khởi tạo dữ liệu Northwind](#khởi-tạo-dữ-liệu-northwind)
  - [Đăng ký Debezium Connector](#đăng-ký-debezium-connector)
  - [Chạy Spark Streaming](#chạy-spark-streaming)
  - [Kiểm tra kết quả](#kiểm-tra-kết-quả)
  - [Clean hệ thống](#clean-hệ-thống)
- [🔹 Phân công công việc](#-phân-công-công-việc)
- [🔹 Lịch trình dự án](#-lịch-trình-dự-án)
- [🔹 Lưu ý](#-lưu-ý)
- [🔹 Khắc phục sự cố](#-khắc-phục-sự-cố)
- [🔹 Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [📧 Liên hệ](#-liên-hệ)

---

## 📋 Mô tả hệ thống

Hệ thống sử dụng **Northwind database** (MySQL) làm nguồn dữ liệu, với các thành phần chính:

- **MySQL**: Lưu trữ Northwind database (`customers`, `orders`, `order_details`).
- **Debezium**: Theo dõi thay đổi (CDC) từ MySQL binlog, gửi đến Kafka topics (`cdc.northwind.customers`, `cdc.northwind.orders`, `cdc.northwind.order_details`).
- **Kafka**: Hàng đợi tin nhắn để truyền dữ liệu thời gian thực.
- **Spark Structured Streaming**: Xử lý, làm sạch, và tính toán aggregation từ Kafka.
- **HDFS**: Kho dữ liệu lưu trữ kết quả dưới dạng Parquet, partition theo ngày.

![System Architecture](https://via.placeholder.com/600x300.png?text=Kiến+trúc+hệ+thống)  
*Hình ảnh kiến trúc hệ thống (thay thế bằng hình ảnh thực tế nếu có)*

---

## 🔹 Luồng dữ liệu

1. **Extract**: Debezium bắt thay đổi (INSERT, UPDATE, DELETE) từ MySQL, gửi JSON messages đến Kafka topics.
2. **Transform**: Spark Structured Streaming đọc từ Kafka, làm sạch dữ liệu (loại bỏ null, duplicate), join `orders` và `order_details`, tính tổng doanh thu và số đơn hàng.
3. **Load**: Lưu dữ liệu thô và aggregation vào HDFS (`/northwind/raw/` và `/northwind/aggregated/`), partition theo ngày (`year=2025/month=09/day=30`).

---

## 📋 Cấu trúc dự án

```
etl-realtime-northwind/
├── docker-compose.yml      # Cấu hình Docker
├── debezium_config.json    # Cấu hình Debezium connector
├── init_northwind.sql      # Script khởi tạo Northwind database
├── spark_job.py            # Spark Structured Streaming job
├── assets/                 # Hình ảnh minh họa
└── README.md               # Tài liệu hướng dẫn
```

---

## 🔹 Yêu cầu

- **Git**: Clone dự án.
- **Docker & Docker Compose**: Chạy MySQL, Kafka, Spark, HDFS.
- **MongoDB Shell (`mongosh`)** hoặc **MongoDB Compass**: Kiểm tra dữ liệu (tùy chọn cho debug).
- **HDFS**: Cluster 3 nodes hoặc local setup.
- **Python**: 3.9+ (pyspark, kafka-python).

---

## 📥 Cài đặt và chạy demo

### Cài đặt môi trường

1. **Clone dự án**:

   ```bash
   git clone https://github.com/your_username/etl-realtime-northwind.git
   cd etl-realtime-northwind
   ```

   ![Clone Project](https://via.placeholder.com/600x200.png?text=Clone+Project)  
   *Hình ảnh minh họa clone dự án*

2. **Tạo file `docker-compose.yml`**:

   ```yaml
   version: '3.8'
   services:
     mysql:
       image: mysql:8.0
       environment:
         MYSQL_ROOT_PASSWORD: root
         MYSQL_DATABASE: northwind
       ports:
         - "3306:3306"
       volumes:
         - ./init_northwind.sql:/docker-entrypoint-initdb.d/init_northwind.sql
       networks:
         - etl-network
     zookeeper:
       image: confluentinc/cp-zookeeper:7.4.0
       environment:
         ZOOKEEPER_CLIENT_PORT: 2181
         ZOOKEEPER_TICK_TIME: 2000
       networks:
         - etl-network
     kafka:
       image: confluentinc/cp-kafka:7.4.0
       depends_on:
         - zookeeper
       environment:
         KAFKA_BROKER_ID: 1
         KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
         KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
         KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
         KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
         KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
       ports:
         - "9093:9093"
       networks:
         - etl-network
     connect:
       image: debezium/connect:2.3
       depends_on:
         - kafka
         - mysql
       environment:
         BOOTSTRAP_SERVERS: kafka:9092
         GROUP_ID: connect-group
         CONFIG_STORAGE_TOPIC: connect_configs
         OFFSET_STORAGE_TOPIC: connect_offsets
         STATUS_STORAGE_TOPIC: connect_status
       ports:
         - "8083:8083"
       networks:
         - etl-network
     spark-master:
       image: bitnami/spark:3.4.0
       environment:
         SPARK_MODE: master
       ports:
         - "7077:7077"
         - "8080:8080"
       networks:
         - etl-network
     spark-worker:
       image: bitnami/spark:3.4.0
       depends_on:
         - spark-master
       environment:
         SPARK_MODE: worker
         SPARK_MASTER_URL: spark://spark-master:7077
       networks:
         - etl-network
     hdfs-namenode:
       image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
       environment:
         CLUSTER_NAME: test
       ports:
         - "9870:9870"
       volumes:
         - hdfs-namenode-data:/hadoop/dfs/name
       networks:
         - etl-network
     hdfs-datanode:
       image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
       depends_on:
         - hdfs-namenode
       environment:
         SERVICE_PRECONDITION: hdfs-namenode:9870
       volumes:
         - hdfs-datanode-data:/hadoop/dfs/data
       networks:
         - etl-network
   volumes:
     hdfs-namenode-data:
     hdfs-datanode-data:
   networks:
     etl-network:
       driver: bridge
   ```

3. **Khởi động các container**:

   ```bash
   docker-compose up -d
   ```

   > **Lưu ý**: Kiểm tra container chạy:
   > ```bash
   > docker ps
   > ```

4. **Cài đặt thư viện Python trong container `spark-master`**:

   ```bash
   docker exec -it spark-master bash
   pip install pyspark kafka-python
   exit
   ```

### Khởi tạo dữ liệu Northwind

5. **Tạo file `init_northwind.sql`**:

   ```sql
   CREATE DATABASE IF NOT EXISTS northwind;
   USE northwind;

   CREATE TABLE customers (
       customer_id VARCHAR(5) PRIMARY KEY,
       company_name VARCHAR(40),
       city VARCHAR(15)
   );

   CREATE TABLE orders (
       order_id INT PRIMARY KEY,
       customer_id VARCHAR(5),
       order_date DATE,
       FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
   );

   CREATE TABLE order_details (
       order_id INT,
       product_id INT,
       unit_price DECIMAL(10,2),
       quantity INT,
       PRIMARY KEY (order_id, product_id),
       FOREIGN KEY (order_id) REFERENCES orders(order_id)
   );

   INSERT INTO customers (customer_id, company_name, city) VALUES
   ('ALFKI', 'Alfreds Futterkiste', 'Berlin'),
   ('ANATR', 'Ana Trujillo Emparedados', 'México D.F.'),
   ('ANTON', 'Antonio Moreno Taquería', 'México D.F.');

   INSERT INTO orders (order_id, customer_id, order_date) VALUES
   (11077, 'ALFKI', '2025-09-30'),
   (11078, 'ANATR', '2025-09-30'),
   (11079, 'ANTON', '2025-09-30');

   INSERT INTO order_details (order_id, product_id, unit_price, quantity) VALUES
   (11077, 1, 18.00, 10),
   (11078, 2, 19.00, 5),
   (11079, 3, 10.00, 20);
   ```

6. **Áp dụng schema Northwind**:

   - File `init_northwind.sql` sẽ tự động chạy khi container `mysql` khởi động (do volume mapping trong `docker-compose.yml`).

7. **Kích hoạt binlog cho MySQL**:

   ```bash
   docker exec -it mysql bash
   echo -e "[mysqld]\nlog-bin=mysql-bin\nbinlog-format=ROW\nserver-id=1" >> /etc/mysql/my.cnf
   exit
   docker-compose restart mysql
   ```

### Đăng ký Debezium Connector

8. **Tạo file `debezium_config.json`**:

   ```json
   {
     "name": "mysql-connector",
     "config": {
       "connector.class": "io.debezium.connector.mysql.MySqlConnector",
       "tasks.max": "1",
       "database.hostname": "mysql",
       "database.port": "3306",
       "database.user": "root",
       "database.password": "root",
       "database.server.id": "1",
       "database.server.name": "cdc",
       "database.include.list": "northwind",
       "table.include.list": "northwind.customers,northwind.orders,northwind.order_details",
       "database.history.kafka.bootstrap.servers": "kafka:9092",
       "database.history.kafka.topic": "cdc.northwind.schema-changes",
       "key.converter": "org.apache.kafka.connect.json.JsonConverter",
       "value.converter": "org.apache.kafka.connect.json.JsonConverter",
       "key.converter.schemas.enable": false,
       "value.converter.schemas.enable": false
     }
   }
   ```

9. **Đăng ký connector**:

   ```bash
   curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors
   ```

10. **Kiểm tra trạng thái connector**:

    ```bash
    curl http://localhost:8083/connectors/mysql-connector/status
    ```

    > **Kỳ vọng**: Trạng thái `RUNNING`. Nếu lỗi, kiểm tra log:
    > ```bash
    > docker logs connect
    > ```

### Chạy Spark Streaming

11. **Tạo file `spark_job.py`**:

    ```python
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_date, sum, count
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

    # Khởi tạo Spark session
    spark = SparkSession.builder \
        .appName("NorthwindETL") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:9870") \
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
        .option("subscribe", "cdc.northwind.orders,cdc.northwind.order_details") \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse JSON từ Kafka
    df = df.selectExpr("CAST(value AS STRING) as json") \
           .select(from_json(col("json"), schema).alias("data")) \
           .select("data.payload.after", "data.payload.op")

    # Parse chuỗi JSON trong 'after'
    order_schema = StructType([
        StructField("order_id", IntegerType()),
        StructField("customer_id", StringType()),
        StructField("order_date", StringType())
    ])
    order_detail_schema = StructType([
        StructField("order_id", IntegerType()),
        StructField("product_id", IntegerType()),
        StructField("unit_price", DoubleType()),
        StructField("quantity", IntegerType())
    ])

    orders_df = df.where(col("op") == "c") \
                 .select(from_json(col("after"), order_schema).alias("order")) \
                 .select("order.*")
    order_details_df = df.where(col("op") == "c") \
                        .select(from_json(col("after"), order_detail_schema).alias("detail")) \
                        .select("detail.*")

    # Join và tính toán
    joined_df = orders_df.join(order_details_df, "order_id") \
                        .withColumn("revenue", col("unit_price") * col("quantity")) \
                        .withColumn("date", to_date(col("order_date")))

    # Aggregation: Tổng doanh thu theo ngày
    agg_df = joined_df.groupBy("date") \
                     .agg(sum("revenue").alias("total_revenue"),
                          count("order_id").alias("order_count"))

    # Lưu dữ liệu thô vào HDFS
    raw_query = order_details_df.writeStream \
        .format("parquet") \
        .option("path", "hdfs://hdfs-namenode:9870/northwind/raw/order_details") \
        .option("checkpointLocation", "/tmp/spark-checkpoint/raw") \
        .partitionBy("order_id") \
        .start()

    # Lưu aggregation vào HDFS
    agg_query = agg_df.writeStream \
        .format("parquet") \
        .option("path", "hdfs://hdfs-namenode:9870/northwind/aggregated/revenue") \
        .option("checkpointLocation", "/tmp/spark-checkpoint/agg") \
        .partitionBy("date") \
        .start()

    spark.streams.awaitAnyTermination()
    ```

12. **Chạy Spark job**:

    ```bash
    docker exec -it spark-master spark-submit /app/spark_job.py
    ```

    > **Kỳ vọng**: Dữ liệu từ Kafka được đọc, xử lý, và lưu vào HDFS.

### Kiểm tra kết quả

13. **Kiểm tra Kafka topics**:

    ```bash
    docker exec -it connect /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic cdc.northwind.order_details --from-beginning
    ```

    **Kỳ vọng**: Thấy JSON messages từ Debezium.

14. **Kiểm tra dữ liệu trong HDFS**:

    ```bash
    docker exec -it hdfs-namenode hdfs dfs -ls /northwind/raw/order_details
    docker exec -it hdfs-namenode hdfs dfs -ls /northwind/aggregated/revenue
    ```

    **Kỳ vọng**:
    - `/northwind/raw/order_details`: Dữ liệu thô từ `order_details`.
    - `/northwind/aggregated/revenue`: Tổng doanh thu theo ngày.

15. **Query HDFS bằng Spark SQL**:

    ```bash
    docker exec -it spark-master spark-shell
    ```

    ```scala
    val df = spark.read.parquet("hdfs://hdfs-namenode:9870/northwind/aggregated/revenue")
    df.show()
    ```

    **Kỳ vọng**:
    ```plaintext
    +----------+-------------+------------+
    |date      |total_revenue|order_count|
    +----------+-------------+------------+
    |2025-09-30|180.00       |1           |
    +----------+-------------+------------+
    ```

### Clean hệ thống

16. **Dừng và xóa container, volume, network**:

    ```bash
    docker-compose down -v
    ```

    > **Lưu ý**: Lệnh này xóa tất cả container, volume (MySQL, HDFS), và Kafka topics. Sao lưu dữ liệu nếu cần.

    ![Clean System](https://via.placeholder.com/600x200.png?text=Clean+hệ+thống)  
    *Hình ảnh minh họa clean hệ thống*

---

## 🔹 Phân công công việc

| Thành viên | Vai trò | Trách nhiệm chính | Thời gian ước tính |
|------------|---------|-------------------|-------------------|
| **Thành viên 1 (Leader)** | Project Manager & DevOps | - Quản lý tiến độ, họp nhóm<br>- Thiết lập Docker Compose<br>- CI/CD với GitHub Actions | 40% |
| **Thành viên 2** | Database & CDC Specialist | - Tạo schema Northwind<br>- Cấu hình Debezium connector<br>- Test CDC | 30% |
| **Thành viên 3** | Streaming Processing Expert | - Viết Spark job (parse, transform, aggregation)<br>- Optimize streaming | 30% |
| **Thành viên 4** | Data Storage & Analytics | - Cấu hình HDFS<br>- Viết Spark SQL queries<br>- Setup Grafana (tùy chọn) | 30% |
| **Thành viên 5** | Tester & Documentation | - Test end-to-end<br>- Viết test cases<br>- Soạn báo cáo, slide, video | 20% |

---

## 🔹 Lịch trình dự án (4 tuần)

### Tuần 1 (30/09 - 06/10): Setup & Thiết kế
- **Nhiệm vụ**:
  - Thành viên 1: Tạo repo, setup Docker Compose.
  - Thành viên 2: Khởi tạo Northwind schema, chèn dữ liệu mẫu.
  - Thành viên 3: Setup Spark project (Python).
  - Thành viên 4: Cấu hình HDFS cluster (3 nodes).
  - Thành viên 5: Tạo template báo cáo.
- **Milestone**: Môi trường chạy, schema sẵn sàng.

### Tuần 2 (07/10 - 13/10): CDC & Streaming
- **Nhiệm vụ**:
  - Thành viên 2: Cấu hình Debezium, test CDC.
  - Thành viên 3: Viết Spark job đọc Kafka, lưu dữ liệu thô.
  - Thành viên 1: Tích hợp Debezium-Kafka.
  - Thành viên 4: Test lưu HDFS.
  - Thành viên 5: Test CDC, viết docs.
- **Milestone**: Dữ liệu từ MySQL → Kafka → HDFS (thô).

### Tuần 3 (14/10 - 20/10): Transform & Load
- **Nhiệm vụ**:
  - Thành viên 3: Implement aggregation (tổng doanh thu, số đơn hàng).
  - Thành viên 4: Lưu aggregation vào HDFS, query Spark SQL.
  - Thành viên 2: Test UPDATE/DELETE CDC.
  - Thành viên 1: Setup error handling.
  - Thành viên 5: Test pipeline, viết test cases.
- **Milestone**: Pipeline ETL hoàn chỉnh.

### Tuần 4 (21/10 - 28/10): Dashboard & Báo cáo
- **Nhiệm vụ**:
  - Thành viên 4: Tạo dashboard Grafana (tùy chọn).
  - Thành viên 3: Optimize Spark job (watermarking).
  - Thành viên 1: Deploy pipeline (CI/CD).
  - Thành viên 5: Hoàn thành báo cáo, slide, video demo.
  - Toàn nhóm: Review code, test cuối.
- **Milestone**: Demo hoàn chỉnh, nộp báo cáo.

**Họp**: Thứ 7, 10h sáng (Google Meet/Zalo).  
**Theo dõi**: GitHub Projects (Kanban board).

---

## 🔹 Lưu ý

- **Binlog MySQL**: Phải bật binlog và dùng format `ROW`.
- **Kafka topics**: Mỗi bảng (`customers`, `orders`, `order_details`) có topic riêng (`cdc.northwind.<table>`).
- **HDFS partition**: Dữ liệu thô và aggregation partition theo ngày để tối ưu query.
- **Timestamp**: Dữ liệu từ MySQL lưu timestamp UTC, Spark sẽ xử lý nếu cần múi giờ +07:00.

---

## 🔹 Khắc phục sự cố

- **Debezium không gửi dữ liệu**:
  - Kiểm tra log:
    ```bash
    docker logs connect
    ```
  - Đảm bảo binlog bật:
    ```bash
    docker exec -it mysql mysql -uroot -proot -e "SHOW VARIABLES LIKE 'log_bin';"
    ```

- **Spark job lỗi**:
  - Thêm debug:
    ```python
    df.show()
    ```
  - Kiểm tra Kafka consumer:
    ```bash
    docker exec -it connect /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic cdc.northwind.orders
    ```

- **HDFS permission lỗi**:
  - Chạy với user `hdfs`:
    ```bash
    docker exec -it hdfs-namenode hdfs dfs -chown -R hdfs:hdfs /northwind
    ```

---

## 🔹 Công nghệ sử dụng

- **MySQL**: 8.0
- **Kafka**: Confluent 7.4.0
- **Debezium**: 2.3.0
- **Spark**: 3.4.0 (Structured Streaming)
- **HDFS**: Hadoop 3.2.1
- **Python**: 3.9 (pyspark, kafka-python)
- **Docker & Docker Compose**

---

## 📧 Liên hệ

Mở issue trên GitHub hoặc liên hệ nhóm qua [Zalo/Slack].