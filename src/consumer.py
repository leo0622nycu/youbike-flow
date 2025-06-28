"""
Kafka → PostgreSQL Consumer  (psycopg v3)
把 youbike_raw 的 JSON 轉成資料表 inventory_stage 欄位
"""

import json, os
import psycopg
from kafka import KafkaConsumer

# ---------- 0. 參數 ----------
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC     = os.getenv("KAFKA_TOPIC", "youbike_raw")

# ---------- 1. PostgreSQL 連線 ----------
PG_CONN = psycopg.connect(
    host="localhost",
    port=15432,
    dbname="youbike",
    user="youbike",
    password=os.getenv("POSTGRES_PASSWORD", "your_password"),  # ← 請換成真密碼或環境變數
    autocommit=True
)
cur = PG_CONN.cursor()

# ---------- 2. Kafka Consumer ----------
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[BOOTSTRAP],
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="youbike_pg_writer"
)

# ---------- 3. SQL ----------
SQL = """
INSERT INTO inventory_stage
(sno, sna, sarea, mday, lat, lng, sbi, bemp, tot)
VALUES (%(sno)s, %(sna)s, %(sarea)s, %(mday)s,
        %(lat)s, %(lng)s, %(sbi)s, %(bemp)s, %(tot)s)
"""

print("Consumer started…  Ctrl+C to stop")

try:
    for msg in consumer:
        src = msg.value  # 原始 JSON dict

        # ---------- 4. 欄位映射 ----------
        rec = {
            "sno":  src["sno"],
            "sna":  src["sna"],
            "sarea": src["sarea"],
            "mday": src["mday"],
            "lat":  src["latitude"],
            "lng":  src["longitude"],
            "sbi":  src["available_rent_bikes"],
            "bemp": src["available_return_bikes"],
            "tot":  src["Quantity"],
        }

        # ---------- 5. 寫入 ----------
        try:
            cur.execute(SQL, rec)
        except Exception as e:
            print("write error:", e, "data sno:", rec["sno"])

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
    cur.close()
    PG_CONN.close()

