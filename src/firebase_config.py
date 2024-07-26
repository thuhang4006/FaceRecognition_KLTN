import firebase_admin
from firebase_admin import credentials, firestore, storage

# # Đường dẫn đến file JSON đã tải xuống
cred = credentials.Certificate('config/facialrecognition-8ffb2-firebase-adminsdk-aahy3-d0068806dc.json')

# Khởi tạo ứng dụng Firebase
app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'facialrecognition-8ffb2.appspot.com'
})

# Kết nối với Firestore
db = firestore.client()

# Kết nối với Firebase Storage
bucket = storage.bucket()
