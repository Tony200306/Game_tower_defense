import os
from auth_service import VorldAuthService

# Đọc email/password từ ENV nếu có, nếu không sẽ dùng placeholder và yêu cầu chỉnh lại hoặc nhập
email: str = os.getenv("TEST_EMAIL") or ""
password: str = os.getenv("TEST_PASSWORD") or ""

service = VorldAuthService(debug=True)  # tự đọc .env (base_url, app_id)
print("Base URL:", service.base_url)
print("App ID  :", service.app_id or "(empty)")

# Nếu ENV không có, yêu cầu nhập để đảm bảo kiểu str
if not email:
	email = input("Nhập email: ").strip()
if not password:
	password = input("Nhập mật khẩu: ").strip()

def attempt_login(hash_password: bool):
	# tạo instance theo chế độ hash/plain mong muốn
	svc = VorldAuthService(debug=True, hash_password=hash_password)
	return svc, svc.login_with_email(email, password)

# Thử đăng nhập với SHA-256 trước
svc, login = attempt_login(hash_password=True)
if not login.success and "status 401" in str(login.error or ""):
	print("Login bằng SHA-256 bị 401 → thử lại với mật khẩu plaintext...")
	svc, login = attempt_login(hash_password=False)

if not login.success:
	print("Login failed:", login.error)
	print("Gợi ý: đặt TEST_EMAIL/TEST_PASSWORD hoặc sửa trực tiếp trong file này. Kiểm tra định dạng email và mật khẩu đúng.")
else:
	print("Login OK:", login.data)
	# Kiểm tra yêu cầu OTP
	requires_otp = False
	data = login.data or {}
	if isinstance(data, dict):
		requires_otp = bool(data.get("requiresOTP") or data.get("requireOtp") or data.get("otpRequired"))

	if requires_otp:
		code = input("Nhập mã OTP (6 số): ").strip()
		verify = svc.verify_otp(email, code)
		if not verify.success:
			print("OTP verify failed:", verify.error)
		else:
			print("OTP verify OK:", verify.data)

	# Sau khi đăng nhập/OTP thành công → gọi profile
	profile = svc.get_profile()
	if profile.success:
		print("Profile:", profile.data)
	else:
		print("Profile error:", profile.error)
from auth_service import VorldAuthService
svc = VorldAuthService(debug=True, hash_password=False)  # thử plaintext trước
# # ví dụ 1: username/password
# print(svc.login_with_credentials({"username": "user@example.com", "password": "your_password"}))
# # ví dụ 2: identifier/password
# print(svc.login_with_credentials({"identifier": "user@example.com", "password": "your_password"}))