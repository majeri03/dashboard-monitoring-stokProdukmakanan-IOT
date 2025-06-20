import paho.mqtt.client as mqtt
import json
from datetime import datetime
import ssl 

ALAMAT_BROKER = "broker.hivemq.com"
PORT_BROKER = 8883    

TOPIK_LANGGANAN = "/tugasMajeri-inventarisBarang/#" 

def saat_terhubung(klien, data_pengguna, bendera, kode_hasil):
    if kode_hasil == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Klien berhasil terhubung ke Broker MQTT via TLS/SSL!")
        klien.subscribe(TOPIK_LANGGANAN)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Berlangganan ke topik: '{TOPIK_LANGGANAN}'")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gagal terhubung, kode error: {kode_hasil}")
        if kode_hasil == 4:
            print("Peringatan: Gagal terhubung, kemungkinan username atau password salah.")
        if kode_hasil == 5:
            print("Peringatan: Gagal terhubung, kemungkinan masalah otorisasi atau SSL/TLS.")

def saat_pesan_diterima(klien, data_pengguna, pesan):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Pesan Diterima dari Topik: '{pesan.topic}'")
    try:
        data = json.loads(pesan.payload.decode('utf-8'))
        
        print(f"  ID Produk           : {data.get('id_produk', 'N/A')}")
        print(f"  Jumlah Stok Saat Ini: {data.get('jumlah_stok', 'N/A')}")
        print(f"  Batas Minimum Stok  : {data.get('batas_minimum_stok', 'N/A')}")
        print(f"  Perlu Restock?      : {data.get('perlu_restock', 'N/A')}")
        print(f"  Suhu Rak            : {data.get('suhu_rak_c', 'N/A')} °C")
        print(f"  Kelembaban Rak      : {data.get('kelembaban_rak_persen', 'N/A')} %")
        print(f"  Waktu Data          : {data.get('waktu_data', 'N/A')}")

        if data.get('perlu_restock'):
            print(f"  *** NOTIFIKASI: STOK {data.get('id_produk', '')} SANGAT RENDAH! MOHON SEGERA REKAM ULANG! ***")
        
        if data.get('notifikasi_suhu_tidak_ideal'):
            print(f"  !!! PERINGATAN: SUHU RAK {data.get('id_produk', '')} TIDAK IDEAL: {data.get('suhu_rak_c', '')}°C !!!")

    except json.JSONDecodeError:
        print(f"  ERROR: Gagal mengurai pesan JSON. Payload: {pesan.payload.decode('utf-8')}")
    except Exception as e:
        print(f"  ERROR: Terjadi kesalahan saat memproses pesan. Detail: {e}")

if __name__ == "__main__":
    klien = mqtt.Client()
    klien.on_connect = saat_terhubung
    klien.on_message = saat_pesan_diterima

    user_input_mqtt = input("Masukkan Username MQTT Anda: ")
    pass_input_mqtt = input("Masukkan Password MQTT Anda: ") 

    klien.username_pw_set(user_input_mqtt, pass_input_mqtt)

    klien.tls_set(tls_version=ssl.PROTOCOL_TLS)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mencoba terhubung ke broker: {ALAMAT_BROKER}:{PORT_BROKER} (via TLS/SSL)...")
    try:
        klien.connect(ALAMAT_BROKER, PORT_BROKER, 60)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Gagal koneksi ke broker. Detail: {e}")
        exit(1)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Subscriber dimulai, menunggu pesan...")
    klien.loop_forever()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Koneksi MQTT diputus.")