import math
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from app.cargas.sincronizacion import cargas_en_frames
from app.Core.celery_app import celery_app
from app.Core.config import VERSION, settings
from app.db.models import Analysis, MachineLoad, Project, Result, SpecimenConfig, TrackingMesh
from app.db.session import SessionLocal
from app.dic.ensayos import obtener_ensayo
from app.dic.mapas import guardar_mapa
from app.dic.ocr import extract_load_value
from app.dic.pipeline import procesar_par_frames
from app.dic.probeta import MedidasProbeta, Probeta
from app.dic.rastreo import preparar_geometria
from app.dic.strain import interpolar_desplazamiento, localizar_punto
from app.services.devices import DeviceService, DeviceServiceError, es_camara, hash_video

# Numero de frames a procesar cuando la fuente es una camara en vivo (sin conteo total de frames)
# y el cliente no especifico frame_fin.
DEFAULT_LIVE_FRAMES = 30


@celery_app.task(bind=True)
def dummy_task(self) -> dict[str, str]:
    for step in range(1, 6):
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": step * 20,
                "frames_procesados": step,
                "frames_total": 5,
                "mensaje": f"Worker activo: paso {step}/5",
            },
        )
        time.sleep(0.2)
    return {"status": "done"}


class AnalysisPipelineError(RuntimeError):
    pass


