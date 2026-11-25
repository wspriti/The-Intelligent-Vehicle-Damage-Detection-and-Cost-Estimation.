# damage_cost = {
#     "scratch": 1500,
#     "dent": 3000,
#     "crack": 2500,
#     "glass shatter": 5000,
#     "lamp broken": 4000,
#     "tire flat": 2000
# }
# 📍 Car part cost multipliers
part_multipliers = {
    "bumper": 0.9,
    "door": 1.3,
    "hood": 1.5,
    "fender": 1.2,
    "headlight": 1.4,
    "taillight": 1.4,
    "windshield": 1.6,
    "tire": 1.0
}
damage_cost = {
    "scratch": {"min": 500, "max": 3000},
    "dent": {"min": 1500, "max": 8000},
    "crack": {"min": 2000, "max": 7000},
    "glass shatter": {"min": 4000, "max": 12000},
    "lamp broken": {"min": 3000, "max": 9000},
    "tire flat": {"min": 1000, "max": 4000}
}

def estimate_cost(labels):
    total = 0
    for label in labels:
        total += damage_cost.get(label, 1000)
    return total

def calculate_intensity(box, img_w, img_h):

    x1, y1, x2, y2 = box
    area = (x2 - x1) * (y2 - y1)
    img_area = img_w * img_h

    ratio = area / img_area

    if ratio < 0.02:
        return "Minor", 1
    elif ratio < 0.08:
        return "Moderate", 1.5
    else:
        return "Severe", 2