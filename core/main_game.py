import os
import random
import pygame
import sys
from bots import GameMap, create_map_for_player
from game_state import GameState, PLAYER_ID, Country, MINE_BIOMES, BED_BIOMES

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MAP_WIDTH = 10
MAP_HEIGHT = 8
LEFT_PADDING = 50
RIGHT_PADDING = 320
BOTTOM_PADDING = 80

COLORS = {
    None: (80, 80, 80),
    PLAYER_ID: (0, 180, 80),
    "bot_0": (200, 50, 50),
    "bot_1": (50, 50, 200),
    "bot_2": (200, 150, 50),
}

SHOW_COUNTRY_NAMES = True
COUNTRY_NAME_MAX_LENGTH = 12
COUNTRY_TEXT_COLOR = (255, 255, 255)
COUNTRY_TEXT_BACKGROUND = False

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_texture(path, default_size=(32, 32)):
    full = get_resource_path(os.path.join("assets", "textures", path))
    if os.path.exists(full):
        try:
            img = pygame.image.load(full)
            return pygame.transform.scale(img, default_size)
        except pygame.error:
            pass
    return None

def get_territory_at_pos(mouse_x, mouse_y, grid_start_x, grid_start_y, territory_size, map_width, map_height):
    rx = mouse_x - grid_start_x
    ry = mouse_y - grid_start_y
    if rx < 0 or ry < 0:
        return None
    col = rx // territory_size
    row = ry // territory_size
    if col >= map_width or row >= map_height:
        return None
    return row * map_width + col

