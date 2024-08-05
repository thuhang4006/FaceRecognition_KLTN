import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1

class FaceNetModel:
    def __init__(self, device='cpu'):
        # mô hình InceptionResnetV1 từ FaceNet
        self.device = device
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

    def get_embedding(self, aligned_face):
        if isinstance(aligned_face, np.ndarray) and aligned_face.size > 0:
            # Chuyển đổi ảnh sang tensor
            face_tensor = self.preprocess_image(aligned_face)

            # Tính toán embedding
            with torch.no_grad():
                embedding = self.model(face_tensor)

            return embedding.squeeze().cpu().numpy()
        else:
            return np.array([])

    def preprocess_image(self, aligned_face):
        face_img_resized = cv2.resize(aligned_face, (160, 160))
        face_img_normalized = face_img_resized / 255.0
        face_tensor = torch.tensor(face_img_normalized).permute(2, 0, 1).unsqueeze(0).float().to(self.device)
        return face_tensor
