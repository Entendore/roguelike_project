# renderer.py
import pygame
import config

def draw_map(surface, game_map, camera_x, camera_y):
    for y in range(game_map.height):
        for x in range(game_map.width):
            tile = game_map.tiles[y][x]
            rect = (x * config.TILE_SIZE - camera_x, y * config.TILE_SIZE - camera_y, config.TILE_SIZE, config.TILE_SIZE)

            # Culling
            if not (-config.TILE_SIZE < rect[0] < config.SCREEN_WIDTH and -config.TILE_SIZE < rect[1] < config.SCREEN_HEIGHT):
                continue

            if tile.visible:
                color = config.COLOR_WALL if tile.blocked else config.COLOR_FLOOR
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (40,40,40), rect, 1)
            elif tile.explored:
                color = config.COLOR_WALL_DARK if tile.blocked else config.COLOR_FLOOR_DARK
                pygame.draw.rect(surface, color, rect)
                s = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
                s.set_alpha(100)
                s.fill((0,0,0))
                surface.blit(s, (rect[0], rect[1]))

def draw_stairs(surface, game_map, camera_x, camera_y):
    sx, sy = game_map.stairs_pos
    if game_map.tiles[sy][sx].visible:
        s_rect = (sx * config.TILE_SIZE - camera_x, sy * config.TILE_SIZE - camera_y, config.TILE_SIZE, config.TILE_SIZE)
        pygame.draw.polygon(surface, config.COLOR_STAIRS, [
            (s_rect[0] + 16, s_rect[1] + 4),
            (s_rect[0] + 4, s_rect[1] + 28),
            (s_rect[0] + 28, s_rect[1] + 28)
        ])

def draw_ui(surface, player, floor, messages, font, ui_font):
    # Background
    s = pygame.Surface((config.SCREEN_WIDTH, 70))
    s.set_alpha(220)
    s.fill((30, 30, 35))
    surface.blit(s, (0,0))

    # Stats
    stats = [f"LVL: {player.level}", f"FLR: {floor}", f"ATK: {player.atk}", f"DEF: {player.defense}"]
    for i, text in enumerate(stats):
        surf = ui_font.render(text, True, config.COLOR_TEXT)
        surface.blit(surf, (10 + i*80, 10))

    hp_surf = ui_font.render(f"HP: {player.hp}/{player.max_hp}", True, config.COLOR_HP)
    surface.blit(hp_surf, (10, 30))

    pot_surf = ui_font.render(f"Potions: {player.potions} [E]", True, config.COLOR_POTION)
    surface.blit(pot_surf, (config.SCREEN_WIDTH - 150, 10))

    # Bars
    bar_w, bar_h = 150, 10
    bar_x = config.SCREEN_WIDTH // 2 - bar_w // 2
    pygame.draw.rect(surface, (50, 50, 50), (bar_x, 30, bar_w, bar_h))
    hp_pct = max(0, player.hp / player.max_hp)
    pygame.draw.rect(surface, config.COLOR_HP, (bar_x, 30, int(bar_w * hp_pct), bar_h))

    pygame.draw.rect(surface, (50, 50, 50), (bar_x, 45, bar_w, bar_h))
    xp_pct = min(1, player.xp / player.xp_to_next)
    pygame.draw.rect(surface, config.COLOR_XP, (bar_x, 45, int(bar_w * xp_pct), bar_h))

    # Log
    log_bg = pygame.Surface((config.SCREEN_WIDTH, 100))
    log_bg.set_alpha(180)
    log_bg.fill((0,0,0))
    surface.blit(log_bg, (0, config.SCREEN_HEIGHT - 100))
    y_off = config.SCREEN_HEIGHT - 90
    for msg in messages:
        txt = ui_font.render(f"> {msg['text']}", True, msg['color'])
        surface.blit(txt, (10, y_off))
        y_off += 16

def draw_centered_text(surface, text, y_offset, color, size):
    f = pygame.font.SysFont(config.FONT_MAIN, size, bold=True)
    surf = f.render(text, True, color)
    rect = surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + y_offset))
    surface.blit(surf, rect)
