import math
import json
import random
from pathlib import Path

import pygame

from collision import Collide
from shape import Polygon


pygame.init()
SCREEN = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Mini Golf | Colisao por poligonos")
CLOCK = pygame.time.Clock()
FONT = pygame.font.Font(None, 26)
SMALL_FONT = pygame.font.Font(None, 20)

COURSE = pygame.Rect(28, 72, 744, 500)
BALL_RADIUS = 10
MAX_PULL = 115
MAX_SPEED = 620
FRICTION = 0.986
STOP_SPEED = 12
HOLE_CENTER = (700, 125)
START_POSITION = (95.0, 510.0)
TOTAL_HOLES = 10
MAX_RECORDS = 10
RECORDS_FILE = Path(__file__).with_name("best_scores.json")

OBSTACLE_POINTS = [
    [(185, 430), (340, 405), (365, 425), (355, 450), (205, 475)],
    [(430, 345), (465, 305), (500, 340), (485, 390), (450, 400)],
    [(545, 205), (580, 190), (620, 220), (600, 250), (560, 245)],
    [(300, 250), (365, 225), (400, 245), (390, 270), (330, 285)],
    [(260, 145), (286, 128), (315, 150), (308, 174), (276, 177)],
    [(465, 155), (495, 140), (520, 162), (510, 190), (478, 187)],
    [(650, 260), (681, 245), (704, 270), (691, 298), (660, 291)],
    [(365, 325), (395, 309), (419, 335), (405, 362), (374, 355)],
    [(290, 510), (320, 490), (346, 512), (331, 540), (300, 536)],
    [(664, 465), (693, 447), (719, 470), (704, 500), (672, 493)],
    [(385, 190), (410, 174), (438, 194), (427, 220), (397, 216)],
    [(635, 360), (663, 342), (690, 366), (676, 393), (645, 387)],
]
previous_obstacle_layout = None


def generate_obstacles():
    global previous_obstacle_layout
    while True:
        layout = tuple(sorted(random.sample(range(len(OBSTACLE_POINTS)), 4)))
        if layout != previous_obstacle_layout:
            previous_obstacle_layout = layout
            return [Polygon(OBSTACLE_POINTS[index]) for index in layout]


WALLS = generate_obstacles()


def generate_boost_zone():
    center_x = random.randint(125, 190)
    center_y = random.randint(235, 335)
    return Polygon([
        (center_x - 65, center_y - 15),
        (center_x - 25, center_y - 45),
        (center_x + 48, center_y - 28),
        (center_x + 65, center_y + 5),
        (center_x + 25, center_y + 40),
        (center_x - 55, center_y + 32),
    ])


def load_records():
    if not RECORDS_FILE.exists():
        RECORDS_FILE.write_text("[]\n", encoding="utf-8")
    try:
        data = json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
        records = [
            {"name": str(item["name"])[:16], "strokes": int(item["strokes"])}
            for item in data
            if isinstance(item, dict) and int(item["strokes"]) >= 0
        ]
    except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
        return []
    return sorted(records, key=lambda item: item["strokes"])[:MAX_RECORDS]


def qualifies_for_record(total_strokes, records):
    return len(records) < MAX_RECORDS or total_strokes < records[-1]["strokes"]


