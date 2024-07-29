from datetime import datetime
import sys
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox, QSizePolicy, QSpacerItem, QGridLayout
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, QTime
import cv2
from firebase_service import FirebaseService
from face_embedding_updater import FaceEmbeddingUpdater
from models.mtcnn_model import MTCNNModel
from models.facenet_model import FaceNetModel
from sklearn.metrics.pairwise import cosine_similarity


class AttendanceSystem(QWidget):
    def __init__(self):
        super().__init__()
        self.firebase_service = FirebaseService()

        # Khởi tạo FaceEmbeddingUpdater và cập nhật embeddings
        self.face_embedding_updater = FaceEmbeddingUpdater()
        self.face_embedding_updater.update_face_embeddings()  # Cập nhật embeddings khi ứng dụng khởi động

        self.last_detection_time = QTime.currentTime()  # Thời điểm phát hiện khuôn mặt gần nhất
        self.timer_10min = QTimer()  # Timer để kiểm tra thời gian không phát hiện khuôn mặt
        self.timer_10min.timeout.connect(self.check_no_face_detected)

        # Khởi tạo MTCNN model
        self.mtcnn_model = MTCNNModel()

        # Khởi tạo FaceNet model
        self.facenet_model = FaceNetModel()

        # # Thêm khởi tạo timer_10min để chạy sau 10 phút
        # self.timer_10min.start(600000)  # 600000ms = 10 phút

        # ảnh thay thế
        self.replacement_camera = QPixmap('images/face_recognition.jpg')
        self.replacement_face = QPixmap('images/face.png')

        # Thiết lập giao diện chính
        self.setWindowTitle('Hệ thống điểm danh khuôn mặt')
        self.setGeometry(240, 140, 1400, 600)

        # Tạo các phần tử giao diện
        self.createUI()

        # Tạo layout chính và đặt các phần tử vào layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.titleLabel, alignment=Qt.AlignCenter)

        columnsLayout = QHBoxLayout()
        leftColumn = self.createLeftColumn()
        rightColumn = self.createRightColumn()
        columnsLayout.addLayout(leftColumn, 2)
        columnsLayout.addSpacing(20)  # Thêm khoảng cách giữa hai cột
        columnsLayout.addLayout(rightColumn, 2)

        mainLayout.addLayout(columnsLayout)
        self.setLayout(mainLayout)

        # Cài đặt camera
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateFrame)
        self.cap = None

        # Load dữ liệu trước
        self.subjects_data = self.firebase_service.get_all_subjects()
        self.teachers_data = self.firebase_service.get_all_teachers()

        # Load subjects
        self.loadSubjects()

        # Khởi tạo pygame và âm thanh
        pygame.init()
        pygame.mixer.init()
        self.success_sound = pygame.mixer.Sound('sounds/checked.mp3')

        # Biến lưu thông tin nhận diện trước đó
        self.last_recognized_student = None


    def createUI(self):
        # Tiêu đề chính
        self.titleLabel = QLabel('Hệ thống điểm danh khuôn mặt', self)
        self.titleLabel.setFont(QFont('Arial', 18))


        # Chọn Môn
        self.subjectLabel = QLabel('Môn học:', self)
        self.subjectComboBox = QComboBox(self)
        self.subjectComboBox.addItem('Chọn môn học')
        self.subjectComboBox.currentIndexChanged.connect(self.loadClasses)  # Kết nối với loadClasses

        # Chọn ca học
        self.classLabel = QLabel('Ca học:', self)
        self.classComboBox = QComboBox(self)
        self.classComboBox.addItem('Chọn ca học')
        self.classComboBox.currentIndexChanged.connect(self.updateClassInfo)

        # Chọn loại điểm danh
        self.attendanceTypeLabel = QLabel('Loại Điểm Danh:', self)
        self.attendanceTypeComboBox = QComboBox(self)
        self.attendanceTypeComboBox.addItems(['Vào', 'Ra'])

        # Màn hình nhận diện (camera)
        self.detectionScreen = QLabel(self)
        self.detectionScreen.setFixedSize(740, 540)
        self.detectionScreen.setPixmap(self.replacement_camera) # Hiển thị ảnh thay thế camera

        # Nút mở camera
        self.openCameraButton = QPushButton('Mở Camera', self)
        self.openCameraButton.clicked.connect(self.openCamera)
        self.openCameraButton.setStyleSheet("background-color: #1B1D7E; color: white; border-radius: 5px; padding: 10px;")

        # Nút tắt camera
        self.closeCameraButton = QPushButton('Tắt Camera', self)
        self.closeCameraButton.clicked.connect(self.closeCamera)
        self.closeCameraButton.setStyleSheet("background-color: #9B9BA0; color: black; border-radius: 5px; padding: 10px;")

        # Thông báo
        self.notificationLabel = QLabel('Vui lòng chọn Môn học, Ca học để mở Camera điểm danh!', self)
        self.notificationLabel.setFont(QFont('Arial', 8))

        # Màn hình nhận diện (face image)
        self.faceImage = QLabel(self)
        self.faceImage.setFixedSize(180, 180)
        scaled_pixmap = self.replacement_face.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.faceImage.setPixmap(scaled_pixmap)

        # Thông tin sinh viên
        self.studentIdLabel = QLabel('')
        self.studentNameLabel = QLabel('')
        self.timeLabel = QLabel('')

        # Thông tin buổi học
        self.subjectInfoLabel = QLabel('')
        self.teacherInfoLabel = QLabel('')
        self.timeInfoLabel = QLabel('')
        comboBoxStyle = """
            QComboBox {
                border: 1px solid gray; /* Đặt đường viền cho toàn bộ combobox */
                border-radius: 2px; /* Bo góc */
                padding: 5px; /* Khoảng cách bên trong combobox */
                background-color: white; /* Màu nền bên trong combobox */
            }
    
            QComboBox::drop-down {
                border-left: 1px solid gray; /* Đường viền bên trái cho phần mũi tên thả xuống */
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px; /* Chiều rộng của phần mũi tên thả xuống */
                background-color: #F0F0F0;
            }
            
            QComboBox::down-arrow {
                image: url(images/arrow.png);
                width: 10px;
            }
        """

        self.subjectComboBox.setStyleSheet(comboBoxStyle)
        self.classComboBox.setStyleSheet(comboBoxStyle)
        self.attendanceTypeComboBox.setStyleSheet(comboBoxStyle)

    def createLeftColumn(self):
        leftColumn = QVBoxLayout()

        # Nhóm Màn hình nhận diện
        recognitionGroup = QGroupBox("Màn hình nhận diện")
        recognitionLayout = QGridLayout()

        # Đặt khoảng cách giữa các widget
        recognitionLayout.setHorizontalSpacing(40)  # Khoảng cách ngang
        recognitionLayout.setVerticalSpacing(10)  # Khoảng cách dọc

        recognitionLayout.addWidget(self.subjectLabel, 0, 0)
        recognitionLayout.addWidget(self.subjectComboBox, 1, 0)
        recognitionLayout.addWidget(self.classLabel, 0, 1)
        recognitionLayout.addWidget(self.classComboBox, 1, 1)
        recognitionLayout.addWidget(self.attendanceTypeLabel, 0, 2)
        recognitionLayout.addWidget(self.attendanceTypeComboBox, 1, 2)

        # Điều chỉnh kích thước combobox
        self.subjectComboBox.setFixedSize(200, 30)
        self.classComboBox.setFixedSize(200, 30)
        self.attendanceTypeComboBox.setFixedSize(200, 30)

        # Tạo layout để căn giữa detectionScreen
        detectionScreenLayout = QVBoxLayout()
        detectionScreenLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        detectionScreenLayout.addWidget(self.detectionScreen, 0, Qt.AlignCenter)
        detectionScreenLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        # Thêm detectionScreenLayout vào recognitionLayout
        recognitionLayout.addLayout(detectionScreenLayout, 2, 0, 1, 3)

        recognitionLayout.addWidget(self.notificationLabel, 3, 0, 1, 3)

        # Thêm một layout để chứa hai nút "Mở Camera" và "Tắt Camera"
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.openCameraButton)
        buttonLayout.addSpacing(60)
        buttonLayout.addWidget(self.closeCameraButton)

        recognitionLayout.addLayout(buttonLayout, 4, 0, 1, 3)  # Thêm layout của nút vào layout chính

        recognitionGroup.setLayout(recognitionLayout)

        recognitionGroup.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid gray;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 16px;
                        margin-top: 20px;
                        margin-left: 15px;
                        background-color: #FFFFFF;
                        padding: 10px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        padding: 0 3px;
                        top: 10px;
                        left: 25px;
                    }
                """)

        recognitionGroup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        leftColumn.addWidget(recognitionGroup)

        return leftColumn

    def createRightColumn(self):
        rightColumn = QVBoxLayout()

        # Nhóm Điểm danh thành công
        successGroup = QGroupBox("Điểm danh thành công")
        successLayout = QGridLayout()

        # Thêm ảnh thay thế vào layout và căn giữa nó
        imageLayout = QHBoxLayout()
        imageLayout.addStretch()  # Thêm khoảng trắng ở bên trái của ảnh
        imageLayout.addWidget(self.faceImage)
        imageLayout.addStretch()  # Thêm khoảng trắng ở bên phải của ảnh

        successLayout.addLayout(imageLayout, 0, 0, 1, 2)

        successLayout.addWidget(QLabel("ID Sinh Viên:"), 1, 0)
        successLayout.addWidget(self.studentIdLabel, 1, 1)
        successLayout.addWidget(QLabel("Tên Sinh Viên:"), 2, 0)
        successLayout.addWidget(self.studentNameLabel, 2, 1)
        successLayout.addWidget(QLabel("Điểm danh:"), 3, 0)
        successLayout.addWidget(self.timeLabel, 3, 1)
        successGroup.setLayout(successLayout)

        # Nhóm Thông tin buổi học
        classInfoGroup = QGroupBox("Thông tin buổi học")
        classInfoLayout = QGridLayout()
        classInfoLayout.addWidget(QLabel('Tên môn học:'), 0, 0)
        classInfoLayout.addWidget(self.subjectInfoLabel, 0, 1)
        classInfoLayout.addWidget(QLabel('Giảng viên:'), 1, 0)
        classInfoLayout.addWidget(self.teacherInfoLabel, 1, 1)
        classInfoLayout.addWidget(QLabel('Thời gian:'), 2, 0)
        classInfoLayout.addWidget(self.timeInfoLabel, 2, 1)
        classInfoGroup.setLayout(classInfoLayout)

        rightColumn.addWidget(successGroup)
        rightColumn.addWidget(classInfoGroup)

        # Đặt kích thước cho cột phải lớn hơn
        rightColumn.setStretch(0, 2)
        rightColumn.setStretch(1, 1)

        successGroup.setStyleSheet("""
                            QGroupBox {
                                border: 1px solid gray;
                                border-radius: 5px;
                                font-weight: bold;
                                font-size: 16px;
                                margin-top: 20px;
                                margin-right: 15px;
                                background-color: #FFFFFF;
                                padding: 10px;
                            }
                            QWidget {
                                font-size: 14px;
                            }
                            QGroupBox::title {
                                subcontrol-origin: margin;
                                padding: 0 3px;
                                top: 10px;  /* Điều chỉnh giá trị này để nhích tiêu đề lên */
                                left: 10px;
                            }
                        """)

        classInfoGroup.setStyleSheet("""
                            QGroupBox {
                                border: 1px solid gray;
                                border-radius: 5px;
                                font-weight: bold;
                                font-size: 16px;
                                margin-top: 20px;
                                margin-right: 15px;
                                background-color: #FFFFFF;
                                padding: 10px;
                            }
                            QWidget {
                                font-size: 14px;
                            }
                            QGroupBox::title {
                                subcontrol-origin: margin;
                                padding: 0 3px;
                                top: 10px;  /* Điều chỉnh giá trị này để nhích tiêu đề lên */
                                left: 10px;
                            }
                        """)

        return rightColumn

    def loadSubjects(self):
        self.subjectComboBox.clear()
        self.subjectComboBox.addItem('Chọn môn học', None)
        for subject_id, subject in self.subjects_data.items():
            self.subjectComboBox.addItem(subject.get('name'), subject_id)

    def loadClasses(self):
        self.classComboBox.clear()
        self.classComboBox.addItem('Chọn ca học', None)
        selected_subject = self.subjectComboBox.currentData()
        if selected_subject:
            class_ids = self.subjects_data[selected_subject].get('classIDs', [])
            for class_id in class_ids:
                class_data = self.firebase_service.get_class_by_id(class_id)
                if class_data:
                    self.classComboBox.addItem(class_data.get('name'), class_id)

    def updateClassInfo(self):
        selected_class_id = self.classComboBox.currentData()
        if selected_class_id:
            class_data = self.firebase_service.get_class_by_id(selected_class_id)
            if class_data:
                # Retrieve class details
                teacher_id = class_data.get('teacherID', '')
                start_time = class_data.get('start', '')
                end_time = class_data.get('end', '')

                # Retrieve subject name from the selected subject
                selected_subject_id = self.subjectComboBox.currentData()
                if selected_subject_id:
                    subject_name = self.subjects_data[selected_subject_id].get('name', '')
                    self.subjectInfoLabel.setText(subject_name)

                # Retrieve teacher's name based on teacherID
                if teacher_id:
                    teacher_data = self.firebase_service.get_teacher_by_id(teacher_id)
                    if teacher_data:
                        self.teacherInfoLabel.setText(teacher_data.get('name', ''))

                # Set class time
                self.timeInfoLabel.setText(f'{start_time} - {end_time}')

    def openCamera(self):
        # Kiểm tra nếu môn học và ca học đã được chọn
        if self.subjectComboBox.currentIndex() == 0 or self.classComboBox.currentIndex() == 0:
            self.notificationLabel.setText('Vui lòng chọn Môn học và Ca học trước khi mở Camera!')
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.notificationLabel.setText('Không thể mở camera!')
            return

        self.timer.start(20)  # Cập nhật khung hình mỗi 20ms

    def closeCamera(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.detectionScreen.setPixmap(self.replacement_camera)  # Hiển thị ảnh thay thế khi tắt camera

    def updateFrame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                boxes, landmarks = self.mtcnn_model.detect_faces(frame)
                if boxes is not None and landmarks is not None:
                    faces = self.mtcnn_model.extract_faces(frame, boxes, landmarks)
                    if faces:
                        print(f"Số lượng khuôn mặt phát hiện: {len(faces)}")

                        for face_data in faces:
                            if isinstance(face_data, dict) and 'aligned_face' in face_data:
                                aligned_face = face_data['aligned_face']

                                # Kiểm tra kích thước của aligned_face
                                print(f"Kích thước của aligned_face: {aligned_face.shape}")

                                # Trước khi tính toán embedding
                                if aligned_face is not None and aligned_face.shape[0] > 0 and aligned_face.shape[1] > 0:
                                    face_embedding = self.facenet_model.get_embedding(aligned_face)
                                    print(f"Kích thước của face_embedding: {face_embedding.shape}")
                                    self.recognize_face(face_embedding)
                                else:
                                    print("Khuôn mặt không hợp lệ.")

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame.shape
                    bytesPerLine = ch * w
                    convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
                    scaledImage = convertToQtFormat.scaled(self.detectionScreen.size(), Qt.KeepAspectRatio)
                    self.detectionScreen.setPixmap(QPixmap.fromImage(scaledImage))
        except Exception as e:
            print(f'Lỗi khi xử lý khung hình: {str(e)}')
            self.closeCamera()

    def recognize_face(self, face_embedding):
        if face_embedding.size == 0:
            print("Embedding không hợp lệ.")
            return

        threshold = 0.5  # Bạn có thể cần điều chỉnh ngưỡng này
        max_similarity = -1  # Giá trị cao nhất của độ tương tự
        closest_student = None

        all_embeddings = self.face_embedding_updater.get_all_embeddings()

        """
        Cosine Similarity: Đảm bảo rằng giá trị độ tương tự cosine được tính đúng cách. Độ tương tự 
        cosine thường nằm trong khoảng từ -1 đến 1, với 1 là hoàn toàn giống nhau. Trong trường hợp 
        này, cần sử dụng giá trị dương gần với 1.
        """
        for student_id, embeddings in all_embeddings.items():
            for saved_embedding in embeddings:
                similarity = cosine_similarity([face_embedding.flatten()], [saved_embedding['embedding']])[0][0]
                print(f"Độ tương tự giữa embedding và saved_embedding: {similarity}")

                if similarity > max_similarity:
                    max_similarity = similarity
                    closest_student = student_id

        if max_similarity > threshold:
            if closest_student and closest_student != self.last_recognized_student:
                self.last_recognized_student = closest_student
                self.update_student_info(closest_student)
        else:
            self.notificationLabel.setText('Không nhận diện được khuôn mặt!')

    def update_student_info(self, student_id):
        # Lấy dữ liệu sinh viên từ Firebase
        student_data = self.firebase_service.get_student_by_id(student_id)
        if student_data:
            name = student_data.get('name', 'Không rõ')
            self.studentIdLabel.setText(student_id)
            self.studentNameLabel.setText(name)
            self.timeLabel.setText(datetime.now().strftime('%H:%M:%S'))
            # Phát âm thanh điểm danh thành công
            try:
                self.success_sound.play()
            except Exception as e:
                self.notificationLabel.setText(f'Lỗi khi phát âm thanh: {str(e)}')

    def check_no_face_detected(self):
        # Kiểm tra nếu đã 10 phút không phát hiện khuôn mặt
        if self.last_detection_time.secsTo(QTime.currentTime()) >= 600:
            self.closeCamera()  # Tắt camera

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        self.timer.stop()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AttendanceSystem()
    window.show()
    sys.exit(app.exec_())


