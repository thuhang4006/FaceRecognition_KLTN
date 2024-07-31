from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox, QSizePolicy, QSpacerItem, QGridLayout
import cv2
import sys
import pygame
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime, timedelta
from models.mtcnn_model import MTCNNModel
from models.facenet_model import FaceNetModel
from firebase_service import FirebaseService
from PyQt5.QtGui import QFont, QImage, QPixmap
from sklearn.metrics.pairwise import cosine_similarity
from face_embedding_updater import FaceEmbeddingUpdater


class AttendanceSystem(QWidget):
    def __init__(self):
        super().__init__()
        self.firebase_service = FirebaseService()

        # Cập nhật embeddings khi ứng dụng khởi động
        self.face_embedding_updater = FaceEmbeddingUpdater()
        self.face_embedding_updater.update_face_embeddings()

        # models
        self.mtcnn_model = MTCNNModel()
        self.facenet_model = FaceNetModel()

        # ảnh thay thế
        self.replacement_camera = QPixmap('../images/face_recognition.jpg')
        self.replacement_face = QPixmap('../images/face.png')

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
        self.success_sound = pygame.mixer.Sound('../sounds/checked.mp3')

        # Biến lưu thông tin nhận diện
        self.recognized_student = None

        # Khởi tạo QTimer cho việc trì hoãn
        self.delay_timer = QTimer()
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.delayed_update_student_info)

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
        self.notificationLabel = QLabel('<font size="5">Vui lòng đểm danh trước khi vào lớp!', self)
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
                image: url(../images/arrow.png);
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

    def openCamera(self):
        # Kiểm tra nếu môn học và ca học đã được chọn
        if self.subjectComboBox.currentIndex() == 0 or self.classComboBox.currentIndex() == 0:
            self.notificationLabel.setText('<font color="red" size="5">Vui lòng chọn Môn học và Ca học trước khi mở Camera!')
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.notificationLabel.setText('Không thể mở camera!')
            return

        self.timer.start(20)
        self.notificationLabel.setText('<font size="5">Vui lòng điểm danh trước khi vào lớp!')

    def closeCamera(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.detectionScreen.setPixmap(self.replacement_camera)  # Hiển thị ảnh thay thế khi tắt camera

    def updateFrame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                print('Không thể đọc khung hình từ camera.')
                return

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

            # Cập nhật khung hình cho GUI
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
            scaledImage = convertToQtFormat.scaled(self.detectionScreen.size(), Qt.KeepAspectRatio)
            self.detectionScreen.setPixmap(QPixmap.fromImage(scaledImage))

        except Exception as e:
            print(f'Lỗi khi xử lý khung hình: {str(e)}')
            self.closeCamera()

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
                teacher_id = class_data.get('teacherID', '')
                start_time = class_data.get('start', '')
                end_time = class_data.get('end', '')

                selected_subject_id = self.subjectComboBox.currentData()
                if selected_subject_id:
                    subject_name = self.subjects_data[selected_subject_id].get('name', '')
                    self.subjectInfoLabel.setText(subject_name)

                # Lấy tên GV bằng teacherID
                if teacher_id:
                    teacher_data = self.firebase_service.get_teacher_by_id(teacher_id)
                    if teacher_data:
                        self.teacherInfoLabel.setText(teacher_data.get('name', ''))

                if start_time and end_time:
                    start_time_utc7 = start_time + timedelta(hours=7)
                    end_time_utc7 = end_time + timedelta(hours=7)

                    start_time_str = start_time_utc7.strftime('%H:%M:%S')
                    end_time_str = end_time_utc7.strftime('%H:%M:%S')
                    self.timeInfoLabel.setText(f'{start_time_str} - {end_time_str}')

    def recognize_face(self, face_embedding):
        if face_embedding.size == 0:
            print("Embedding không hợp lệ.")
            return

        threshold = 0.8
        max_similarity = -1
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
            if closest_student and closest_student != self.recognized_student:
                # Delay sau 2s mới điểm danh thành công 2 giây
                self.delay_timer.start(1500)  # 2000 ms = 2 giây
                self.recognized_student = closest_student
        else:
            self.notificationLabel.setText('<font size="5">Vui lòng điểm danh trước khi vào lớp!')

    def delayed_update_student_info(self):
        student_id = getattr(self, 'recognized_student', None)
        if student_id:
            self.update_student_info(student_id)

    def update_student_info(self, student_id):
        selected_class_id = self.classComboBox.currentData()
        class_data = self.firebase_service.get_class_by_id(selected_class_id)

        student_ids_in_class = class_data.get('studentIDs', [])
        if student_id not in student_ids_in_class:
            self.notificationLabel.setText('<font color="red" size="5">Không phải sinh viên trong lớp!')
            self.studentIdLabel.clear()
            self.studentNameLabel.clear()
            self.timeLabel.clear()
            return

        student_data = self.firebase_service.get_student_by_id(student_id)
        if not student_data:
            self.notificationLabel.setText('<font color="red" size="5">Không tìm thấy thông tin sinh viên.')
            return

        name = student_data.get('name')
        self.studentIdLabel.setText(student_id)
        self.studentNameLabel.setText(name)
        self.timeLabel.setText(datetime.now().strftime('%H:%M:%S'))

        # Cập nhật thông tin điểm danh lên Firebase
        current_datetime = datetime.now()  # Sử dụng datetime thay vì date
        buoi_array = class_data.get('buoi', [])
        date_today = current_datetime.date()

        # Tìm kiếm ngày hiện tại trong buoi_array
        buoi_today = next((buoi for buoi in buoi_array if buoi.get('ngay').date() == date_today), None)

        if buoi_today:
            # Nếu ngày hiện tại đã tồn tại, kiểm tra tình trạng điểm danh
            students_array = buoi_today.get('students', [])
            student_exists = next((student for student in students_array if student['studentID'] == student_id), None)

            if not student_exists:
                # Hiển thị thông tin sinh viên
                self.studentIdLabel.setText(student_id)
                self.studentNameLabel.setText(name)
                self.timeLabel.setText(datetime.now().strftime('%H:%M:%S'))
                # Phát âm thanh
                self.success_sound.play()

                # cập nhật thông tin điểm danh ln firebase
                students_array.append({
                    'checkinStatus': True,
                    'checkoutStatus': True,
                    'studentID': student_id,
                    'name': name
                })
                buoi_today['students'] = students_array

                # Cập nhật dữ liệu lớp học
                self.firebase_service.update_class_data(selected_class_id, {'buoi': buoi_array})
            else:
                # Sinh viên đã điểm danh
                self.notificationLabel.setText('<font color="green" size="5">Sinh viên đã điểm danh hôm nay!')

        # Nếu ngày hiện tại chưa tồn tại
        else:
            # Hiện thông tin sinh viên
            self.studentIdLabel.setText(student_id)
            self.studentNameLabel.setText(name)
            self.timeLabel.setText(datetime.now().strftime('%H:%M:%S'))
            # Phát âm thanh
            self.success_sound.play()

            # Thêm mới và cập nhật thông tin điểm danh
            buoi_array.append({
                'ngay': current_datetime,  # Sử dụng datetime
                'students': [{
                    'checkinStatus': True,
                    'checkoutStatus': True,
                    'studentID': student_id,
                    'name': name
                }]
            })
            # Cập nhật dữ liệu lớp học
            self.firebase_service.update_class_data(selected_class_id, {'buoi': buoi_array})


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


