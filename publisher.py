import paho.mqtt.client as mqtt
import time
import json
import random
from datetime import datetime
import ssl

ALAMAT_BROKER = "broker.hivemq.com"
PORT_BROKER = 8883

USER_MQTT = "jery"
PASS_MQTT = "12345"

TOPIK_DASAR = "/tugasMajeri-inventarisBarang" 

DAFTAR_PRODUK = [
    {"id_produk": "EsKrim", "stok_awal": 50, "batas_minimum": 5},
    {"id_produk": "DAGING_Sapi_Premium", "stok_awal": 30, "batas_minimum": 3},
    {"id_produk": "SUSU_FullCream", "stok_awal": 80, "batas_minimum": 8},
    {"id_produk": "nugget", "stok_awal": 30, "batas_minimum": 10},
    {"id_produk": "dagingAyam", "stok_awal": 34, "batas_minimum": 12},
    {"id_produk": "YOGHURT_Strawberry", "stok_awal": 60, "batas_minimum": 6},
    {"id_produk": "KEJU_Cheddar", "stok_awal": 45, "batas_minimum": 5},
    {"id_produk": "IKAN_Fillet_Beku", "stok_awal": 28, "batas_minimum": 4},
    {"id_produk": "SAYUR_Bayam_Fresh", "stok_awal": 25, "batas_minimum": 5},
    {"id_produk": "BUAH_Apel_Import", "stok_awal": 40, "batas_minimum": 6},
]
stok_saat_ini = {p["id_produk"]: p["stok_awal"] for p in DAFTAR_PRODUK}

def saat_terhubung(klien, data_pengguna, bendera, kode_hasil):
    if kode_hasil == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Klien berhasil terhubung ke Broker MQTT via TLS/SSL!")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gagal terhubung, kode error: {kode_hasil}")
        if kode_hasil == 4:
            print("Peringatan: Gagal terhubung, kemungkinan username atau password salah.")
        if kode_hasil == 5:
            print("Peringatan: Gagal terhubung, kemungkinan masalah otorisasi atau SSL/TLS.")

def buat_data_retail(id_produk_terpilih, batas_minimum_produk):
    global stok_saat_ini

    stok_produk = stok_saat_ini[id_produk_terpilih]

    if stok_produk > 0:
        jumlah_terjual = random.randint(1, 5)
        stok_produk = max(0, stok_produk - jumlah_terjual)
    else:
        stok_produk = 0

    if stok_produk <= batas_minimum_produk and random.random() < 0.3:
        jumlah_restock = random.randint(10, 30)
        stok_produk += jumlah_restock
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] RESTOCK: {id_produk_terpilih} +{jumlah_restock} unit. Stok Baru: {stok_produk}")

    stok_saat_ini[id_produk_terpilih] = stok_produk

    perlu_restock = stok_produk <= batas_minimum_produk

    suhu_rak_c = round(random.uniform(-5.0, 5.0), 1) 
    kelembaban_rak_persen = round(random.uniform(70.0, 90.0), 1)

    if not (-10.0 <= suhu_rak_c <= 50.0): 
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [VALIDASI ERROR] Suhu {id_produk_terpilih} tidak valid: {suhu_rak_c}°C. Menyesuaikan ke rentang aman.")
        suhu_rak_c = random.uniform(-2.0, 4.0) 
    
    if not (0.0 <= kelembaban_rak_persen <= 100.0):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [VALIDASI ERROR] Kelembaban {id_produk_terpilih} tidak valid: {kelembaban_rak_persen}%. Menyesuaikan ke rentang aman.")
        kelembaban_rak_persen = random.uniform(50.0, 80.0)

    
    if stok_produk > 200:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [VALIDASI ERROR] Stok {id_produk_terpilih} terlalu tinggi: {stok_produk}. Menyesuaikan ke 200.")
        stok_produk = 200
    
    notifikasi_suhu_tidak_ideal = False
    if "ES_KRIM" in id_produk_terpilih and suhu_rak_c > -2:
        notifikasi_suhu_tidak_ideal = True
    elif ("DAGING" in id_produk_terpilih or "SUSU" in id_produk_terpilih) and suhu_rak_c > 3:
        notifikasi_suhu_tidak_ideal = True
    
    data_yang_dikirim = {
        "id_produk": id_produk_terpilih,
        "jumlah_stok": stok_produk,
        "batas_minimum_stok": batas_minimum_produk,
        "perlu_restock": perlu_restock,
        "suhu_rak_c": suhu_rak_c,
        "kelembaban_rak_persen": kelembaban_rak_persen,
        "notifikasi_suhu_tidak_ideal": notifikasi_suhu_tidak_ideal,
        "waktu_data": datetime.now().isoformat()
    }
    return data_yang_dikirim

if __name__ == "__main__":
    klien = mqtt.Client()
    klien.on_connect = saat_terhubung
    
    klien.username_pw_set(USER_MQTT, PASS_MQTT)
    klien.tls_set(tls_version=ssl.PROTOCOL_TLS) 

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mencoba terhubung ke broker: {ALAMAT_BROKER}:{PORT_BROKER} (via TLS/SSL)...")
    try:
        klien.connect(ALAMAT_BROKER, PORT_BROKER, 60)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Gagal koneksi ke broker. Detail: {e}")
        exit(1)

    klien.loop_start()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Publisher simulasi retail dimulai.")
    print(f"Data akan dikirim ke topik: {TOPIK_DASAR}/<id_produk>/data")

    try:
        while True:
            produk_terpilih = random.choice(DAFTAR_PRODUK)
            id_produk_saat_ini = produk_terpilih["id_produk"]
            batas_minimum_produk = produk_terpilih["batas_minimum"]

            data_yang_dikirim = buat_data_retail(id_produk_saat_ini, batas_minimum_produk)
            
            topik_kirim = f"{TOPIK_DASAR}/{id_produk_saat_ini}/data"
            
            klien.publish(topik_kirim, json.dumps(data_yang_dikirim), qos=1)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] KIRIM ke '{topik_kirim}': {json.dumps(data_yang_dikirim)}")
            
            time.sleep(random.uniform(3, 7))
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Pengiriman data dihentikan oleh pengguna.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR SAAT BERJALAN: {e}")
    finally:
        klien.loop_stop()
        klien.disconnect()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Koneksi MQTT diputus.")