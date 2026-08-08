from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def guardar_mapa(valores: list[list[float]], titulo: str, ruta: Path) -> None:
    """Renderiza la grilla 2x2 de deformacion como un mapa de calor JPG."""
    fig, ax = plt.subplots(figsize=(3, 3))
    imagen = ax.imshow(valores, cmap="jet", interpolation="bilinear")
    ax.set_title(titulo, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(imagen, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(ruta, format="jpg", dpi=120)
    plt.close(fig)