def save_record(name, total_strokes, records):
    updated_records = records + [{"name": name[:16], "strokes": total_strokes}]
    updated_records.sort(key=lambda item: item["strokes"])
    updated_records = updated_records[:MAX_RECORDS]
    RECORDS_FILE.write_text(
        json.dumps(updated_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return updated_records


BOOST_ZONE = generate_boost_zone()
HOLE = Polygon([
    (HOLE_CENTER[0] - 15 * math.cos(i * math.tau / 16),
     HOLE_CENTER[1] - 11 * math.sin(i * math.tau / 16))
    for i in range(16)
])


def make_ball_polygon(position):
    x, y = position
    return Polygon([
        (x + BALL_RADIUS * math.cos(i * math.tau / 16),
         y + BALL_RADIUS * math.sin(i * math.tau / 16))
        for i in range(16)
    ])


def draw_polygon(surface, polygon, fill, outline=None, width=2):
    pygame.draw.polygon(surface, fill, polygon.points)
    if outline:
        pygame.draw.polygon(surface, outline, polygon.points, width)


def nearest_edge(position, polygon):
    px, py = position
    best_distance = float("inf")
    best_point = None
    best_normal = None
    points = polygon.points
    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)

    for index, start in enumerate(points):
        end = points[(index + 1) % len(points)]
        edge_x = end[0] - start[0]
        edge_y = end[1] - start[1]
        length_squared = edge_x * edge_x + edge_y * edge_y
        if length_squared == 0:
            continue

        amount = max(0, min(1, ((px - start[0]) * edge_x +
                                (py - start[1]) * edge_y) / length_squared))
        point = (start[0] + amount * edge_x, start[1] + amount * edge_y)
        distance = math.hypot(px - point[0], py - point[1])
        if distance < best_distance:
            normal_x = edge_y
            normal_y = -edge_x
            if normal_x * (point[0] - center_x) + normal_y * (point[1] - center_y) < 0:
                normal_x = -normal_x
                normal_y = -normal_y
            normal_length = math.hypot(normal_x, normal_y)
            best_distance = distance
            best_point = point
            best_normal = (normal_x / normal_length, normal_y / normal_length)

    return best_distance, best_point, best_normal


ball_position = START_POSITION
velocity = [0.0, 0.0]
hole_number = 1
hole_strokes = 0
total_strokes = 0
records = load_records()
aiming = False
sunk = False
game_over = False
player_name = ""
record_eligible = False
record_saved = False
active_effects = set()
running = True

while running:
    dt = min(CLOCK.tick(60) / 1000, 0.025)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                ball_position = START_POSITION
                velocity = [0.0, 0.0]
                hole_number = 1
                hole_strokes = 0
                total_strokes = 0
                aiming = False
                sunk = False
                game_over = False
                player_name = ""
                record_eligible = False
                record_saved = False
                active_effects.clear()
                WALLS = generate_obstacles()
                BOOST_ZONE = generate_boost_zone()
            elif game_over and record_eligible and not record_saved:
                if event.key == pygame.K_RETURN and player_name.strip():
                    records = save_record(player_name.strip(), total_strokes, records)
                    record_saved = True
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode and event.unicode.isprintable() and len(player_name) < 16:
                    player_name += event.unicode
            elif sunk and not game_over and event.key == pygame.K_RETURN:
                hole_number += 1
                hole_strokes = 0
                ball_position = START_POSITION
                velocity = [0.0, 0.0]
                aiming = False
                sunk = False
                active_effects.clear()
                WALLS = generate_obstacles()
                BOOST_ZONE = generate_boost_zone()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not sunk and not game_over and math.hypot(event.pos[0] - ball_position[0],
                                                         event.pos[1] - ball_position[1]) <= BALL_RADIUS * 2:
                if math.hypot(*velocity) < STOP_SPEED:
                    aiming = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and aiming:
            pull_x = max(-MAX_PULL, min(MAX_PULL, ball_position[0] - event.pos[0]))
            pull_y = max(-MAX_PULL, min(MAX_PULL, ball_position[1] - event.pos[1]))
            pull_length = math.hypot(pull_x, pull_y)
            if pull_length > 4:
                power = min(MAX_SPEED, pull_length * 5)
                velocity = [pull_x / pull_length * power, pull_y / pull_length * power]
                hole_strokes += 1
            aiming = False

    if not aiming and not sunk and math.hypot(*velocity) >= STOP_SPEED:
        steps = max(1, math.ceil(dt * max(abs(velocity[0]), abs(velocity[1])) / 4))
        step_dt = dt / steps
        for _ in range(steps):
            ball_position = (ball_position[0] + velocity[0] * step_dt,
                             ball_position[1] + velocity[1] * step_dt)
            ball_shape = make_ball_polygon(ball_position)

            effects_now = set()
            if Collide.polygon(ball_shape, BOOST_ZONE):
                effects_now.add("boost")
                if "boost" not in active_effects:
                    velocity[0] *= 1.45
                    velocity[1] *= 1.45
            active_effects = effects_now

            if Collide.polygon(ball_shape, HOLE):
                sunk = True
                velocity = [0.0, 0.0]
                total_strokes += hole_strokes
                if hole_number == TOTAL_HOLES:
                    game_over = True
                    record_eligible = qualifies_for_record(total_strokes, records)
                break

            for wall in WALLS:
                collision = Collide.polygon(ball_shape, wall)
                if collision:
                    distance, _, normal = nearest_edge(ball_position, collision[1])
                    if distance < BALL_RADIUS:
                        correction = BALL_RADIUS - distance + 0.2
                        ball_position = (ball_position[0] + normal[0] * correction,
                                         ball_position[1] + normal[1] * correction)
                    speed_into_wall = velocity[0] * normal[0] + velocity[1] * normal[1]
                    if speed_into_wall < 0:
                        velocity[0] -= 1.82 * speed_into_wall * normal[0]
                        velocity[1] -= 1.82 * speed_into_wall * normal[1]
                    ball_shape = make_ball_polygon(ball_position)

            if ball_position[0] < COURSE.left + BALL_RADIUS:
                ball_position = (COURSE.left + BALL_RADIUS, ball_position[1])
                velocity[0] = abs(velocity[0]) * 0.82
            elif ball_position[0] > COURSE.right - BALL_RADIUS:
                ball_position = (COURSE.right - BALL_RADIUS, ball_position[1])
                velocity[0] = -abs(velocity[0]) * 0.82
            if ball_position[1] < COURSE.top + BALL_RADIUS:
                ball_position = (ball_position[0], COURSE.top + BALL_RADIUS)
                velocity[1] = abs(velocity[1]) * 0.82
            elif ball_position[1] > COURSE.bottom - BALL_RADIUS:
                ball_position = (ball_position[0], COURSE.bottom - BALL_RADIUS)
                velocity[1] = -abs(velocity[1]) * 0.82

            velocity[0] *= FRICTION ** (step_dt * 60)
            velocity[1] *= FRICTION ** (step_dt * 60)

        if math.hypot(*velocity) < STOP_SPEED:
            velocity = [0.0, 0.0]

    SCREEN.fill((24, 34, 38))
    pygame.draw.rect(SCREEN, (61, 112, 83), COURSE, border_radius=18)
    pygame.draw.rect(SCREEN, (188, 207, 156), COURSE, 3, border_radius=18)

    draw_polygon(SCREEN, BOOST_ZONE, (63, 151, 158), (142, 231, 214))
    for wall in WALLS:
        draw_polygon(SCREEN, wall, (48, 69, 69), (154, 183, 157), 3)

    draw_polygon(SCREEN, HOLE, (26, 31, 31), (230, 234, 208), 2)
    pygame.draw.circle(SCREEN, (234, 236, 218), (HOLE_CENTER[0] + 5, HOLE_CENTER[1] - 12), 3)

    if aiming:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pull_x = ball_position[0] - mouse_x
        pull_y = ball_position[1] - mouse_y
        pull_length = math.hypot(pull_x, pull_y)
        if pull_length > 1:
            aim_x = pull_x / pull_length
            aim_y = pull_y / pull_length
            preview_length = min(MAX_SPEED, pull_length * 5) * 0.3
            for index in range(1, 9):
                point = (int(ball_position[0] + aim_x * preview_length * index / 8),
                         int(ball_position[1] + aim_y * preview_length * index / 8))
                pygame.draw.circle(SCREEN, (244, 239, 204), point, 2)
            pygame.draw.line(SCREEN, (244, 239, 204), ball_position,
                             (ball_position[0] - aim_x * min(MAX_PULL, pull_length),
                              ball_position[1] - aim_y * min(MAX_PULL, pull_length)), 2)

    ball_color = (247, 242, 222) if not sunk else (134, 145, 133)
    pygame.draw.circle(SCREEN, (37, 52, 45), (round(ball_position[0] + 2), round(ball_position[1] + 3)), BALL_RADIUS + 1)
    pygame.draw.circle(SCREEN, ball_color, (round(ball_position[0]), round(ball_position[1])), BALL_RADIUS)
    pygame.draw.circle(SCREEN, (255, 255, 246), (round(ball_position[0] - 3), round(ball_position[1] - 3)), 2)

    pygame.draw.rect(SCREEN, (24, 34, 38), (0, 0, 800, 58))
    SCREEN.blit(FONT.render(
        f"BURACO {hole_number}/{TOTAL_HOLES}   Tacadas: {total_strokes}   Neste buraco: {hole_strokes}",
        True, (238, 239, 217)), (28, 14))
    SCREEN.blit(SMALL_FONT.render("Arraste a bola para mirar e solte para tacar | R nova partida", True, (184, 201, 184)), (28, 38))
    boost_label = SMALL_FONT.render("TURBO", True, (203, 245, 230))
    SCREEN.blit(boost_label, boost_label.get_rect(center=BOOST_ZONE.bounding_box.center))

    if sunk and not game_over:
        label = FONT.render(f"Buraco {hole_number} concluido!  ENTER para continuar", True, (255, 246, 205))
        pygame.draw.rect(SCREEN, (24, 34, 38), (145, 272, 510, 52), border_radius=8)
        SCREEN.blit(label, label.get_rect(center=(400, 298)))

    if game_over:
        pygame.draw.rect(SCREEN, (24, 34, 38), (135, 78, 530, 480), border_radius=8)
        pygame.draw.rect(SCREEN, (188, 207, 156), (135, 78, 530, 480), 2, border_radius=8)
        SCREEN.blit(FONT.render("FIM DA PARTIDA", True, (255, 246, 205)), (180, 96))
        SCREEN.blit(FONT.render(f"Total: {total_strokes} tacadas em {TOTAL_HOLES} buracos", True,
                                (238, 239, 217)), (180, 127))
        if record_eligible and not record_saved:
            SCREEN.blit(SMALL_FONT.render("Nova pontuacao no top 10! Digite seu nome e pressione ENTER", True,
                                          (203, 245, 230)), (160, 164))
            pygame.draw.rect(SCREEN, (45, 62, 57), (160, 188, 480, 34), border_radius=4)
            name_text = player_name or "Nome do jogador"
            SCREEN.blit(FONT.render(name_text, True, (255, 246, 205)), (172, 194))
        elif record_saved:
            SCREEN.blit(SMALL_FONT.render("Recorde salvo! Pressione R para nova partida.", True,
                                          (203, 245, 230)), (180, 164))
        else:
            SCREEN.blit(SMALL_FONT.render("Pontuacao fora do top 10. Pressione R para jogar novamente.",
                                          True, (220, 205, 175)), (160, 164))

        SCREEN.blit(SMALL_FONT.render("MELHORES 10 PARTIDAS", True, (238, 239, 217)), (180, 238))
        for index, record in enumerate(records):
            row = f"{index + 1:>2}. {record['name']:<16} {record['strokes']:>3} tacadas"
            SCREEN.blit(SMALL_FONT.render(row, True, (184, 201, 184)), (190, 267 + index * 24))

    pygame.display.flip()

pygame.quit()