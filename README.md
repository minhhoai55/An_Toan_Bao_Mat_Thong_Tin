# An_Toan_Bao_Mat_Thong_Tin
🔐 Ứng dụng bảo mật tin nhắn âm thanh với mã hóa DES và xác thực RSA

📝 Giới thiệu

Đây là một ứng dụng Python sử dụng Flask và Socket để truyền file âm thanh giữa hai máy tính trong mạng LAN, đảm bảo bảo mật bằng mã hóa DES3, mã hóa khóa bằng RSA và xác thực dữ liệu bằng chữ ký số SHA512.

⚙️ Tính năng chính

Mã hóa file âm thanh bằng DES3 (mã hóa đối xứng)

Mã hóa khóa phiên DES3 bằng RSA (mã hóa bất đối xứng)

Tạo chữ ký số bằng SHA512 và RSA

Giao diện web cho người gửi và người nhận

Truyền file âm thanh qua socket trong mạng LAN

🖥️ Yêu cầu hệ thống

Python >= 3.8

Thư viện: flask, socket, pycryptodome, flask-socketio, requests, eventlet

Cài đặt:

pip install -r requirements.txt

🚀 Cách sử dụng

Khởi động Receiver (Người nhận)
python receiver_web.py

Truy cập tại: http://localhost:5001

Khởi động Sender (Người gửi)
python sender_web.py

Truy cập tại: http://localhost:5000

Truyền file
Trên giao diện Sender:

Nhập IP của Receiver

Chọn file âm thanh (.mp3/.wav)

Bấm "Bắt đầu kết nối" → "Gửi File"

Trên giao diện Receiver:

Bấm "Bắt đầu lắng nghe"

Sau khi nhận file, chọn "Phát" để kiểm tra

🔒 Mô hình bảo mật

File được chia thành các phần (nếu lớn)

Mỗi phần được mã hóa bằng khóa phiên DES3

Khóa DES3 được mã hóa bằng RSA công khai của người nhận

Dữ liệu được ký SHA512 bởi người gửi

Người nhận giải mã khóa và nội dung, xác thực chữ ký

📁 Cấu trúc thư mục

. ├── sender_web.py # Giao diện người gửi ├── receiver_web.py # Giao diện người nhận ├── templates/ # HTML templates ├── static/ # CSS & JS ├── utils/ # Các hàm mã hóa, xác thực └── README.md # Tài liệu này

📚 Tài liệu tham khảo

Cryptography and Network Security – William Stallings

Handbook of Applied Cryptography – Menezes et al.

https://pycryptodome.readthedocs.io
