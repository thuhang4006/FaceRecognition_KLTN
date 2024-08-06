﻿# FaceRecognition_KLTN
1. Tạo (Cập nhật) tệp requirements.txt chứa tất cả thư viện: pip freeze > requirements.txt
2. Install PyTorch: 
    - PyTorch Build: Stable (2.4.0)
    - Your OS: Windows
    - Package: Pip
    - Language: Python
    - Compute Platform: CUDA 12.1
    - Run this Command: pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
3. Chạy giao diện quản lý: app.py
4. Chạy màn hình điểm danh:
   - Chạy attendance.py
   - Nhấn mục điểm danh trong giao diện quản lý của giảng viên (teacher)
5. Thư mục src/data lưu tất cả embeddings được chuyển từ ảnh (lưu trên Firebase) thu thập được của sinh viên.
6. Dòng code "self.face_embedding_updater.update_face_embeddings()" (dòng 22 trong attendance.py) cập nhật lại các embeddings của sinh viên nếu có thay đổi trên Firebase, thực hiện mỗi khi chạy giao diện điểm danh attendance.py