def _sin_nan(valor):
    """JSON no admite NaN: los datos faltantes se guardan como null."""
    if isinstance(valor, float):
        return valor if math.isfinite(valor) else None
    if isinstance(valor, dict):
        return {k: _sin_nan(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_sin_nan(v) for v in valor]
    return valor


def _max_finito(valores: list[float]) -> float:
    finitos = [v for v in valores if math.isfinite(v)]
    return max(finitos) if finitos else math.nan


def _commit_git() -> str | None:
    if settings.GIT_COMMIT:
        return settings.GIT_COMMIT
    try:
        salida = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return salida.stdout.strip() or None


def _paso_px(nodos: list[dict], columnas: int) -> dict:
    return {
        "x": nodos[1]["x"] - nodos[0]["x"] if columnas > 1 else None,
        "y": nodos[columnas]["y"] - nodos[0]["y"] if len(nodos) > columnas else None,
    }


def _marcar_estado(db, analysis_id: str, project_id: str | None, estado: str) -> None:
    analysis_row = db.get(Analysis, analysis_id)
    if analysis_row is not None:
        analysis_row.status = estado
    if project_id is not None:
        project = db.get(Project, project_id)
        if project is not None:
            project.status = {"running": "in_progress", "success": "completed", "failed": "failed"}[estado]
    db.commit()


@celery_app.task(bind=True)
def process_full_analysis(self, analysis_id: str, project_id: str, source_id: int | str, params: dict) -> dict:
    db = SessionLocal()
    try:
        _marcar_estado(db, analysis_id, project_id, "running")
        specimen = db.get(SpecimenConfig, project_id)
        mesh = db.get(TrackingMesh, project_id)
        if specimen is None or mesh is None:
            raise AnalysisPipelineError(
                "Falta calibrar la probeta o construir la malla de rastreo para este proyecto"
            )

        advertencias: list[str] = []
        probeta = Probeta(
            MedidasProbeta(
                long_calibracion_px=specimen.long_calibracion_px,
                long_calibracion_mm=specimen.long_calibracion_mm,
                ancho_mm=specimen.ancho_mm,
                espesor_mm=specimen.espesor_mm,
                long_calibre_mm=specimen.long_calibre_mm,
            )
        )
        subset_size = int(params.get("subset_size", 32))
        search_range = int(params.get("search_range", 20))
        frame_inicio = int(params.get("frame_inicio", 0))

        try:
            geometria = preparar_geometria(
                mesh.nodos, mesh.validos, mesh.poligono, mesh.frame_width, mesh.frame_height, subset_size
            )
        except ValueError as exc:
            raise AnalysisPipelineError(str(exc)) from exc
        invalidos = geometria.validos.count(False)
        if invalidos:
            advertencias.append(
                f"{invalidos} de {len(geometria.nodos)} nodos quedan fuera de la region para un subset de "
                f"{subset_size} px y no se rastrean"
            )

        ensayo = obtener_ensayo(specimen.tipo_ensayo or "traccion")
        parametros_ensayo = specimen.parametros_ensayo or {}
        ubicaciones = None
        if mesh.puntos_ensayo and len(mesh.puntos_ensayo) == ensayo.n_puntos:
            ubicaciones = [localizar_punto(p, geometria.nodos, geometria.triangulos) for p in mesh.puntos_ensayo]
            if any(u is None for u in ubicaciones):
                advertencias.append("Algun punto del extensometro virtual quedo fuera de la malla valida; su medida es nula")
            puntos_ensayo_mm = [(p["x"] * probeta.mm_por_px, p["y"] * probeta.mm_por_px) for p in mesh.puntos_ensayo]
        else:
            advertencias.append(
                f"No se marcaron los {ensayo.n_puntos} puntos del ensayo de {ensayo.nombre} ({ensayo.puntos}); "
                "no hay curva del ensayo ni propiedad"
            )

        fuente_carga = specimen.fuente_carga or "ninguna"
        carga_maquina = db.get(MachineLoad, project_id) if fuente_carga == "archivo" else None
        if fuente_carga == "archivo" and carga_maquina is None:
            raise AnalysisPipelineError("La fuente de carga es el archivo de la maquina, pero no se ha importado ninguno")
        if fuente_carga == "ninguna":
            advertencias.append("Sin fuente de carga configurada: carga y esfuerzo quedan nulos")

        try:
            video_sha256 = hash_video(source_id)
            cap = DeviceService().open_capture_for_source_id(source_id)
        except DeviceServiceError as exc:
            raise AnalysisPipelineError(str(exc)) from exc

        output_dir = Path(settings.STORAGE_DIR) / "analyses" / analysis_id
        output_dir.mkdir(parents=True, exist_ok=True)
        frames: list[dict] = []
        fallos_ocr = 0
        ultimo_campo = None

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            frame_fin = params.get("frame_fin")
            if frame_fin is None:
                frame_fin = (frame_count - 1) if frame_count > 0 else (frame_inicio + DEFAULT_LIVE_FRAMES - 1)
            frame_fin = max(frame_inicio, int(frame_fin))

            if frame_count > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_inicio)
            else:
                for _ in range(frame_inicio):
                    cap.read()

            ok, ref_frame = cap.read()
            if not ok:
                raise AnalysisPipelineError("No fue posible leer el frame de referencia")
            imagen_ref = cv2.cvtColor(ref_frame, cv2.COLOR_BGR2GRAY)

            total_frames = max(1, frame_fin - frame_inicio)

            for idx in range(1, total_frames + 1):
                ok, frame = cap.read()
                if not ok:
                    break
                imagen_def = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                try:
                    resultado = procesar_par_frames(
                        imagen_ref, imagen_def, geometria, probeta.mm_por_px, subset_size, search_range
                    )
                except ValueError:
                    continue
                ultimo_campo = resultado.campo

                carga_n = math.nan
                if fuente_carga == "ocr":
                    try:
                        carga_n = extract_load_value(frame, specimen.roi_carga)
                    except Exception:
                        fallos_ocr += 1  # se descarta el punto; nunca se reemplaza por 0

                medida = math.nan
                if ubicaciones is not None:
                    desplaz = [interpolar_desplazamiento(u, resultado.desplazamientos_mm) for u in ubicaciones]
                    medida = ensayo.medir(puntos_ensayo_mm, desplaz, parametros_ensayo)

                frames.append(
                    {
                        "frame": frame_inicio + idx,
                        "tiempo_s": idx / fps if fps > 0 else math.nan,
                        "u_mm": resultado.u_mm_centro,
                        "v_mm": resultado.v_mm_centro,
                        "eps_xx": resultado.campo.eps_xx_medio,
                        "eps_yy": resultado.campo.eps_yy_medio,
                        "eps_xy": resultado.campo.eps_xy_medio,
                        "carga_n": carga_n,
                        "medida_ensayo": medida,
                        "coef_correlacion": resultado.coef_correlacion_medio,
                        "nodos_perdidos": resultado.nodos_perdidos,
                    }
                )

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(idx / total_frames * 100),
                        "frames_procesados": idx,
                        "frames_total": total_frames,
                        "mensaje": f"Procesando frame {idx}/{total_frames}",
                    },
                )

            if not frames:
                raise AnalysisPipelineError("No fue posible rastrear ningun frame del video")
        finally:
            cap.release()

        carga_info: dict = {"fuente": fuente_carga}
        if fuente_carga == "ocr":
            carga_info["fallos_ocr"] = fallos_ocr
            if fallos_ocr:
                advertencias.append(f"El OCR no pudo leer la carga en {fallos_ocr} de {len(frames)} frames; esos puntos se descartan")
        elif fuente_carga == "archivo":
            sinc = carga_maquina.sincronizacion
            if fps <= 0:
                advertencias.append("El video no informa fps: no se puede sincronizar la carga de la maquina")
                carga_info.update(interpolados=0, descartados=len(frames))
            else:
                try:
                    cargas, interpolados, descartados = cargas_en_frames(
                        [f["tiempo_s"] for f in frames],
                        carga_maquina.tiempos_s,
                        carga_maquina.cargas_n,
                        offset_s=float(sinc.get("offset_s", 0.0)),
                        evento_inicio=sinc.get("evento_inicio", "ninguno"),
                        umbral_n=sinc.get("umbral_n"),
                    )
                except ValueError as exc:
                    raise AnalysisPipelineError(f"No se pudo sincronizar la carga: {exc}") from exc
                for f, c in zip(frames, cargas):
                    f["carga_n"] = c
                carga_info.update(interpolados=interpolados, descartados=descartados)
                if descartados:
                    advertencias.append(
                        f"{descartados} frames caen fuera del registro de la maquina; su carga queda nula"
                    )

        for f in frames:
            f["esfuerzo_mpa"] = probeta.calcular_esfuerzo(f["carga_n"])
            f["respuesta_ensayo"] = ensayo.calcular_respuesta(f["carga_n"], probeta.area_mm2, parametros_ensayo)
        carga_info["frames_con_carga"] = sum(1 for f in frames if math.isfinite(f["carga_n"]))

        for componente in ("xx", "yy", "xy"):
            guardar_mapa(
                imagen_ref,
                geometria.nodos,
                ultimo_campo.triangulos,
                getattr(ultimo_campo, f"eps_{componente}"),
                f"Deformacion {componente.upper()} (ultimo frame)",
                output_dir / f"mapa_{componente}.jpg",
            )

        columna = lambda clave: [f[clave] for f in frames]
        data = {
            "frames": frames,
            "curva_desplaz_carga": {"x": columna("v_mm"), "y": columna("carga_n")},
            "curva_esfuerzo_strain": {"x": columna("eps_yy"), "y": columna("esfuerzo_mpa")},
            "ensayo": None
            if ubicaciones is None
            else {
                **ensayo.describir(),
                "parametros": parametros_ensayo,
                "curva": {"x": columna("medida_ensayo"), "y": columna("respuesta_ensayo")},
                "ajuste": None,
            },
            "mapa_xx_path": f"/storage/analyses/{analysis_id}/mapa_xx.jpg",
            "mapa_yy_path": f"/storage/analyses/{analysis_id}/mapa_yy.jpg",
            "mapa_xy_path": f"/storage/analyses/{analysis_id}/mapa_xy.jpg",
            "esfuerzo_max_mpa": _max_finito(columna("esfuerzo_mpa")),
            "strain_max": _max_finito([abs(v) for v in columna("eps_yy")]),
            "coef_correlacion_medio": float(np.mean(columna("coef_correlacion"))),
            "carga": carga_info,
            "advertencias": advertencias,
            "metadatos": {
                "fecha_utc": datetime.now(timezone.utc).isoformat(),
                "software": {"version": VERSION, "commit": _commit_git()},
                "parametros": {**params, "paso_nodos_px": _paso_px(geometria.nodos, mesh.columnas)},
                "malla": {
                    "filas": mesh.filas,
                    "columnas": mesh.columnas,
                    "subset_malla_px": mesh.subset_size,
                    "nodos_total": len(geometria.nodos),
                    "nodos_validos": geometria.validos.count(True),
                    "triangulos": len(geometria.triangulos),
                    "poligono_px": mesh.poligono,
                },
                "calibracion": {
                    "long_calibracion_px": specimen.long_calibracion_px,
                    "long_calibracion_mm": specimen.long_calibracion_mm,
                    "mm_por_px": probeta.mm_por_px,
                    "ancho_mm": specimen.ancho_mm,
                    "espesor_mm": specimen.espesor_mm,
                    "area_mm2": probeta.area_mm2,
                    "long_calibre_mm": specimen.long_calibre_mm,
                },
                "video": {
                    "source_id": source_id,
                    "tipo": "camara" if es_camara(source_id) else "archivo",
                    "sha256": video_sha256,
                    "fps": fps,
                    "frame_inicio": frame_inicio,
                    "frame_fin": frame_fin,
                },
                "carga": {
                    "metodo": fuente_carga,
                    "roi_carga": specimen.roi_carga if fuente_carga == "ocr" else None,
                    "archivo": None
                    if carga_maquina is None
                    else {
                        "nombre": carga_maquina.nombre_archivo,
                        "sha256": carga_maquina.sha256,
                        "mapeo": carga_maquina.mapeo,
                        "sincronizacion": carga_maquina.sincronizacion,
                    },
                },
                "ensayo": {"tipo": ensayo.tipo, "parametros": parametros_ensayo, "puntos_px": mesh.puntos_ensayo},
                "limitacion": "DIC 2D con una camara: el movimiento fuera del plano introduce error",
            },
        }
        if video_sha256 is None:
            advertencias.append("Fuente en vivo: no hay hash del video para reproducir el analisis")
        if data["metadatos"]["software"]["commit"] is None:
            advertencias.append("No se pudo determinar el commit del software (define GIT_COMMIT)")

        db.add(Result(analysis_id=analysis_id, data=_sin_nan(data)))
        _marcar_estado(db, analysis_id, project_id, "success")

        return {
            "status": "success",
            "progress": 100,
            "frames_procesados": len(frames),
            "frames_total": total_frames,
            "mensaje": "Analisis completado",
        }
    except Exception:
        db.rollback()
        _marcar_estado(db, analysis_id, project_id, "failed")
        raise
    finally:
        db.close()
