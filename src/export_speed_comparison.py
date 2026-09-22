"""Exporta comparação velocidade de referência × simulada em SVG, sem dependências extras."""
import argparse
import json
from pathlib import Path


def _points(xs, ys, x_scale, y_scale, left, top, height):
    return " ".join(
        f"{left + x * x_scale:.2f},{top + height - y * y_scale:.2f}"
        for x, y in zip(xs, ys)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, help="JSON produzido pelo simulador")
    parser.add_argument("--output", required=True, help="Arquivo SVG de saída")
    args = parser.parse_args()

    with open(args.result, encoding="utf-8") as stream:
        result = json.load(stream)

    trace = result["trace"]
    time_s = trace["time_s"]
    speed_ref = [value * 3.6 for value in trace["speed_ref_mps"]]
    speed_sim = [value * 3.6 for value in trace["speed_sim_mps"]]
    saturated = trace.get("torque_saturated", [False] * len(time_s))

    width, height = 1200, 500
    left, right, top, bottom = 70, 25, 45, 55
    plot_w, plot_h = width - left - right, height - top - bottom
    x_max = max(time_s) or 1
    y_max = max(max(speed_ref), max(speed_sim), 1) * 1.08
    x_scale, y_scale = plot_w / x_max, plot_h / y_max

    saturation_rects = []
    start = None
    for index, flag in enumerate(saturated + [False]):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            x = left + time_s[start] * x_scale
            end_time = time_s[min(index, len(time_s) - 1)]
            rect_w = max((end_time - time_s[start]) * x_scale, 1)
            saturation_rects.append(
                f'<rect x="{x:.2f}" y="{top}" width="{rect_w:.2f}" height="{plot_h}" fill="#ef4444" opacity="0.12"/>'
            )
            start = None

    ref_points = _points(time_s, speed_ref, x_scale, y_scale, left, top, plot_h)
    sim_points = _points(time_s, speed_sim, x_scale, y_scale, left, top, plot_h)
    summary = result["summary"]
    subtitle = (
        f"Erro máximo: {summary['max_speed_error_mps']:.2f} m/s | "
        f"Torque saturado: {summary['pct_time_torque_clipped']:.2f}% do ciclo"
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="{left}" y="22" font-family="Arial" font-size="18" font-weight="700">Velocidade de referência × velocidade simulada</text>
<text x="{left}" y="39" font-family="Arial" font-size="12" fill="#475569">{subtitle}</text>
<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#64748b"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#64748b"/>
{''.join(saturation_rects)}
<polyline points="{ref_points}" fill="none" stroke="#2563eb" stroke-width="2"/>
<polyline points="{sim_points}" fill="none" stroke="#f97316" stroke-width="1.6"/>
<text x="{left + plot_w / 2}" y="{height - 15}" text-anchor="middle" font-family="Arial" font-size="13">Tempo (s)</text>
<text x="18" y="{top + plot_h / 2}" text-anchor="middle" font-family="Arial" font-size="13" transform="rotate(-90 18 {top + plot_h / 2})">Velocidade (km/h)</text>
<line x1="{width - 330}" y1="25" x2="{width - 295}" y2="25" stroke="#2563eb" stroke-width="2"/><text x="{width - 288}" y="29" font-family="Arial" font-size="12">Referência</text>
<line x1="{width - 205}" y1="25" x2="{width - 170}" y2="25" stroke="#f97316" stroke-width="2"/><text x="{width - 163}" y="29" font-family="Arial" font-size="12">Simulada</text>
<rect x="{width - 90}" y="17" width="20" height="13" fill="#ef4444" opacity="0.18"/><text x="{width - 64}" y="29" font-family="Arial" font-size="12">Saturação</text>
</svg>'''
    Path(args.output).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
