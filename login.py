import pygame as pg
import requests
import threading
from auth_service import VorldAuthService
import argparse
import os
import hashlib
def positive_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("Expected a boolean (true/false)")


def run_login(screen):
    """
    Render a login overlay on the provided Pygame screen and capture
    username and password.

    Returns: (username, password)

    Controls:
    - Type to enter text
    - Tab to switch between Username/Password
    - Backspace to delete
    - Enter to submit (empty username becomes 'Player')
    - Click button to submit
    - Esc or window close to cancel (returns ('Player', ''))
    """
    clock = pg.time.Clock()
    base_font = pg.font.SysFont("Consolas", 28)
    title_font = pg.font.SysFont("Consolas", 36, bold=True)

    # Overlay sizes
    screen_w, screen_h = screen.get_size()
    box_w, box_h = 520, 320
    box_x = (screen_w - box_w) // 2
    box_y = (screen_h - box_h) // 2
    
    user_rect = pg.Rect(box_x + 30, box_y + 110, box_w - 60, 40)
    pass_rect = pg.Rect(box_x + 30, box_y + 170, box_w - 60, 40)

    username = ""
    password = ""
    user_placeholder = "Email"
    pass_placeholder = "Mật khẩu"
    caret_visible = True
    caret_timer = 0
    running = True
    active_field = "user"  # 'user' or 'pass'

    # Button setup
    button_w, button_h = 160, 50
    button_x = box_x + (box_w - button_w) // 2
    button_y = box_y + box_h - button_h - 25
    button_pressed = False
    
    # API request state
    is_loading = False
    api_response = None
    api_error = None

    while running:
        dt = clock.tick(60)
        caret_timer += dt
        if caret_timer >= 500:
            caret_timer = 0
            caret_visible = not caret_visible

        for event in pg.event.get():
            if event.type == pg.QUIT:
                # Treat as cancel
                return ("Player", "")
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return ("Player", "")
                elif event.key == pg.K_RETURN and not is_loading:
                    # Khi nhấn Enter, gọi API xác thực
                    if username.strip() and password:
                        is_loading = True
                        
                        def call_api():
                            nonlocal api_response, api_error, is_loading
                            try:
                                hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                                print(f"Hashed Password: {hashed_password}")
                                base_url = os.getenv("NEXT_PUBLIC_AUTH_SERVER_URL")
                                url = f"{base_url}/auth/login"
                                payload = {
                                    "email": username.strip(),
                                    "password": hashed_password
                                }
                                print(f"Đang gửi request đến: {url}")
                                response = requests.post(url, json=payload, timeout=10, headers={
                                    "x-vorld-app-id": "app_mgw1hs2z_06893227",
                                    "Content-Type": "application/json"
                                })
                                api_response = response.json()
                                print("Response từ API:", api_response)
                            except Exception as e:
                                api_error = str(e)
                                print(f"Lỗi khi gọi API: {e}")
                            finally:
                                is_loading = False
                        
                        api_thread = threading.Thread(target=call_api, daemon=True)
                        api_thread.start()
                elif event.key == pg.K_TAB:
                    active_field = "pass" if active_field == "user" else "user"
                elif event.key == pg.K_BACKSPACE:
                    if active_field == "user":
                        username = username[:-1]
                    else:
                        password = password[:-1]
                else:
                    # Append printable characters only
                    if event.unicode and 32 <= ord(event.unicode) <= 126:
                        if active_field == "user":
                            if len(username) < 50:
                                username += event.unicode
                        else:
                            if len(password) < 50:
                                password += event.unicode
            
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                # Check if clicking on username field
                if user_rect.collidepoint(mouse_pos):
                    active_field = "user"
                # Check if clicking on password field
                elif pass_rect.collidepoint(mouse_pos):
                    active_field = "pass"
                # Check if clicking on button
                button_rect = pg.Rect(button_x, button_y, button_w, button_h)
                if button_rect.collidepoint(mouse_pos):
                    button_pressed = True
                    
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                if button_pressed:
                    mouse_pos = event.pos
                    button_rect = pg.Rect(button_x, button_y, button_w, button_h)
                    if button_rect.collidepoint(mouse_pos) and not is_loading:
                        # Kiểm tra xem đã nhập đủ thông tin chưa
                        if not username.strip() or not password:
                            print("Vui lòng nhập đầy đủ email và mật khẩu!")
                            button_pressed = False
                            continue
                            
                        # In thông tin ra console
                        print("=" * 50)
                        print("THÔNG TIN ĐĂNG NHẬP")
                        print("=" * 50)
                        print(f"Email: {username.strip()}")
                        print(f"Password: {password}")
                        print("=" * 50)
                        
                        # Bắt đầu gọi API trong thread riêng
                        is_loading = True
                        
                        def call_api():
                            nonlocal api_response, api_error, is_loading
                            try:
                                hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                                print(f"Hashed Password: {hashed_password}")
                                base_url = os.getenv("NEXT_PUBLIC_AUTH_SERVER_URL")
                                url = f"{base_url}/auth/login"
                                payload = {
                                    "email": username.strip(),
                                    "password": hashed_password
                                }
                                print(f"Đang gửi request đến: {url}")
                                response = requests.post(url, json=payload, timeout=10, headers={
                                    "x-vorld-app-id": "app_mgw1hs2z_06893227",
                                    "Content-Type": "application/json"
                                })
                                api_response = response.json()
                                print("Response từ API:", api_response)
                            except Exception as e:
                                api_error = str(e)
                                print(f"Lỗi khi gọi API: {e}")
                            finally:
                                is_loading = False
                        
                        # Chạy API call trong thread riêng để không block UI
                        api_thread = threading.Thread(target=call_api, daemon=True)
                        api_thread.start()
                        
                button_pressed = False
        
        # Kiểm tra nếu API đã trả về response
        if api_response is not None:
            if api_response.get('success'):
                print("Đăng nhập thành công!")
                user_data = api_response.get('data', {}).get('user', {})
                player_username = user_data.get('username', username.strip())
                return (player_username, password)
            else:
                error_msg = api_response.get('error', 'Đăng nhập thất bại')
                print(f"Lỗi: {error_msg}")
                api_response = None  # Reset để thử lại
        elif api_error is not None and not is_loading:
            print(f"Đăng nhập thất bại: {api_error}")
            # Reset để có thể thử lại
            api_error = None

        # Dim the background
        dim = pg.Surface((screen_w, screen_h), pg.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (0, 0))

        # Draw dialog box
        pg.draw.rect(screen, pg.Color("#1e1e2e"), (box_x, box_y, box_w, box_h), border_radius=16)
        pg.draw.rect(screen, pg.Color("#6c6c7a"), (box_x, box_y, box_w, box_h), width=2, border_radius=16)

        # Title and instructions
        title_surf = title_font.render("Đăng nhập Vorld", True, pg.Color("#e6e6e6"))
        screen.blit(title_surf, (box_x + 30, box_y + 24))
        
        # Hiển thị lỗi nếu có
        if api_response is not None and not api_response.get('success'):
            error_font = pg.font.SysFont("Consolas", 20)
            error_msg = api_response.get('error', 'Đăng nhập thất bại')
            error_text = error_font.render(f"Lỗi: {error_msg}", True, pg.Color("#ff5555"))
            screen.blit(error_text, (box_x + 30, box_y + 68))
        elif api_error is not None:
            error_font = pg.font.SysFont("Consolas", 20)
            error_text = error_font.render("Lỗi kết nối server!", True, pg.Color("#ff5555"))
            screen.blit(error_text, (box_x + 30, box_y + 68))
        else:
            hint_surf = base_font.render("Nhập email và mật khẩu", True, pg.Color("#c8c8c8"))
            screen.blit(hint_surf, (box_x + 30, box_y + 68))

        # Username field
        pg.draw.rect(screen, pg.Color("#2b2b3b"), user_rect, border_radius=8)
        pg.draw.rect(screen, pg.Color("#9aa0ff") if active_field == "user" else pg.Color("#808091"), 
                     user_rect, width=2, border_radius=8)
        if username:
            user_surf = base_font.render(username, True, pg.Color("#ffffff"))
        else:
            user_surf = base_font.render(user_placeholder, True, pg.Color("#9a9aa5"))
        screen.blit(user_surf, (user_rect.x + 10, user_rect.y + 6))

        # Password field (masked)
        pg.draw.rect(screen, pg.Color("#2b2b3b"), pass_rect, border_radius=8)
        pg.draw.rect(screen, pg.Color("#9aa0ff") if active_field == "pass" else pg.Color("#808091"), 
                     pass_rect, width=2, border_radius=8)
        masked = "*" * len(password) if password else pass_placeholder
        pass_surf = base_font.render(masked, True, pg.Color("#ffffff") if password else pg.Color("#9a9aa5"))
        screen.blit(pass_surf, (pass_rect.x + 10, pass_rect.y + 6))

        # Caret for active field
        if caret_visible:
            if active_field == "user":
                caret_x = user_rect.x + 10 + base_font.size(username)[0]
                caret_y = user_rect.y + 6
                caret_h = base_font.get_height()
                pg.draw.rect(screen, pg.Color("#ffffff"), (caret_x, caret_y, 2, caret_h))
            else:
                caret_x = pass_rect.x + 10 + base_font.size("*" * len(password))[0]
                caret_y = pass_rect.y + 6
                caret_h = base_font.get_height()
                pg.draw.rect(screen, pg.Color("#ffffff"), (caret_x, caret_y, 2, caret_h))

        # Draw confirm button
        mouse_pos = pg.mouse.get_pos()
        button_rect = pg.Rect(button_x, button_y, button_w, button_h)
        hovered = button_rect.collidepoint(mouse_pos) and not is_loading
        pressed = button_pressed and hovered
        
        # Button color based on state
        if is_loading:
            btn_color = pg.Color("#666666")  # Gray when loading
        elif pressed:
            btn_color = pg.Color("#2d4d9e")
        elif hovered:
            btn_color = pg.Color("#4e7cff")
        else:
            btn_color = pg.Color("#2b4db3")
            
        pg.draw.rect(screen, btn_color, button_rect, border_radius=10)
        pg.draw.rect(screen, pg.Color("#9aa0ff"), button_rect, width=2, border_radius=10)
        
        btn_font = pg.font.SysFont("Consolas", 24, bold=True)
        if is_loading:
            # Hiển thị loading animation
            dots = "." * ((pg.time.get_ticks() // 500) % 4)
            btn_text = btn_font.render(f"Đang xử lý{dots}", True, pg.Color("#ffffff"))
        else:
            btn_text = btn_font.render("Xác nhận", True, pg.Color("#ffffff"))
        text_rect = btn_text.get_rect(center=button_rect.center)
        screen.blit(btn_text, text_rect)
        
        # Hiển thị trạng thái loading ở dưới nút
        if is_loading:
            loading_font = pg.font.SysFont("Consolas", 20)
            loading_text = loading_font.render("Đang kết nối đến server...", True, pg.Color("#ffaa00"))
            loading_rect = loading_text.get_rect(center=(box_x + box_w // 2, button_y + button_h + 15))
            screen.blit(loading_text, loading_rect)

        pg.display.flip()

    # Fallback
    return (username.strip() or "Player", password)
