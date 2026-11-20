"""Tk preview and Python counterpart of the geometry helpers."""
import math

def in_circle(point, radius): return math.hypot(*point) <= radius
def in_cone(point, radius, angle, direction=(1, 0)):
    length = math.hypot(*point)
    return length == 0 or (length <= radius and (point[0] * direction[0] + point[1] * direction[1]) / length >= math.cos(math.radians(angle) / 2))
def in_line(point, length, width, direction=(1, 0)):
    return 0 <= point[0] * direction[0] + point[1] * direction[1] <= length and abs(point[0] * direction[1] - point[1] * direction[0]) <= width

def draw_ability_preview(canvas, target_type, radius_value, width_value, angle_value="90"):
    canvas.delete("all")
    try:
        radius = float(radius_value); width = float(width_value or 1); angle = float(angle_value or 90)
        if radius < 0 or width < 0 or not 0 <= angle <= 360: raise ValueError
    except (TypeError, ValueError):
        canvas.create_text(180, 110, text="入力値を確認", fill="#ffcc66", font=("Arial", 14)); return
    size = 360; center = size / 2; extent = max(radius, width, 1) + 1; scale = min(26, (size - 44) / (2 * extent))
    def xy(point): return center + point[0] * scale, center - point[1] * scale
    for n in range(math.floor(-extent), math.ceil(extent) + 1):
        x = xy((n, 0))[0]; y = xy((0, n))[1]; canvas.create_line(x, 0, x, size, fill="#38404a"); canvas.create_line(0, y, size, y, fill="#38404a")
    canvas.create_text(8, 8, anchor="nw", text=f"1マス=1ブロック  半径={radius:g}  角度={angle:g}°  幅={width:g}", fill="#fff")
    for px in range(math.floor(-extent), math.ceil(extent) + 1):
        for pz in range(math.floor(-extent), math.ceil(extent) + 1):
            hit = target_type == "self" and (px, pz) == (0, 0)
            if target_type == "circle": hit = in_circle((px, pz), radius)
            elif target_type == "cone": hit = in_cone((px, pz), radius, angle)
            elif target_type == "line": hit = in_line((px, pz), radius, width)
            elif target_type == "look": hit = 0 <= px <= radius and pz == 0
            if (px, pz) != (0, 0):
                x, y = xy((px, pz)); canvas.create_oval(x-3, y-3, x+3, y+3, fill="#40c878" if hit else "#d9534f", outline="")
    dummy = getattr(canvas, "_dummy_point", (1, 0))
    dummy_hit = target_type == "circle" and in_circle(dummy, radius) or target_type == "cone" and in_cone(dummy, radius, angle) or target_type == "line" and in_line(dummy, radius, width) or target_type == "look" and 0 <= dummy[0] <= radius and dummy[1] == 0 or target_type == "self" and dummy == (0, 0)
    x, y = xy(dummy); canvas.create_oval(x-6, y-6, x+6, y+6, outline="#40c878" if dummy_hit else "#d9534f", width=2); canvas.create_text(x+8, y, text="dummy", anchor="w", fill="#fff")
    canvas.create_oval(center-5, center-5, center+5, center+5, fill="#fff", outline="")
    canvas.create_line(center, center, center + scale, center, fill="#fff", width=2, arrow="last")
