from flask import Flask, render_template, request, jsonify
import socket
import json
import base64
import tkinter as tk
from tkinter import messagebox
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import DES3, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA512
from Crypto.Util.Padding import unpad
import threading
import time

app = Flask(__name__)

class ReceiverWeb:
    def __init__(self):
        self.server = None
        self.is_listening = False
        self.logs = []
        self.current_connection = None
        self.listen_port = 12345
        
    def log(self, msg):
        self.logs.append(f"{time.strftime('%H:%M:%S')} - {msg}")
        if len(self.logs) > 100:  # Giới hạn log
            self.logs.pop(0)
            
    def get_logs(self):
        return self.logs.copy()

    def get_local_ip(self):
        """Lấy địa chỉ IP local của máy"""
        try:
            # Tạo socket tạm thời để lấy IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

receiver = ReceiverWeb()

# Load khóa
with open("receiver_private.pem", "rb") as f:
    receiver_private_key = RSA.import_key(f.read())
with open("sender_public.pem", "rb") as f:
    sender_public_key = RSA.import_key(f.read())

@app.route('/')
def index():
    return render_template('receiver.html')

@app.route('/get_local_ip')
def get_local_ip():
    """API để lấy địa chỉ IP local"""
    return jsonify({
        'local_ip': receiver.get_local_ip(),
        'port': receiver.listen_port
    })

@app.route('/start_listening', methods=['POST'])
def start_listening():
    if receiver.is_listening:
        return jsonify({'error': 'Đã đang lắng nghe'})
    
    try:
        receiver.server = socket.socket()
        # Bind trên tất cả các interface (0.0.0.0) để có thể nhận kết nối từ mạng LAN
        receiver.server.bind(("0.0.0.0", receiver.listen_port))
        receiver.server.listen(1)
        receiver.is_listening = True
        receiver.log(f"🔄 Đang lắng nghe kết nối từ mạng LAN trên port {receiver.listen_port}...")
        receiver.log(f"📍 Địa chỉ IP local: {receiver.get_local_ip()}")
        
        # Chạy việc lắng nghe trong thread riêng
        threading.Thread(target=accept_connection_thread, daemon=True).start()
        
        return jsonify({
            'success': True,
            'status': 'Đang lắng nghe',
            'local_ip': receiver.get_local_ip(),
            'port': receiver.listen_port,
            'logs': receiver.get_logs()
        })
        
    except Exception as e:
        receiver.log(f"❌ Lỗi khởi tạo server: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Lỗi khởi tạo',
            'logs': receiver.get_logs()
        })

def accept_connection_thread():
    try:
        receiver.server.settimeout(1)  # Timeout để có thể dừng
        while receiver.is_listening:
            try:
                conn, addr = receiver.server.accept()
                receiver.log(f"✅ Đã kết nối từ {addr[0]}:{addr[1]}")
                receiver.current_connection = conn
                
                # Xử lý kết nối trong thread riêng
                threading.Thread(target=handle_connection_thread, args=(conn, addr), daemon=True).start()
                break
                
            except socket.timeout:
                continue
            except Exception as e:
                receiver.log(f"❌ Lỗi kết nối: {str(e)}")
                break
                
    except Exception as e:
        receiver.log(f"❌ Lỗi trong accept_connection: {str(e)}")
    finally:
        if receiver.server:
            receiver.server.close()
            receiver.server = None

