"""Poligonos de prueba no rectangulares (coordenadas en px)."""

RECTANGULO = [{"x": 60, "y": 60}, {"x": 240, "y": 60}, {"x": 240, "y": 240}, {"x": 60, "y": 240}]

# L: brazo vertical a la izquierda y brazo horizontal abajo; el cuadrante superior derecho es vacio.
FORMA_L = [
    {"x": 20, "y": 20}, {"x": 120, "y": 20}, {"x": 120, "y": 180},
    {"x": 280, "y": 180}, {"x": 280, "y": 280}, {"x": 20, "y": 280},
]

# Hueso de perro: cabezas anchas arriba y abajo, cuello angosto en el centro.
HUESO_DE_PERRO = [
    {"x": 40, "y": 20}, {"x": 260, "y": 20}, {"x": 260, "y": 90}, {"x": 190, "y": 120},
    {"x": 190, "y": 180}, {"x": 260, "y": 210}, {"x": 260, "y": 280}, {"x": 40, "y": 280},
    {"x": 40, "y": 210}, {"x": 110, "y": 180}, {"x": 110, "y": 120}, {"x": 40, "y": 90},
]

# Probeta con entalla en V desde el borde derecho.
ENTALLA = [
    {"x": 40, "y": 40}, {"x": 260, "y": 40}, {"x": 260, "y": 130}, {"x": 160, "y": 150},
    {"x": 260, "y": 170}, {"x": 260, "y": 260}, {"x": 40, "y": 260},
]
