import os
import json
import requests
import cv2
from datetime import datetime
from models.mtcnn_model import MTCNNModel
from models.facenet_model import FaceNetModel
from firebase_service import FirebaseService
import numpy as np

class FaceEmbeddingUpdater:
    def __init__(self, data_directory='data', device='cpu'):
        self.data_directory = data_directory
        self.device = device

        # Khởi tạo các mô hình
        self.mtcnn_model = MTCNNModel(device=self.device)
        self.facenet_model = FaceNetModel(device=self.device)
        self.firebase_service = FirebaseService()

    def update_face_embeddings(self):
        print("Cập nhật dữ liệu embeddings...")

        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)
            print(f"Thư mục data đã được tạo: {self.data_directory}")

        # Lấy danh sách sinh viên từ Firebase
        students = self.firebase_service.get_all_students_dict()
        print(f"Sinh viên: {students}")

        for student in students:
            student_id = student.get('studentID')
            faces_data = student.get('facesData', [])
            updated_time = student.get('updatedTime')
            created_time = student.get('createdTime')

            # Bỏ qua nếu không có facesData
            if not faces_data:
                continue

            # Kiểm tra và tạo thư mục cho sinh viên nếu chưa tồn tại
            student_folder = os.path.join(self.data_directory, student_id)
            if not os.path.exists(student_folder):
                os.makedirs(student_folder)
                print(f"Đã tạo thư mục cho sinh viên: {student_folder}")

            # Đọc thời gian cập nhật từ metadata
            metadata_path = os.path.join(student_folder, 'metadata.json')
            last_updated_time = None
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    last_updated_time = metadata.get('time')
                    if last_updated_time:
                        last_updated_time = datetime.fromisoformat(last_updated_time)

            # Xác định thời gian cần lưu
            time_to_save = updated_time if updated_time else created_time
            if time_to_save:
                time_to_save = time_to_save.isoformat()

            # Kiểm tra xem có cần cập nhật không
            if last_updated_time and datetime.fromisoformat(time_to_save) <= last_updated_time:
                print(f"Bỏ qua cập nhật cho sinh viên {student_id} vì dữ liệu đã cập nhật.")
                continue

            # Xóa các file cũ trước khi xử lý ảnh mới
            self.clear_old_embeddings(student_folder)

            # Cập nhật embeddings nếu cần thiết
            self.process_faces(student_folder, faces_data)

            # Lưu thông tin thời gian cập nhật vào metadata
            metadata = {'studentID': student_id, 'time': time_to_save}
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            print(f"Đã lưu metadata cho sinh viên {student_id}")

    def clear_old_embeddings(self, student_folder):
        """
        Xóa các file embedding cũ trong thư mục sinh viên.
        Input: student_folder (str): Thư mục của sinh viên chứa các file embedding.
        """
        for file_name in os.listdir(student_folder):
            if file_name.endswith('.npy'):
                os.remove(os.path.join(student_folder, file_name))
        print(f"Xóa các file embedding cũ trong: {student_folder}")

    def process_faces(self, student_folder, faces_data):
        """
        Xử lý ảnh khuôn mặt và lưu embeddings.
        Input:
            student_folder (str): Thư mục lưu embeddings cho sinh viên.
            faces_data (list): Danh sách dữ liệu khuôn mặt từ Firebase.
        """
        for face_data in faces_data:
            file_name = face_data.get('fileName')
            image_url = face_data.get('imageUrl')

            # Tải và xử lý ảnh
            image = self.download_image(image_url)
            if image is not None:
                boxes, landmarks = self.mtcnn_model.detect_faces(image)
                if boxes is not None and landmarks is not None:
                    aligned_faces = self.mtcnn_model.extract_faces(image, boxes, landmarks)
                    for i, aligned_face in enumerate(aligned_faces):
                        if aligned_face['aligned_face'].size == 0:
                            print(f"Detected face {i} is empty in image {file_name}")
                            continue  # Khuôn mặt rỗng

                        # Lấy embedding và lưu
                        embedding = self.facenet_model.get_embedding(aligned_face['aligned_face'])
                        if embedding is not None and embedding.size > 0:
                            print(f"Embedding của {file_name} có dạng {embedding.shape}")
                            self.save_embedding(student_folder, file_name, embedding)
                        else:
                            print(f"{file_name} có embedding rỗng")
                else:
                    print(f"Không nhận diện được khuôn mặt trong ảnh {file_name}")
            else:
                print(f"Không thể tải ảnh từ {image_url}")

    def download_image(self, url):
        """
        Tải ảnh từ URL.
        Input: url (str): URL của ảnh.
        Output: numpy.ndarray: Ảnh đã được tải xuống.
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
                return image
        except requests.RequestException as e:
            print(f"Lỗi khi tải ảnh: {e}")
        return None

    def save_embedding(self, folder, file_name, embedding):
        """
        Lưu embedding dưới dạng file .npy.
        Input:
            folder (str): Thư mục lưu embeddings.
            file_name (str): Tên file của ảnh.
            embedding (numpy.ndarray): Embedding của khuôn mặt.
        """

        if not os.path.exists(folder):
            os.makedirs(folder)

        # Làm sạch tên file tránh các ký tự không hợp lệ
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        embedding_file = os.path.join(folder, f"{sanitized_file_name}.npy")

        # Save embedding
        try:
            if embedding.size > 0:
                np.save(embedding_file, embedding)
                print(f"Lưu embedding thành công cho {file_name} với {embedding_file}")
            else:
                print(f"Không lưu {file_name} vì embedding trống.")
        except Exception as e:
            print(f"Không lưu được embedding cho {file_name}: {e}")

    def get_all_embeddings(self):
        all_embeddings = {}
        for student_dir in os.listdir('data'):
            student_path = os.path.join('data', student_dir)
            print(f"{student_dir}")
            if os.path.isdir(student_path):
                # Load metadata.json lấy studentID
                metadata_path = os.path.join(student_path, 'metadata.json')
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                student_id = metadata.get('studentID')

                # Load tất cả file .npy của SV
                embeddings = []
                for file in os.listdir(student_path):
                    if file.endswith('.npy'):
                        file_path = os.path.join(student_path, file)
                        embedding = np.load(file_path)
                        embeddings.append({'embedding': embedding})

                all_embeddings[student_id] = embeddings
        return all_embeddings