def run_game():
    global SCREEN_WIDTH, SCREEN_HEIGHT
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    pygame.display.set_caption("Age of Resources")

    font = pygame.font.Font(None, 22)
    font_large = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()

    #текстурыпостроек
    building_textures = {
        "mine": load_texture(os.path.join("textures_of_resources", "mine.png")),
        "bed": load_texture(os.path.join("textures_of_resources", "bed.png")),
        "sawmill": load_texture(os.path.join("textures_of_resources", "sawmill.png")),
        "default": load_texture(os.path.join("textures_of_resources", "wood.png")),
    }
    
    menu_mode = "main"
    selected_save = 0
    saves_list = []
    
    def draw_main_menu():
        screen.fill((20, 20, 30))
        title = font_large.render("Age of Resources", True, (0, 255, 150))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)
        new_game_text = font.render("Новая игра", True, (255, 255, 255))
        new_game_rect = new_game_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(new_game_text, new_game_rect)
        load_game_text = font.render("Загрузить игру", True, (255, 255, 255))
        load_game_rect = load_game_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        screen.blit(load_game_text, load_game_rect)
        quit_text = font.render("Выход", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        screen.blit(quit_text, quit_rect)
        return new_game_rect, load_game_rect, quit_rect
    
    def draw_load_menu():
        screen.fill((20, 20, 30))
        title = font_large.render("Загрузить игру", True, (0, 255, 150))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)
        if not saves_list:
            no_saves_text = font.render("Сохранений не найдено", True, (200, 200, 200))
            no_saves_rect = no_saves_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            screen.blit(no_saves_text, no_saves_rect)
        else:
            for i, save_name in enumerate(saves_list):
                color = (0, 255, 150) if i == selected_save else (255, 255, 255)
                save_text = font.render(save_name, True, color)
                save_rect = save_text.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 40))
                screen.blit(save_text, save_rect)
        back_text = font.render("Назад (ESC)", True, (200, 200, 200))
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)
        return back_rect

    gs = GameState(MAP_WIDTH, MAP_HEIGHT)
    saves_list = gs.get_save_list()
    game_map = create_map_for_player(MAP_WIDTH, MAP_HEIGHT)
    
    running = True
    while running and menu_mode != "game":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if menu_mode == "main":
                    if event.key == pygame.K_UP:
                        menu_mode = "new_game"
                    elif event.key == pygame.K_DOWN:
                        menu_mode = "load_game"
                        selected_save = 0
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif menu_mode == "new_game":
                    if event.key == pygame.K_RETURN:
                        menu_mode = "game"
                        break
                    elif event.key == pygame.K_ESCAPE:
                        menu_mode = "main"
                elif menu_mode == "load_game":
                    if event.key == pygame.K_UP:
                        selected_save = max(0, selected_save - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_save = min(len(saves_list) - 1, selected_save + 1)
                    elif event.key == pygame.K_RETURN and saves_list:
                        gs.init_for_map(game_map)
                        if gs.load_game(saves_list[selected_save]):
                            menu_mode = "game"
                            break
                    elif event.key == pygame.K_ESCAPE:
                        menu_mode = "main"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if menu_mode == "main":
                    new_game_rect, load_game_rect, quit_rect = draw_main_menu()
                    if new_game_rect.collidepoint(mouse_pos):
                        menu_mode = "new_game"
                    elif load_game_rect.collidepoint(mouse_pos):
                        menu_mode = "load_game"
                        selected_save = 0
                    elif quit_rect.collidepoint(mouse_pos):
                        running = False
                elif menu_mode == "new_game":
                    menu_mode = "game"
                    break
                elif menu_mode == "load_game":
                    if saves_list:
                        for i, save_name in enumerate(saves_list):
                            save_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 130 + i * 40, 200, 30)
                            if save_rect.collidepoint(mouse_pos):
                                selected_save = i
                                if event.button == 1:
                                    gs.init_for_map(game_map)
                                    if gs.load_game(saves_list[selected_save]):
                                        menu_mode = "game"
                                        break
        
        if menu_mode == "main":
            draw_main_menu()
        elif menu_mode == "load_game":
            draw_load_menu()
        elif menu_mode == "new_game":
            screen.fill((20, 20, 30))
            start_text = font_large.render("Нажмите ENTER для начала игры", True, (255, 255, 255))
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(start_text, start_rect)
            back_text = font.render("ESC для возврата в меню", True, (200, 200, 200))
            back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            screen.blit(back_text, back_rect)
        
        pygame.display.flip()
    
    if not running or menu_mode != "game":
        pygame.quit()
        return

    gs.init_for_map(game_map)
    
    ai_config = [
        ("bot_0", "Северная Империя", [1, 2]),
        ("bot_1", "Южная Лига", [MAP_WIDTH * (MAP_HEIGHT - 2), MAP_WIDTH * (MAP_HEIGHT - 2) + 1]),
        ("bot_2", "Восточный Союз", [MAP_WIDTH - 2, 2 * MAP_WIDTH - 2]),
    ]
    for cid, name, sectors in ai_config:
        c = Country(cid, name)
        c.balance = 500
        gs.countries[cid] = c
        for sid in sectors:
            if 0 <= sid < MAP_WIDTH * MAP_HEIGHT:
                t = game_map.get_territory(sid)
                if t and (not t.custom_data or t.custom_data.get("biome") != "Море"):
                    c.add_territory(sid, game_map)

    bg_path = get_resource_path(os.path.join("assets", "textures", "maps", "evu.jpg"))
    if os.path.exists(bg_path):
        try:
            bg = pygame.image.load(bg_path)
        except pygame.error:
            bg = None
    else:
        bg = None

    if bg is None:
        bg = pygame.Surface((100, 100))
        bg.fill((30, 50, 70))

    ai_timer_ms = 0
    AI_TURN_INTERVAL_MS = 1000
    input_mode = "start"
    country_name_input = ""
    message_log = []
    selected_sector_id = None
    current_save_slot = 1
    
    def get_next_save_slot():
        nonlocal current_save_slot
        saves_list = gs.get_save_list()
        while f"map_{current_save_slot}" in saves_list:
            current_save_slot += 1
        return f"map_{current_save_slot}"
    
    def add_msg(text):
        message_log.append(text)
        if len(message_log) > 5:
            message_log.pop(0)
    
    def save_current_game():
        save_name = get_next_save_slot()
        if gs.save_game(save_name):
            add_msg(f"Игра сохранена: {save_name}")
        else:
            add_msg("Ошибка сохранения игры")

    menu_mode = None
    menu_index = 0
    menu_sub = "main"
    menu_data = []
    trade_qty = 1
    trade_price = 50
    trade_selected_res = None
    RESOURCES_LIST = ["Coal", "Iron", "Stone", "Wood", "Wheat", "Carrot", "Potato"]
    DEFAULT_PRICES = {"Coal": 50, "Iron": 120, "Stone": 30, "Wood": 40, "Wheat": 25, "Carrot": 20, "Potato": 15}

    def open_trade_menu():
        nonlocal menu_mode, menu_index, menu_sub, menu_data
        bordering = gs.get_player_bordering_countries()
        if not bordering:
            add_msg("Нет соседних стран для торговли.")
            return
        menu_mode = "trade"
        menu_sub = "main"
        menu_index = 0
        menu_data = ["Продать", "Купить", "Выход (Esc)"]

    def open_war_menu():
        nonlocal menu_mode, menu_index, menu_sub, menu_data
        others = [(cid, gs.countries[cid].name) for cid in gs.countries if cid != PLAYER_ID]
        if not others:
            add_msg("Нет других стран.")
            return
        menu_mode = "war"
        menu_sub = "main"
        menu_index = 0
        menu_data = [f"{name} ({'Война' if cid in gs.player_country.wars else 'Мир'})" for cid, name in others]

    def open_alliance_menu():
        nonlocal menu_mode, menu_index, menu_sub, menu_data
        others = [(cid, gs.countries[cid].name) for cid in gs.countries if cid != PLAYER_ID]
        if not others:
            add_msg("Нет других стран.")
            return
        menu_mode = "alliance"
        menu_sub = "main"
        menu_index = 0
        menu_data = [f"{name} ({'Союзник' if cid in gs.player_country.alliances else '-'})" for cid, name in others]

    def handle_trade_confirm():
        nonlocal menu_mode, menu_sub, menu_index, menu_data, trade_qty, trade_price, trade_selected_res
        if menu_sub == "main":
            if menu_index == 0:
                inv = [(r, q) for r, q in gs.player_country.inventory.items() if q > 0]
                if not inv:
                    add_msg("Нет ресурсов для продажи.")
                    menu_mode = None
                    return
                menu_data = [f"{r}: {q} шт" for r, q in inv]
                menu_sub = "sell_res"
                menu_index = 0
            elif menu_index == 1:
                menu_data = RESOURCES_LIST + ["Назад"]
                menu_sub = "buy_res"
                menu_index = 0
            else:
                menu_mode = None
        elif menu_sub == "sell_res":
            inv = [(r, q) for r, q in gs.player_country.inventory.items() if q > 0]
            if inv and menu_index < len(inv):
                res, qty_max = inv[menu_index]
                trade_selected_res = res
                trade_qty = min(5, qty_max)
                trade_price = DEFAULT_PRICES.get(res, 50)
                menu_sub = "sell_qty"
                menu_data = [f"Кол-во: {trade_qty} (←→)", f"Цена: {trade_price}", "Подтвердить (Enter)"]
                menu_index = 0
            else:
                menu_mode = None
        elif menu_sub == "sell_qty":
            if trade_selected_res and gs.player_country.inventory.get(trade_selected_res, 0) >= trade_qty:
                if random.randint(1, 100) <= 60:
                    gs.player_country.balance += trade_price * trade_qty
                    gs.player_country.remove_resource(trade_selected_res, trade_qty)
                    add_msg(f"Продано {trade_qty} {trade_selected_res}. Баланс: {gs.player_country.balance}")
                else:
                    add_msg("Покупатель отказался.")
            menu_mode = None
        elif menu_sub == "buy_res":
            if menu_index < len(RESOURCES_LIST):
                res = RESOURCES_LIST[menu_index]
                trade_selected_res = res
                trade_price = DEFAULT_PRICES.get(res, 50)
                trade_qty = 1
                menu_sub = "buy_qty"
                menu_data = [f"Кол-во: {trade_qty} (←→)", f"Итого: {trade_price}", "Подтвердить (Enter)"]
                menu_index = 0
            else:
                menu_mode = None
        elif menu_sub == "buy_qty":
            if trade_selected_res:
                total = trade_price * trade_qty
                if gs.player_country.balance >= total and random.randint(1, 100) <= 60:
                    gs.player_country.balance -= total
                    gs.player_country.add_resource(trade_selected_res, trade_qty)
                    add_msg(f"Куплено {trade_qty} {trade_selected_res}. Баланс: {gs.player_country.balance}")
                else:
                    add_msg("Недостаточно средств или продавец отказался.")
            menu_mode = None

    def handle_war_confirm():
        nonlocal menu_mode
        others = [(cid, gs.countries[cid].name) for cid in gs.countries if cid != PLAYER_ID]
        if not others or menu_index >= len(others):
            menu_mode = None
            return
        cid, cname = others[menu_index]
        is_war = cid in gs.player_country.wars
        if is_war:
            gs.player_country.wars.remove(cid)
            gs.countries[cid].wars.remove(PLAYER_ID)
            add_msg(f"Мир заключён с {cname}.")
        else:
            gs.player_country.wars.append(cid)
            gs.countries[cid].wars.append(PLAYER_ID)
            add_msg(f"Война объявлена {cname}!")
        menu_mode = None

    def handle_alliance_confirm():
        nonlocal menu_mode
        others = [(cid, gs.countries[cid].name) for cid in gs.countries if cid != PLAYER_ID]
        if not others or menu_index >= len(others):
            menu_mode = None
            return
        cid, cname = others[menu_index]
        is_ally = cid in gs.player_country.alliances
        if is_ally:
            gs.player_country.alliances.remove(cid)
            gs.countries[cid].alliances.remove(PLAYER_ID)
            add_msg(f"Союз с {cname} расторгнут.")
        else:
            gs.player_country.alliances.append(cid)
            gs.countries[cid].alliances.append(PLAYER_ID)
            add_msg(f"Союз с {cname} заключён!")
        menu_mode = None

    def draw_menu_overlay():
        surf = pygame.Surface((500, 420))
        surf.fill((25, 30, 40))
        pygame.draw.rect(surf, (0, 120, 80), (0, 0, 500, 420), 3)
        x, y = 20, 20
        title = {"trade": "Торговля", "war": "Война / Мир", "alliance": "Союзы"}.get(menu_mode, "")
        txt = font_large.render(title, True, (0, 255, 150))
        surf.blit(txt, (x, y))
        y += 40
        hint = "↑↓ выбор  Enter подтвердить  Esc выход"
        if menu_sub in ("sell_qty", "buy_qty"):
            hint += "  ←→ кол-во"
        txt = font.render(hint, True, (150, 150, 150))
        surf.blit(txt, (x, y))
        y += 30
        for i, item in enumerate(menu_data[:15]):
            color = (0, 255, 150) if i == menu_index else (255, 255, 255)
            prefix = ">" if (menu_sub in ("sell_qty", "buy_qty") and i == 2) or (menu_sub not in ("sell_qty", "buy_qty") and i == menu_index) else " "
            txt = font.render(f"{prefix} {item}", True, color)
            surf.blit(txt, (x, y))
            y += 24
        screen.blit(surf, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 210))

    def draw_panel():
        x = SCREEN_WIDTH - RIGHT_PADDING + 10
        y = 20
        pygame.draw.rect(screen, (40, 40, 50), (SCREEN_WIDTH - RIGHT_PADDING, 0, RIGHT_PADDING, SCREEN_HEIGHT))

        if not gs.game_started:
            txt = font.render("Выберите сектор для старта", True, (255, 255, 255))
            screen.blit(txt, (x, y))
            y += 30
            txt = font.render("(клик по карте)", True, (180, 180, 180))
            screen.blit(txt, (x, y))
            return

        txt = font_large.render(f"{gs.player_country.name}", True, (0, 255, 150))
        screen.blit(txt, (x, y))
        y += 28
        txt = font.render(f"Баланс: {gs.player_country.balance}", True, (255, 255, 255))
        screen.blit(txt, (x, y))
        y += 24
        txt = font.render(f"Секторов: {len(gs.player_country.territories)}", True, (255, 255, 255))
        screen.blit(txt, (x, y))
        y += 24
        
        building_count = gs.count_buildings(gs.player_country)
        if building_count > 0:
            income = building_count * 15
            txt = font.render(f"Производств: {building_count} (+{income}₽/ход)", True, (180, 255, 180))
            screen.blit(txt, (x, y))
        else:
            txt = font.render(f"Производств: 0 (-20₽/ход)", True, (255, 180, 180))
            screen.blit(txt, (x, y))
        y += 30

        if selected_sector_id is not None:
            t = game_map.get_territory(selected_sector_id)
            if t:
                txt = font.render(f"Сектор {selected_sector_id}", True, (255, 220, 100))
                screen.blit(txt, (x, y))
                y += 22
                biome = t.custom_data.get("biome", "?") if t.custom_data else "?"
                txt = font.render(f"Биом: {biome}", True, (255, 255, 255))
                screen.blit(txt, (x, y))
                y += 22
                owner = t.owner or "Нейтральный"
                txt = font.render(f"Владелец: {owner}", True, (255, 255, 255))
                screen.blit(txt, (x, y))
                y += 30

                if t.owner == PLAYER_ID:
                    if not t.custom_data or not t.custom_data.get("building"):
                        if biome in MINE_BIOMES:
                            txt = font.render("[M] Шахта", True, (180, 255, 180))
                            screen.blit(txt, (x, y))
                            y += 22
                        if biome in BED_BIOMES:
                            txt = font.render("[G] Грядки", True, (180, 255, 180))
                            screen.blit(txt, (x, y))
                            y += 22
                    else:
                        txt = font.render("[E] Собрать ресурсы", True, (180, 255, 180))
                        screen.blit(txt, (x, y))
                        y += 22
                else:
                    ok, msg = gs.can_capture_sector(selected_sector_id)
                    if ok:
                        txt = font.render("[C] Захватить", True, (255, 200, 100))
                        screen.blit(txt, (x, y))
                        y += 22
                        from game_state import CAPTURE_COST, CAPTURE_RESOURCES
                        req_text = f"Требуется: {CAPTURE_COST}₽"
                        txt = font.render(req_text, True, (200, 200, 200))
                        screen.blit(txt, (x, y))
                        y += 20
                        for res, amount in CAPTURE_RESOURCES.items():
                            req_text = f"  {res}: {amount}"
                            txt = font.render(req_text, True, (180, 180, 180))
                            screen.blit(txt, (x, y))
                            y += 18
                    else:
                        txt = font.render(msg[:35], True, (200, 150, 150))
                        screen.blit(txt, (x, y))
                        y += 22

        y += 20
        txt = font.render("[T] Торговля", True, (200, 200, 255))
        screen.blit(txt, (x, y))
        y += 22
        txt = font.render("[W] Война/Мир", True, (200, 200, 255))
        screen.blit(txt, (x, y))
        y += 22
        txt = font.render("[A] Союзы", True, (200, 200, 255))
        screen.blit(txt, (x, y))
        y += 22
        txt = font.render("[SPACE] Пропустить ход", True, (200, 200, 255))
        screen.blit(txt, (x, y))

        y = SCREEN_HEIGHT - 120
        for m in message_log[-3:]:
            txt = font.render(m[:45], True, (180, 220, 180))
            screen.blit(txt, (x, y))
            y += 20

    def draw_map_section():
        eff_w = SCREEN_WIDTH - LEFT_PADDING - RIGHT_PADDING
        eff_h = SCREEN_HEIGHT - BOTTOM_PADDING
        ts = min(eff_w // MAP_WIDTH, eff_h // MAP_HEIGHT)
        gw = MAP_WIDTH * ts
        gh = MAP_HEIGHT * ts
        gx = LEFT_PADDING + (eff_w - gw) // 2
        gy = (SCREEN_HEIGHT - BOTTOM_PADDING - gh) // 2

        if bg:
            scaled = pygame.transform.scale(bg, (gw, gh))
            screen.blit(scaled, (gx, gy))

        for tid, t in game_map.territories.items():
            rx = gx + t.x * ts
            ry = gy + t.y * ts
            color = COLORS.get(t.owner, (60, 60, 60))
            s = pygame.Surface((ts, ts))
            s.set_alpha(200)
            s.fill(color)
            screen.blit(s, (rx, ry))
            pygame.draw.rect(screen, (255, 255, 255) if selected_sector_id == tid else (150, 150, 150), (rx, ry, ts, ts), 2)

        for tid, t in game_map.territories.items():
            rx = gx + t.x * ts
            ry = gy + t.y * ts
            if t.owner and SHOW_COUNTRY_NAMES:
                owner_name = ""
                if t.owner == PLAYER_ID:
                    owner_name = gs.player_country.name
                elif t.owner in gs.countries:
                    owner_name = gs.countries[t.owner].name
                if owner_name:
                    display_name = owner_name[:COUNTRY_NAME_MAX_LENGTH]
                    font_size = max(10, min(16, ts // 4))
                    adaptive_font = pygame.font.Font(None, font_size)
                    country_text = adaptive_font.render(display_name, True, COUNTRY_TEXT_COLOR)
                    text_rect = country_text.get_rect(center=(rx + ts // 2, ry + ts // 2))
                    screen.blit(country_text, text_rect)

            if t.custom_data and t.custom_data.get("building"):
                b = t.custom_data.get("building")
                buildings = b if isinstance(b, list) else [b]
                icon_size = max(12, ts // 3)
                offset_x = 0
                for btype in buildings[:3]:
                    tex = building_textures.get(btype) or building_textures.get("default")
                    if tex:
                        icon = pygame.transform.scale(tex, (icon_size, icon_size))
                        screen.blit(icon, (rx + 2 + offset_x, ry + 2))
                        offset_x += icon_size + 2

        return gx, gy, ts

    running = True
    grid_gx = grid_gy = territory_size = 0

    while running:
        dt = clock.tick(60)
        ai_timer_ms += dt

        if gs.game_started and ai_timer_ms >= AI_TURN_INTERVAL_MS:
            gs.run_ai_turn()
            ai_timer_ms = 0

        screen.fill((20, 20, 30))
        grid_gx, grid_gy, territory_size = draw_map_section()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tid = get_territory_at_pos(event.pos[0], event.pos[1], grid_gx, grid_gy, territory_size, MAP_WIDTH, MAP_HEIGHT)
                if tid is not None:
                    if not gs.game_started:
                        t = game_map.get_territory(tid)
                        if t and t.custom_data and t.custom_data.get("biome") != "Море" and t.owner is None:
                            input_mode = "name"
                            selected_sector_id = tid
                            country_name_input = ""
                    else:
                        selected_sector_id = tid
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5 and gs.game_started:
                    save_current_game()
                elif input_mode == "name":
                    if event.key == pygame.K_RETURN and country_name_input.strip():
                        gs.create_player_country(country_name_input.strip(), selected_sector_id)
                        add_msg(f"Страна {country_name_input} создана!")
                        input_mode = "game"
                    elif event.key == pygame.K_BACKSPACE:
                        country_name_input = country_name_input[:-1]
                    elif event.unicode.isprintable():
                        country_name_input += event.unicode
                elif input_mode == "game" and gs.game_started:
                    if menu_mode:
                        if event.key == pygame.K_ESCAPE:
                            if menu_sub == "main":
                                menu_mode = None
                            else:
                                menu_sub = "main"
                                menu_index = 0
                                if menu_mode == "trade":
                                    menu_data = ["Продать", "Купить", "Выход (Esc)"]
                        elif event.key == pygame.K_UP:
                            menu_index = max(0, menu_index - 1)
                        elif event.key == pygame.K_DOWN:
                            menu_index = min(len(menu_data) - 1, menu_index + 1)
                        elif event.key == pygame.K_RETURN:
                            if menu_mode == "trade":
                                handle_trade_confirm()
                            elif menu_mode == "war":
                                handle_war_confirm()
                            elif menu_mode == "alliance":
                                handle_alliance_confirm()
                        elif menu_mode == "trade" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            if menu_sub == "sell_qty" and trade_selected_res:
                                qty_max = gs.player_country.inventory.get(trade_selected_res, 0)
                                if event.key == pygame.K_LEFT:
                                    trade_qty = max(1, trade_qty - 1)
                                else:
                                    trade_qty = min(min(99, qty_max), trade_qty + 1)
                                menu_data = [f"Кол-во: {trade_qty} (←→)", f"Цена: {trade_price}", "Подтвердить (Enter)"]
                            elif menu_sub == "buy_qty" and trade_selected_res:
                                if event.key == pygame.K_LEFT:
                                    trade_qty = max(1, trade_qty - 1)
                                else:
                                    max_qty = gs.player_country.balance // max(1, trade_price)
                                    trade_qty = min(99, max_qty, trade_qty + 1)
                                menu_data = [f"Кол-во: {trade_qty} (←→)", f"Итого: {trade_price * trade_qty}", "Подтвердить (Enter)"]
                    else:
                        if event.key == pygame.K_m and selected_sector_id is not None:
                            ok, msg = gs.place_mine(selected_sector_id)
                            add_msg(msg)
                        elif event.key == pygame.K_g and selected_sector_id is not None:
                            ok, msg = gs.place_bed(selected_sector_id)
                            add_msg(msg)
                        elif event.key == pygame.K_l and selected_sector_id is not None:
                            ok, msg = gs.place_sawmill(selected_sector_id)
                            add_msg(msg)
                        elif event.key == pygame.K_e and selected_sector_id is not None:
                            ok, msg = gs.extract_from_sector(selected_sector_id)
                            add_msg(msg)
                        elif event.key == pygame.K_c and selected_sector_id is not None:
                            ok, msg = gs.capture_sector(selected_sector_id)
                            add_msg(msg)
                        elif event.key == pygame.K_t and gs.game_started:
                            open_trade_menu()
                        elif event.key == pygame.K_w and gs.game_started:
                            open_war_menu()
                        elif event.key == pygame.K_a and gs.game_started:
                            open_alliance_menu()
                        elif event.key == pygame.K_SPACE and gs.game_started:
                            income_msg = gs.apply_production_income(gs.player_country)
                            add_msg(income_msg)
                            gs.run_ai_turn()
                            ai_timer_ms = 0
                            add_msg("Ход пропущен")

        draw_panel()

        if menu_mode:
            draw_menu_overlay()

        if input_mode == "name":
            overlay = pygame.Surface((400, 80))
            overlay.fill((30, 40, 50))
            pygame.draw.rect(overlay, (0, 150, 100), (0, 0, 400, 80), 3)
            screen.blit(overlay, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 40))
            txt = font.render("Введите имя страны:", True, (255, 255, 255))
            screen.blit(txt, (SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2 - 35))
            txt = font.render(country_name_input + "_", True, (0, 255, 150))
            screen.blit(txt, (SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2 - 5))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_game()