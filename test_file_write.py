#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra quyền ghi file
"""

import os
import time

def test_file_write():
    """Test khả năng ghi file"""
    print("🧪 Bắt đầu test khả năng ghi file...")
    
    # Lấy thư mục hiện tại
    current_dir = os.getcwd()
    print(f"📂 Thư mục hiện tại: {current_dir}")
    
    # Test tạo file đơn giản
    test_filename = "test_write.txt"
    test_content = "Đây là file test để kiểm tra quyền ghi"
    
    try:
        # Ghi file test
        with open(test_filename, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print(f"✅ Đã ghi file thành công: {test_filename}")
        
        # Kiểm tra file đã được tạo
        if os.path.exists(test_filename):
            file_size = os.path.getsize(test_filename)
            print(f"📊 Kích thước file: {file_size} bytes")
            
            # Đọc lại file để kiểm tra
            with open(test_filename, "r", encoding="utf-8") as f:
                content = f.read()
            
            if content == test_content:
                print("✅ Nội dung file khớp với dữ liệu ghi")
            else:
                print("❌ Nội dung file không khớp")
        else:
            print("❌ File không được tạo")
            
    except Exception as e:
        print(f"❌ Lỗi khi ghi file: {str(e)}")
        return False
    
    # Test tạo file âm thanh giả
    audio_filename = "test_audio.mp3"
    audio_content = b"FAKE_MP3_HEADER" + b"0" * 1000  # Giả lập file MP3
    
    try:
        with open(audio_filename, "wb") as f:
            f.write(audio_content)
        
        print(f"✅ Đã ghi file âm thanh test: {audio_filename}")
        
        if os.path.exists(audio_filename):
            file_size = os.path.getsize(audio_filename)
            print(f"📊 Kích thước file âm thanh: {file_size} bytes")
        else:
            print("❌ File âm thanh không được tạo")
            
    except Exception as e:
        print(f"❌ Lỗi khi ghi file âm thanh: {str(e)}")
        return False
    
    # Dọn dẹp file test
    try:
        os.remove(test_filename)
        os.remove(audio_filename)
        print("🧹 Đã xóa file test")
    except:
        pass
    
    print("🎉 Test hoàn thành!")
    return True

if __name__ == "__main__":
    test_file_write() 