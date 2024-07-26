import tempfile
from flask import render_template, Response, request, url_for, redirect, jsonify, session
import cv2
import os
from datetime import datetime
from google.cloud.firestore_v1 import FieldFilter
from src.firebase_config import bucket, db
from datetime import datetime, timedelta

camera = cv2.VideoCapture(0)


def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def configure_routes(app):
    @app.route('/')
    def login():
        return render_template('login.html')

    @app.route('/management')
    def main_page():
        return render_template('main_page.html')

    @app.route('/addDB')
    def addDB():
        return render_template('addFaceDB_page.html')

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/submit', methods=['POST'])
    def submit():
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        class_name = request.form.get('class_name')
        return redirect(url_for('addDB', name=name, student_id=student_id, class_name=class_name))

    @app.route('/capture_image', methods=['GET'])
    def capture_image():
        success, frame = camera.read()
        if success:
            # Lưu ảnh tạm thời
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            cv2.imwrite(temp_file.name, frame)
            return jsonify({'filename': temp_file.name})
        else:
            return jsonify({'error': 'Image capture failed'}), 500

    @app.route('/upload_images', methods=['POST'])
    def upload_images():
        images = request.json.get('images', [])
        student_id = request.json.get('student_id')
        uploaded_files = []

        # Tạo một danh sách lưu trữ tên file và đường dẫn cục bộ
        file_info_list = []

        # Kiểm tra thư mục tồn tại
        blobs = bucket.list_blobs(prefix=f'{student_id}/')
        existing_files = [blob.name for blob in blobs]

        # Xóa các file trong thư mục nếu thư mục tồn tại
        if existing_files:
            bucket.delete_blobs(existing_files)
            # Nếu đã có ảnh thì lưu ngày cập nhật
            update_created_time = False
        else:
            # Nếu chưa có ảnh thì lưu ngày tạo
            update_created_time = True

        # Tải lên các ảnh mới
        for image in images:
            file_path = image['file_path']
            file_name = os.path.basename(file_path)
            blob = bucket.blob(f'{student_id}/{file_name}')
            blob.upload_from_filename(file_path)
            uploaded_files.append(file_name)

            # Xóa file tạm sau khi tải lên
            if os.path.exists(file_path):
                os.remove(file_path)

            # Thu thập thông tin file để cập nhật vào Firestore
            file_info_list.append({
                'fileName': f'{student_id}_{file_name}',
                'blob': blob
            })

        # Cập nhật Firestore với các URL ảnh
        # Tạo một dictionary để lưu trữ facesData mới
        new_faces_data = []

        # Lấy danh sách các documents có cùng studentID
        doc_ref = db.collection('Students').where('studentID', '==', student_id).stream()
        for doc in doc_ref:
            if doc.exists:
                doc_id = doc.id

                # Xây dựng danh sách facesData mới từ file_info_list
                for file_info in file_info_list:
                    blob = file_info['blob']
                    file_name = file_info['fileName']

                    # Tạo URL công khai cho blob
                    image_url = blob.generate_signed_url(expiration=timedelta(days=365), method='GET')

                    timestamp = datetime.utcnow()  # lấy thời gian hiện tại dạng UTC

                    # Thay thế phần xử lý fileName và imageUrl
                    new_faces_data.append({
                        'fileName': file_name,
                        'imageUrl': image_url
                    })

                # Cập nhật hoặc thêm trường ngày tạo/ngày cập nhật vào Firestore
                if update_created_time:
                    db.collection('Students').document(doc_id).update({
                        'facesData': new_faces_data,
                        'createdTime': timestamp
                    })
                else:
                    db.collection('Students').document(doc_id).update({
                        'facesData': new_faces_data,
                        'updatedTime': timestamp
                    })

                print(f'Đã upload thành công cho sinh viên với MSSV: {student_id}, document ID: {doc_id}')
                break

        return jsonify({'uploaded_files': uploaded_files})
