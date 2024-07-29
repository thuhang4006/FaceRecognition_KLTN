import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# # Đường dẫn đến file JSON đã tải xuống
cred = credentials.Certificate('config/facialrecognition-8ffb2-firebase-adminsdk-aahy3-5e06effe11.json')

# Khởi tạo ứng dụng Firebase
app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'facialrecognition-8ffb2.appspot.com'
})

# Kết nối với Firestore
db = firestore.client()

# Kết nối với Firebase Storage
bucket = storage.bucket()

# Thêm claim cho người dùng
def add_custom_claims(uid, role):
    auth.set_custom_user_claims(uid, {'role': role})
