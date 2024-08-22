import io
import cv2
import numpy as np
import requests
from PIL import Image
from firebase_config import db, bucket


class FirebaseService:
    def __init__(self):
        self.db = db
        self.bucket = bucket
        self.subjects_cache = {}  # Cache cho môn học
        self.teachers_cache = {}  # Cache cho giáo viên
        self.classes_cache = {}  # Cache cho lớp học

    def get_all_subjects(self):
        if not self.subjects_cache:
            subjects_data = {}
            subjects_ref = self.db.collection('Subjects')
            subjects = subjects_ref.stream()
            for subject in subjects:
                subjects_data[subject.id] = subject.to_dict()
            self.subjects_cache = subjects_data
        return self.subjects_cache

    def get_class_by_id(self, class_id):
        if class_id not in self.classes_cache:
            class_ref = self.db.collection('Classes').document(class_id)
            class_data = class_ref.get().to_dict()
            self.classes_cache[class_id] = class_data
        return self.classes_cache.get(class_id)

    def get_all_teachers(self):
        teachers_data = {}
        teachers_ref = self.db.collection('Teachers')
        teachers = teachers_ref.stream()
        for teacher in teachers:
            teachers_data[teacher.get('teacherID')] = teacher.to_dict()
        return teachers_data

    def get_teacher_by_id(self, teacher_id):
        teachers_ref = self.db.collection('Teachers').where('teacherID', '==', teacher_id)
        teacher_docs = teachers_ref.stream()
        for teacher_doc in teacher_docs:
            return teacher_doc.to_dict()
        return None

    def get_all_students_dict(self):
        # Giả sử bạn lấy dữ liệu từ Firestore
        students_ref = self.db.collection('Students')
        docs = students_ref.stream()
        students = []
        for doc in docs:
            student = doc.to_dict()
            students.append(student)
        return students

    def get_student_by_id(self, student_id):
        student_ref = self.db.collection('Students').where('studentID', '==', student_id).limit(1).stream()
        for doc in student_ref:
            return doc.to_dict()
        return None

    def update_class_data(self, class_id, update_data):
        class_ref = self.db.collection('Classes').document(class_id)
        try:
            class_ref.update(update_data)
            print(f"Dữ liệu lớp học {class_id} đã được cập nhật thành công.")
        except Exception as e:
            print(f"Lỗi khi cập nhật dữ liệu lớp học {class_id}: {str(e)}")


