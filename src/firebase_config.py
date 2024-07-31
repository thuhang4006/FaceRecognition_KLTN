import re
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# # Đường dẫn đến file JSON đã tải xuống
cred = credentials.Certificate('../config/facialrecognition-8ffb2-firebase-adminsdk-aahy3-5e06effe11.json')

# Khởi tạo ứng dụng Firebase
app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'facialrecognition-8ffb2.appspot.com'
})

# Kết nối với Firestore
db = firestore.client()

# Kết nối với Firebase Storage
bucket = storage.bucket()

def set_custom_user_claims(user_id, role):
    try:
        # Thiết lập custom claims cho người dùng
        auth.set_custom_user_claims(user_id, {'role': role})
        print(f"{user_id}: {role}")
    except Exception as e:
        print(f"Error: {e}")

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_valid_password(password):
    return len(password) >= 6

set_custom_user_claims('lXrsUlboSGby8QNo9zb5dJDqzZG3', 'admin')
set_custom_user_claims('JpMCfN1SyobVsisg1TVGgTyLbyv1', 'teacher')
set_custom_user_claims('KpSqEIZ2XmaUxz0Nfec1ki582ig1', 'teacher')
#
#

