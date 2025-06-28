import json, time, os, requests
from kafka import KafkaProducer

YBIKE_URL = ("https://tcgbusfs.blob.core.windows.net/"
             "dotapp/youbike/v2/youbike_immediate.json")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC     = os.getenv("KAFKA_TOPIC", "youbike_raw")
INTERVAL  = int(os.getenv("FETCH_INTERVAL_SEC", 30))

producer = KafkaProducer(
    bootstrap_servers=[BOOTSTRAP],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
)

def fetch_youbike():
    r = requests.get(YBIKE_URL, timeout=10)
    r.raise_for_status()
    return r.json()          # list[dict]

if __name__ == "__main__":
    print(f"Producer → {BOOTSTRAP}  topic:{TOPIC}")
    while True:
        try:
            rows = fetch_youbike()
            for rec in rows:
                producer.send(TOPIC, rec)
            producer.flush()
            print(f"[✓] sent {len(rows):4d} records  {time.strftime('%X')}")
        except Exception as e:
            print("[!] error:", e)
        time.sleep(INTERVAL)
