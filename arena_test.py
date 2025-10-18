import os
from arena_game_service import ArenaGameService

# Lấy token từ luồng đăng nhập (auth_service) của bạn
user_token = os.getenv("TEST_ACCESS_TOKEN") or "<put_access_token_here>"

arena = ArenaGameService(user_token=user_token, debug=True)

# Gắn callback nếu cần
arena.on_arena_countdown_started = lambda data: print("[evt] countdown_started:", data)
arena.on_arena_begins = lambda data: print("[evt] arena_begins:", data)

# Khởi tạo game
init = arena.initialize_game("https://your.stream/url")
print("init:", init.success, init.error or init.data)

# Lấy game_id nếu có trong state trả về rồi test get_game_details
state = arena.get_game_state() or {}
game_id = state.get("gameId")
if game_id:
    details = arena.get_game_details(game_id)
    print("details:", details.success, details.error or details.data)

# Ví dụ gọi catalog
catalog = arena.get_items_catalog()
print("catalog:", catalog.success, catalog.error or (catalog.data and list(catalog.data)[:1]))

# Ngắt socket khi xong
arena.disconnect()