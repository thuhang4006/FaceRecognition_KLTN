import cv2
import numpy as np
from facenet_pytorch import MTCNN

class MTCNNModel:
    def __init__(self, device='cpu'):
        self.device = device
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

    def detect_faces(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes, probs, landmarks = self.mtcnn.detect(image_rgb, landmarks=True)
        return boxes, landmarks

    def extract_faces(self, image, boxes, landmarks):
        aligned_faces = []
        if boxes is not None and landmarks is not None:
            for box, lm in zip(boxes, landmarks):
                if box is not None and lm is not None:
                    # Align face
                    aligned_face = self.align_face(image, box, lm)
                    if aligned_face is not None:
                        aligned_faces.append({
                            'box': box,
                            'aligned_face': aligned_face
                        })

        return aligned_faces

    # Hàm để căn chỉnh khuôn mặt bằng điểm mốc
    def align_face(self, img_rgb, box, landmarks):
        if landmarks is None or len(landmarks) == 0:
            raise ValueError("Không có điểm mốc nào được phát hiện.")

        # Các điểm mốc có hình dạng đúng
        if len(landmarks.shape) == 2 and landmarks.shape[0] >= 5:
            # Chọn điểm mốc của khuôn mặt đầu tiên
            landmarks = landmarks.astype(int)

            # Điểm mốc của hai mắt
            left_eye = landmarks[0]
            right_eye = landmarks[1]

            # Tính toán góc xoay để căn chỉnh hai mắt
            delta_x = right_eye[0] - left_eye[0]
            delta_y = right_eye[1] - left_eye[1]
            angle = np.arctan2(delta_y, delta_x) * 180 / np.pi

            # Tính toán trung tâm của khuôn mặt
            x1, y1, x2, y2 = [int(coord) for coord in box]
            center = (int((x1 + x2) / 2), int((y1 + y2) / 2))

            # Tạo ma trận xoay và xoay ảnh
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1)
            aligned_face = cv2.warpAffine(img_rgb, rotation_matrix, (img_rgb.shape[1], img_rgb.shape[0]),
                                          flags=cv2.INTER_CUBIC)

            # Cắt khuôn mặt từ ảnh căn chỉnh
            x1, y1, x2, y2 = [int(coord) for coord in box]
            aligned_face = aligned_face[y1:y2, x1:x2]

            return aligned_face
        else:
            raise ValueError("Hình dạng của điểm mốc không như mong đợi.")


