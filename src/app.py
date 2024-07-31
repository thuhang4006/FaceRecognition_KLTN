from flask import Flask
from src.management_ui.routes import configure_routes
import os

# Tạo một chuỗi ngẫu nhiên để làm secret key
secret_key = os.urandom(24)
print(secret_key)

app = Flask(__name__, template_folder='management_ui/templates', static_folder='management_ui/static')
app.secret_key = secret_key

configure_routes(app)

if __name__ == '__main__':
    app.run(debug=False)
