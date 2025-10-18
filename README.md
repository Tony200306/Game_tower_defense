# Game_tower_defense

## Python Auth Service (Vorld)

Đã thêm phiên bản Python cho dịch vụ xác thực tương ứng với `authService.ts`.

- File: `auth_service.py`
- Phụ thuộc: `requests`, `python-dotenv` (đã có trong `requirements.txt`)

### Biến môi trường / .env

Thư viện sẽ tự động đọc file `.env` ở thư mục gốc project (nếu có) nhờ `python-dotenv`.

Ví dụ nội dung `.env`:

```
NEXT_PUBLIC_VORLD_APP_ID=app_mgvu1iso_3ec1e498
NEXT_PUBLIC_AUTH_SERVER_URL=https://vorld-auth.onrender.com/api
NODE_ENV=development
```

Hoặc thiết lập các biến môi trường trực tiếp (PowerShell trên Windows):

```
$Env:NEXT_PUBLIC_AUTH_SERVER_URL = "http://localhost:3001/api"
$Env:NEXT_PUBLIC_VORLD_APP_ID = "<your-app-id>"
```

Giá trị mặc định nếu không đặt:

- `NEXT_PUBLIC_AUTH_SERVER_URL`: `http://localhost:3001/api`
- `NEXT_PUBLIC_VORLD_APP_ID`: chuỗi rỗng

### Cài đặt phụ thuộc

```
pip install -r requirements.txt
```

### Cách dùng nhanh

```python
from auth_service import VorldAuthService

service = VorldAuthService()  # tự đọc biến môi trường nếu có

# Đăng nhập email/password (mật khẩu sẽ được hash SHA-256 trước khi gửi)
result = service.login_with_email("user@example.com", "your_password")
if result.success:
	print("Login OK:", result.data)
else:
	print("Login failed:", result.error)

# Lấy hồ sơ người dùng (sử dụng cookie trong Session)
profile = service.get_profile()
if profile.success:
	print("Profile:", profile.data)
else:
	print("Profile error:", profile.error)
```

Lưu ý: Backend cần hỗ trợ cookie-based session (tương đương `withCredentials: true` ở frontend) và các endpoint:

- `POST /auth/login` (body: `{ email, password }`, trong đó `password` đã được SHA-256)
- `GET /user/profile`

