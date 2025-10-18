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