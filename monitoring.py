from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import ssl
import threading
import os
from collections import deque

ALAMAT_BROKER = "broker.hivemq.com"
PORT_BROKER = 8883

USER_MQTT = "jery"
PASS_MQTT = "12345"

TOPIK_LANGGANAN = "/tugasMajeri-inventarisBarang/#" 

data_terbaru_produk = {} 
historical_product_data = {} 
MAX_HISTORY_POINTS = 30 

data_lock = threading.Lock()

app = Flask(__name__)
app.secret_key = os.urandom(24) 

monitor_USER = "admin"
monitor_PASS = "admin123"

def saat_terhubung(klien, data_pengguna, bendera, kode_hasil):
    if kode_hasil == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] Klien berhasil terhubung ke Broker MQTT via TLS/SSL!")
        klien.subscribe(TOPIK_LANGGANAN)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] Berlangganan ke topik: '{TOPIK_LANGGANAN}'")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] Gagal terhubung, kode error: {kode_hasil}")
        if kode_hasil == 4:
            print("[MQTT] Peringatan: Gagal terhubung, kemungkinan username atau password salah.")
        if kode_hasil == 5:
            print("[MQTT] Peringatan: Gagal terhubung, kemungkinan masalah otorisasi atau SSL/TLS.")

def saat_pesan_diterima(klien, data_pengguna, pesan):
    with data_lock:
        try:
            payload_str = pesan.payload.decode('utf-8')
            data = json.loads(payload_str)
            id_produk = data.get('id_produk', 'UNKNOWN')
            
            data_terbaru_produk[id_produk] = data
            
            if id_produk not in historical_product_data:
                historical_product_data[id_produk] = deque(maxlen=MAX_HISTORY_POINTS)
            
            historical_product_data[id_produk].append(data)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] Pesan diterima dari '{pesan.topic}' untuk produk '{id_produk}'. Variabel global diupdate.")

        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] ERROR: Gagal mengurai pesan JSON. Payload: {pesan.payload.decode('utf-8')}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] ERROR: Terjadi kesalahan saat memproses pesan. Detail: {e}")

def jalankan_klien_mqtt():
    klien = mqtt.Client()
    klien.on_connect = saat_terhubung
    klien.on_message = saat_pesan_diterima

    klien.username_pw_set(USER_MQTT, PASS_MQTT)
    klien.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2) 

    print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] Mencoba terhubung ke broker: {ALAMAT_BROKER}:{PORT_BROKER} (via TLS/SSL)...")
    try:
        klien.connect(ALAMAT_BROKER, PORT_BROKER, 60)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [MQTT] ERROR: Gagal koneksi ke broker. Detail: {e}")
        return
    klien.loop_forever()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == monitor_USER and password == monitor_PASS:
            session['logged_in'] = True
            flash('Berhasil masuk!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/data')
def get_monitor_data():
    with data_lock:
        data_untuk_api = {
            "data_produk": data_terbaru_produk, 
            "historical_data": {}, 
            "waktu_sekarang": datetime.now().strftime('%H:%M:%S')
        }

        for product_id, history_deque in historical_product_data.items():
            if history_deque: 
                data_untuk_api["historical_data"][product_id] = {
                    "timestamps": [d.get("waktu_data", "N/A") for d in history_deque],
                    "stock": [d.get("jumlah_stok", 0) for d in history_deque],
                    "temperature": [d.get("suhu_rak_c", 0) for d in history_deque],
                    "humidity": [d.get("kelembaban_rak_persen", 0) for d in history_deque]
                }
        
        return jsonify(data_untuk_api)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Anda telah keluar.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=jalankan_klien_mqtt)
    mqtt_thread.daemon = True 
    mqtt_thread.start()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] [WEB] monitor web berjalan di: http://127.0.0.1:5000/login") 
    app.run(host='0.0.0.0', port=5000, debug=False)