def handle_connection_thread(conn, addr):
    try:
        if conn.recv(1024) != b"Hello!":
            raise Exception("❌ Tin nhắn khởi đầu không hợp lệ")
        conn.sendall(b"Ready!")
        receiver.log("✅ Đã gửi phản hồi Ready!")

        meta_data = json.loads(conn.recv(4096).decode())
        metadata = meta_data.get("metadata")
        signature = base64.b64decode(meta_data.get("signature"))
        h_meta = SHA512.new(json.dumps(metadata).encode())
        pkcs1_15.new(sender_public_key).verify(h_meta, signature)
        receiver.log("✅ Metadata đã được xác thực.")
        receiver.log(f"📄 Thông tin file: {metadata.get('filename')} - {metadata.get('filesize')} bytes")

        enc_session_key = base64.b64decode(conn.recv(2048))
        cipher_rsa = PKCS1_OAEP.new(receiver_private_key, hashAlgo=SHA512)
        session_key = cipher_rsa.decrypt(enc_session_key)
        receiver.log("🔐 Đã giải mã khóa phiên.")

        conn_file = conn.makefile("rb")
        chunks = [b"", b"", b""]
        received_chunks = 0

        receiver.log(f"🔄 Bắt đầu nhận {len(chunks)} chunks...")

        while True:
            try:
                line = conn_file.readline()
                if not line:
                    receiver.log("⚠️ Không nhận được dữ liệu từ sender")
                    break
                line = line.strip()
                if not line:
                    continue

                # 1. Giải mã JSON packet
                packet = json.loads(line.decode())
                idx = packet.get("index")
                iv = base64.b64decode(packet.get("iv"))
                cipher = base64.b64decode(packet.get("cipher"))
                hash_val = packet.get("hash")
                sig = base64.b64decode(packet.get("sig"))

                receiver.log(f"📦 Nhận packet {idx}: {len(cipher)} bytes")

                h = SHA512.new(iv + cipher)
                pkcs1_15.new(sender_public_key).verify(h, sig)
                if h.hexdigest() != hash_val:
                    raise Exception(f"❌ Hash không khớp tại đoạn {idx}")

                cipher_des3 = DES3.new(session_key, DES3.MODE_CBC, iv)
                plaintext = unpad(cipher_des3.decrypt(cipher), DES3.block_size)
                chunks[idx] = plaintext
                received_chunks += 1
                receiver.log(f"✅ Đoạn {idx} đã kiểm tra và giải mã thành công ({len(plaintext)} bytes)")

                # 2. Nhận chữ ký xác nhận
                sig_ack_line = conn_file.readline().strip()
                if not sig_ack_line:
                    raise Exception("❌ Không nhận được sig_ack từ sender")

                sig_ack_str = sig_ack_line.decode(errors='ignore')
                sig_ack_str = ''.join(sig_ack_str.strip().split())
                padding = len(sig_ack_str) % 4
                if padding:
                    sig_ack_str += '=' * (4 - padding)

                sig_ack = base64.b64decode(sig_ack_str)
                h_ack = SHA512.new(iv + cipher)
                pkcs1_15.new(sender_public_key).verify(h_ack, sig_ack)
                receiver.log(f"🔐 Đã xác minh chữ ký phản hồi cho đoạn {idx}")

            except Exception as e:
                receiver.log(f"⚠️ Lỗi tại đoạn {idx if 'idx' in locals() else 'unknown'}: {e}")
                break

            if all(chunks):
                receiver.log(f"✅ Đã nhận đủ {received_chunks} chunks")
                break

        receiver.log(f"📊 Tổng kết: Nhận được {received_chunks}/{len(chunks)} chunks")

        filename = metadata.get("filename", "recording_received.mp3")
        # Làm sạch tên file để tránh ký tự không hợp lệ
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        if not filename.endswith(('.mp3', '.wav', '.m4a', '.aac')):
            filename += '.mp3'
        
        receiver.log(f"📁 Đang lưu file: {filename}")
        receiver.log(f"📊 Số chunks nhận được: {len([c for c in chunks if c])}")
        
        # Kiểm tra xem tất cả chunks có dữ liệu không
        if not all(chunks):
            missing_chunks = [i for i, chunk in enumerate(chunks) if not chunk]
            receiver.log(f"❌ Thiếu chunks: {missing_chunks}")
            raise Exception(f"Thiếu chunks: {missing_chunks}")
        
        try:
            # Kiểm tra quyền ghi file
            current_dir = os.getcwd()
            receiver.log(f"📂 Thư mục hiện tại: {current_dir}")
            
            with open(filename, "wb") as f:
                total_bytes = 0
                for i, chunk in enumerate(chunks):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        receiver.log(f"📝 Đã ghi chunk {i}: {len(chunk)} bytes")
                    else:
                        receiver.log(f"⚠️ Chunk {i} rỗng, bỏ qua")
            
            # Kiểm tra file đã được tạo
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                receiver.log(f"🎉 File đã được ghép và lưu thành công: {filename} ({file_size} bytes)")
            else:
                receiver.log(f"❌ File không được tạo: {filename}")
                raise Exception("File không được tạo")
                
            conn.sendall(b"ACK")
            receiver.log("✅ Đã gửi ACK cho người gửi")
            
        except Exception as e:
            receiver.log(f"❌ Lỗi khi lưu file: {str(e)}")
            raise e

    except Exception as e:
        receiver.log(f"⚠️ Lỗi: {e}")
        try:
            conn.sendall(b"NACK")
        except:
            pass
    finally:
        conn.close()
        receiver.current_connection = None
        receiver.is_listening = False

@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    receiver.is_listening = False
    if receiver.current_connection:
        receiver.current_connection.close()
        receiver.current_connection = None
    if receiver.server:
        receiver.server.close()
        receiver.server = None
    
    receiver.log("🛑 Đã dừng lắng nghe")
    return jsonify({
        'success': True,
        'status': 'Đã dừng lắng nghe',
        'logs': receiver.get_logs()
    })

@app.route('/get_status')
def get_status():
    return jsonify({
        'is_listening': receiver.is_listening,
        'has_connection': receiver.current_connection is not None,
        'local_ip': receiver.get_local_ip(),
        'port': receiver.listen_port,
        'logs': receiver.get_logs()
    })

@app.route('/list_files')
def list_files():
    """API để liệt kê các file âm thanh đã nhận"""
    try:
        current_dir = os.getcwd()
        audio_files = []
        
        for file in os.listdir(current_dir):
            if file.endswith(('.mp3', '.wav', '.m4a', '.aac')):
                file_path = os.path.join(current_dir, file)
                file_size = os.path.getsize(file_path)
                audio_files.append({
                    'name': file,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                })
        
        return jsonify({
            'success': True,
            'files': audio_files,
            'current_directory': current_dir
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')