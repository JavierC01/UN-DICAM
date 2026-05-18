from pathlib import Path

import cv2


class Dispositivos:
    @staticmethod
    def listar_camaras(max_dispositivos: int = 5) -> list[dict]:
        camaras: list[dict] = []
        for camera_id in range(max_dispositivos):
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                continue
            camaras.append(
                {
                    "id": camera_id,
                    "nombre": f"Camara USB {camera_id}",
                    "ancho": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "alto": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
                }
            )
            cap.release()
        return camaras

    @staticmethod
    def abrir_archivo(path: str) -> dict:
        if not Path(path).exists():
            raise FileNotFoundError(path)
        return Dispositivos._leer_metadatos(path, "file")

    @staticmethod
    def abrir_camara(camera_id: int) -> dict:
        return Dispositivos._leer_metadatos(camera_id, "camera")

    @staticmethod
    def _leer_metadatos(source: int | str, source_type: str) -> dict:
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if source_type == "camera" else cv2.CAP_ANY)
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir la fuente de video")
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        metadata = {
            "source_id": source,
            "source_type": source_type,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": fps,
            "duration_s": (frame_count / fps) if source_type == "file" and fps > 0 else None,
        }
        cap.release()
        return metadata
