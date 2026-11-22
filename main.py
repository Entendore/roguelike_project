# main.py
import pygame
import random
import math
import config
import sound_manager
import ai
from entities import Player, Entity, Item, FloatingText
from map_system import DungeonMap
import renderer

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Roguelike: Modular AI Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(config.FONT_MAIN, 14, bold=True)
        self.ui_font = pygame.font.SysFont(config.FONT_MAIN, 12)

        self.sound_manager = sound_manager.SoundManager()
        self.map_system = DungeonMap()

        self.state = "MENU" 
        self.floor = 1
        self.player = None
        self.entities = []
        self.items = []
        self.particles = []
        self.messages = []
        self.screen_shake = 0

    def log(self, msg, type="neutral"):
        color = config.COLOR_TEXT
        if type == "gain": color = config.COLOR_XP
        elif type == "danger": color = (255, 85, 85)
        elif type == "info": color = (100, 200, 255)
        self.messages.insert(0, {"text": msg, "color": color})
        if len(self.messages) > 6: self.messages.pop()

    def generate_level(self):
        rooms = self.map_system.generate()

        if self.player is None:
            self.player = Player(rooms[0].centerx, rooms[0].centery)
        else:
            self.player.x = rooms[0].centerx
            self.player.y = rooms[0].centery # FIXED TYPO

        self.entities = [self.player]
        self.items = []

        for i in range(1, len(rooms)):
            r = rooms[i]
            # Enemies
            for _ in range(random.randint(1, 2)):
                ex, ey = random.randint(r.left+1, r.right-1), random.randint(r.top+1, r.bottom-1)
                roll = random.random()
                is_smart = False
                if roll < 0.6:
                    enemy = Entity(ex, ey, "Slime", config.COLOR_ENEMY_SLIME, 12 + self.floor*2, 3 + self.floor//2, 0)
                elif roll < 0.9:
                    enemy = Entity(ex, ey, "Goblin", config.COLOR_ENEMY_GOBLIN, 18 + self.floor*3, 5 + self.floor//2, 1)
                else:
                    enemy = Entity(ex, ey, "Ogre", config.COLOR_ENEMY_BOSS, 30 + self.floor*5, 8 + self.floor, 2)
                    is_smart = True
                enemy.use_smart_ai = is_smart
                self.entities.append(enemy)

            # Items
            if random.random() < 0.4:
                ix, iy = random.randint(r.left+1, r.right-1), random.randint(r.top+1, r.bottom-1)
                self.items.append(Item(ix, iy, "Health Potion", config.COLOR_POTION, "heal"))

        self.map_system.calculate_fov(self.player.x, self.player.y)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False

            if event.type == pygame.KEYDOWN:
                if self.state in ["MENU", "GAMEOVER"]:
                    if event.key == pygame.K_RETURN:
                        self.floor = 1
                        self.player = None
                        self.particles = []
                        self.messages = []
                        self.state = "PLAYING"
                        self.generate_level()
                        self.log("Depths of Doom: Modular Edition", "info")

                elif self.state == "PLAYING":
                    dx, dy = 0, 0
                    if event.key == pygame.K_w or event.key == pygame.K_UP: dy = -1
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN: dy = 1
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT: dx = -1
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT: dx = 1
                    elif event.key == pygame.K_SPACE: self.end_turn() # Wait
                    elif event.key == pygame.K_e or event.key == pygame.K_RETURN: self.use_potion()

                    if dx != 0 or dy != 0: self.player_turn(dx, dy)
        return True

    def player_turn(self, dx, dy):
        tx, ty = self.player.x + dx, self.player.y + dy

        # Check Attack
        target = next((e for e in self.entities if not e.dead and e.x == tx and e.y == ty), None)
        if target:
            self.attack(self.player, target)
        else:
            if self.player.move(dx, dy, self.map_system):
                self.sound_manager.play('step')

                # Pick up item
                item = next((i for i in self.items if i.x == self.player.x and i.y == self.player.y), None)
                if item and item.type == "heal":
                    self.items.remove(item)
                    self.player.potions += 1
                    self.log("Picked up a Health Potion!", "gain")
                    self.particles.append(FloatingText(self.player.x, self.player.y, "Potion!", config.COLOR_POTION))

                if (tx, ty) == self.map_system.stairs_pos:
                    self.floor += 1
                    self.log(f"Descending to Floor {self.floor}...", "info")
                    self.generate_level()
                    return
            else:
                return # Blocked

        self.end_turn()

    def use_potion(self):
        if self.player.potions > 0:
            heal = 20
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.player.potions -= 1
            self.sound_manager.play('potion')
            self.log(f"Used potion. Healed {heal} HP.", "gain")
            self.particles.append(FloatingText(self.player.x, self.player.y, "+20 HP", config.COLOR_POTION))
            self.end_turn()
        else:
            self.log("No potions left!", "danger")

    def attack(self, attacker, defender):
        dmg = max(1, int(random.random() * attacker.atk) + 1)
        if random.random() < 0.1 + (attacker.level * 0.01):
            dmg = int(dmg * 1.5)
            self.log("Critical Hit!", "info")
        self.log(f"{attacker.name} hits {defender.name} for {dmg}.")
        died = defender.take_damage(dmg, self)
        if died:
            self.log(f"{defender.name} dies!", "gain")
            if attacker == self.player:
                attacker.gain_xp(12 + self.floor * 2, self)

    def end_turn(self):
        for e in self.entities:
            if e == self.player or e.dead: continue

            dist = math.sqrt((e.x - self.player.x)**2 + (e.y - self.player.y)**2)
            if dist < 7 and self.map_system.tiles[e.y][e.x].visible:
                dx, dy = 0, 0
                if e.use_smart_ai:
                    dx, dy = ai.SmartEnemyAI.get_best_move(e, self.player, self.map_system)
                else:
                    if e.x < self.player.x: dx = 1
                    elif e.x > self.player.x: dx = -1
                    if e.y < self.player.y: dy = 1
                    elif e.y > self.player.y: dy = -1

                if (e.x + dx == self.player.x and e.y + dy == self.player.y):
                    self.attack(e, self.player)
                else:
                    if not e.move(dx, dy, self.map_system):
                        if dx != 0 and dy != 0:
                            if e.move(dx, 0, self.map_system): pass
                            elif e.move(0, dy, self.map_system): pass

        self.entities = [e for e in self.entities if not e.dead]
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        self.map_system.calculate_fov(self.player.x, self.player.y)

        if self.screen_shake > 0: self.screen_shake -= 1
        if self.player.dead: self.state = "GAMEOVER"

    def run(self):
        running = True
        while running:
            running = self.handle_input()

            self.screen.fill(config.COLOR_BG)

            if self.state == "PLAYING":
                cam_x = self.player.x * config.TILE_SIZE - config.SCREEN_WIDTH // 2 + config.TILE_SIZE // 2
                cam_y = self.player.y * config.TILE_SIZE - config.SCREEN_HEIGHT // 2 + config.TILE_SIZE // 2

                if self.screen_shake > 0:
                    cam_x += random.randint(-4, 4)
                    cam_y += random.randint(-4, 4)

                renderer.draw_map(self.screen, self.map_system, cam_x, cam_y)
                renderer.draw_stairs(self.screen, self.map_system, cam_x, cam_y)

                # Draw Items
                for item in self.items:
                    if self.map_system.tiles[item.y][item.x].visible:
                        item.draw(self.screen, cam_x, cam_y)

                # Draw Entities
                self.entities.sort(key=lambda e: e.y)
                for e in self.entities:
                    if self.map_system.tiles[e.y][e.x].visible:
                        e.draw(self.screen, cam_x, cam_y)

                for p in self.particles: p.draw(self.screen, self.font, cam_x, cam_y)
                renderer.draw_ui(self.screen, self.player, self.floor, self.messages, self.font, self.ui_font)

            elif self.state == "MENU":
                renderer.draw_centered_text(self.screen, "DEPTHS OF DOOM", -50, config.COLOR_STAIRS, 32)
                renderer.draw_centered_text(self.screen, "Press ENTER to Start", 40, (150, 150, 150), 16)

            elif self.state == "GAMEOVER":
                renderer.draw_centered_text(self.screen, "YOU DIED", -50, (255, 50, 50), 40)
                renderer.draw_centered_text(self.screen, "Press ENTER to Restart", 60, (150, 150, 150), 16)

            pygame.display.flip()
            self.clock.tick(config.FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
