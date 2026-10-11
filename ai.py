# ai.py
import math
import config

class SmartEnemyAI:
    """
    Uses a Utility-based approach similar to MDP.
    Calculates the score of every possible move (N, S, E, W, Wait).
    """
    @staticmethod
    def get_best_move(entity, player, game_map):
        actions = [(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)]
        best_action = None
        best_score = -float('inf')

        current_dist = math.sqrt((entity.x - player.x)**2 + (entity.y - player.y)**2)
        is_desperate = entity.hp < (entity.max_hp * 0.3)

        for dx, dy in actions:
            tx, ty = entity.x + dx, entity.y + dy

            # Validity Check
            if not (0 <= tx < config.MAP_WIDTH and 0 <= ty < config.MAP_HEIGHT): continue
            if game_map.tiles[ty][tx].blocked: continue

            score = 0
            new_dist = math.sqrt((tx - player.x)**2 + (ty - player.y)**2)

            # Desire: Minimize distance to player
            if new_dist < current_dist: score += 20
            elif new_dist > current_dist: score -= 15

            # Opportunity: Adjacent to player?
            if abs(tx - player.x) + abs(ty - player.y) == 1:
                score += 50
            elif dx == 0 and dy == 0: # Wait
                if current_dist <= 1.5: score += 40
                else: score -= 5

            # Danger: Avoid corners (Penalty for trapped state)
            neighbors = 0
            for nx, ny in [(0,1), (0,-1), (1,0), (-1,0)]:
                if 0 <= tx+nx < config.MAP_WIDTH and 0 <= ty+ny < config.MAP_HEIGHT:
                    if game_map.tiles[ty+ny][tx+nx].blocked: neighbors += 1
            if neighbors >= 3: score -= 20

            # Heuristic: Fear of death
            if is_desperate:
                if new_dist < current_dist: score -= 30
                if dx == 0 and dy == 0: score += 10

            if score > best_score:
                best_score = score
                best_action = (dx, dy)

        return best_action if best_action else (0, 0)
