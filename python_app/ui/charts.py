import pygame
import config

def draw_chart(surface, rect, font, charts_config):
    """
    Renders one or multiple line charts within the specified 'rect' region.
    """
    if isinstance(charts_config, dict):
        charts_config = [charts_config]

    num_charts = len(charts_config)
    if num_charts == 0:
        return

    # Background and border for the charts panel
    pygame.draw.rect(surface, (15, 18, 26), rect)
    pygame.draw.rect(surface, (50, 60, 80), rect, 1)

    chart_height = rect.height / num_charts

    for idx, cfg in enumerate(charts_config):
        title = cfg.get("title", "")
        min_val = cfg.get("min_val", -1.0)
        max_val = cfg.get("max_val", 1.0)
        series_list = cfg.get("series", [])

        sub_rect = pygame.Rect(
            rect.x,
            rect.y + idx * chart_height,
            rect.width,
            chart_height
        )

        left_margin = 45
        top_margin = 20
        bottom_margin = 22  # Prevents overlapping of bottom Y-axis labels (e.g., -30.0)

        chart_rect = pygame.Rect(
            sub_rect.x + left_margin,
            sub_rect.y + top_margin,
            sub_rect.width - left_margin - 10,
            max(10, sub_rect.height - top_margin - bottom_margin)
        )

        # Render chart title
        if title:
            title_txt = font.render(title, True, config.COLOR_TEXT)
            surface.blit(title_txt, (sub_rect.x + 10, sub_rect.y + 2))

        val_range = max_val - min_val if max_val != min_val else 1.0

        # Y-axis line and tick labels
        pygame.draw.line(surface, (80, 90, 110), (chart_rect.x, chart_rect.y), (chart_rect.x, chart_rect.bottom), 2)

        y_positions = {
            max_val: chart_rect.y,
            (max_val + min_val) / 2: chart_rect.y + chart_rect.height / 2,
            min_val: chart_rect.bottom
        }

        for val, y_pos in y_positions.items():
            pygame.draw.line(surface, (35, 42, 58), (chart_rect.x, y_pos), (chart_rect.right, y_pos), 1)
            pygame.draw.line(surface, (80, 90, 110), (chart_rect.x - 4, y_pos), (chart_rect.x, y_pos), 2)
            lbl_txt = font.render(f"{val:.1f}", True, (140, 150, 170))
            surface.blit(lbl_txt, (chart_rect.x - lbl_txt.get_width() - 6, y_pos - lbl_txt.get_height() // 2))

        # Render zero reference line
        if min_val < 0 < max_val:
            zero_y = chart_rect.bottom - ((0 - min_val) / val_range) * chart_rect.height
            pygame.draw.line(surface, (100, 110, 130), (chart_rect.x, zero_y), (chart_rect.right, zero_y), 1)

        # Plot data series
        for series in series_list:
            data = series.get("data", [])
            color = series.get("color", (255, 255, 255))
            if len(data) < 2:
                continue

            pts = []
            for i, val in enumerate(data):
                x = chart_rect.x + (i / max(1, len(data) - 1)) * chart_rect.width
                val_clamped = max(min_val, min(max_val, val))
                norm_y = (val_clamped - min_val) / val_range
                y = chart_rect.bottom - norm_y * chart_rect.height
                pts.append((x, y))

            if len(pts) > 1:
                pygame.draw.lines(surface, color, False, pts, 2)

        # Subchart separator line
        if idx < num_charts - 1:
            pygame.draw.line(surface, (40, 50, 70), (sub_rect.x, sub_rect.bottom), (sub_rect.right, sub_rect.bottom), 1)