import pygame
import config

def draw_chart(surface, rect, font, title, min_val, max_val, series_list):
    # 1. Rysowanie tła i ramki wykresu
    pygame.draw.rect(surface, (15, 18, 26), rect)
    pygame.draw.rect(surface, (50, 60, 80), rect, 1)

    # Margines z lewej strony przeznaczony na etykiety osi Y
    left_margin = 45
    chart_rect = pygame.Rect(
        rect.x + left_margin, 
        rect.y + 25, 
        rect.width - left_margin - 10, 
        rect.height - 35
    )

    # 2. Tytuł wykresu
    title_txt = font.render(title, True, config.COLOR_TEXT)
    surface.blit(title_txt, (rect.x + 10, rect.y + 5))

    # 3. Rysowanie osi Y i poziomych linii siatki
    pygame.draw.line(surface, (80, 90, 110), (chart_rect.x, chart_rect.y), (chart_rect.x, chart_rect.bottom), 2)

    # Wyznaczenie pozycji dla wartości max, mid, min
    y_positions = {
        max_val: chart_rect.y,
        (max_val + min_val) / 2: chart_rect.y + chart_rect.height / 2,
        min_val: chart_rect.bottom
    }

    # Rysowanie podziałki i etykiet wartości na osi Y
    for val, y_pos in y_positions.items():
        # Pozioma linia siatki
        pygame.draw.line(surface, (35, 42, 58), (chart_rect.x, y_pos), (chart_rect.right, y_pos), 1)
        
        # Mała kreska na osi Y
        pygame.draw.line(surface, (80, 90, 110), (chart_rect.x - 4, y_pos), (chart_rect.x, y_pos), 2)

        # Tekst etykiety z wartością
        lbl_txt = font.render(f"{val:.1f}", True, (140, 150, 170))
        surface.blit(lbl_txt, (chart_rect.x - lbl_txt.get_width() - 6, y_pos - lbl_txt.get_height() // 2))

    # Linia odniesienia Zero (jeśli 0 mieści się w zakresie min_val..max_val)
    if min_val < 0 < max_val:
        zero_y = chart_rect.bottom - ((0 - min_val) / (max_val - min_val)) * chart_rect.height
        pygame.draw.line(surface, (100, 110, 130), (chart_rect.x, zero_y), (chart_rect.right, zero_y), 1)

    # 4. Rysowanie serii danych (wykresów)
    for series in series_list:
        data = series.get("data", [])
        color = series.get("color", (255, 255, 255))
        if len(data) < 2:
            continue

        pts = []
        for i, val in enumerate(data):
            x = chart_rect.x + (i / max(1, len(data) - 1)) * chart_rect.width
            val_clamped = max(min_val, min(max_val, val))
            norm_y = (val_clamped - min_val) / (max_val - min_val)
            y = chart_rect.bottom - norm_y * chart_rect.height
            pts.append((x, y))

        if len(pts) > 1:
            pygame.draw.lines(surface, color, False, pts, 2)