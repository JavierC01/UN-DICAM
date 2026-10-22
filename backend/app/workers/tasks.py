import time
from pathlib import Path

import cv2
import numpy as np

from app.Core.celery_app import celery_app
from app.Core.config import settings
from app.db.models import Analysis, Project, Result, SpecimenConfig, TrackingMesh
from app.db.session import SessionLocal
from app.dic.analisis import Analisis
from app.dic.mapas import guardar_mapa
from app.dic.ocr import extract_load_value
from app.dic.pipeline import procesar_par_frames
from app.dic.probeta import MedidasProbeta, Probeta
from app.services.devices import DeviceService, DeviceServiceError

# Numero de frames a procesar cuando la fuente es una camara en vivo (sin conteo total de frames)
# y el cliente no especifico frame_fin.
DEFAULT_LIVE_FRAMES = 30

# Se usa si el proyecto no configuro roi_carga o el OCR no pudo leer un valor en ese frame.
CARGA_N_PLACEHOLDER = 0.0


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


@celery_app.task(bind=True)
def process_full_analysis(self, analysis_id: str, project_id: str, source_id: int | str, params: dict) -> dict:
    db = SessionLocal()
    try:
        specimen = db.get(SpecimenConfig, project_id)
        mesh = db.get(TrackingMesh, project_id)
        if specimen is None or mesh is None:
            raise AnalysisPipelineError(
                "Falta calibrar la probeta o construir la malla de rastreo para este proyecto"
            )

        probeta = Probeta(
            MedidasProbeta(
                long_calibracion_px=specimen.long_calibracion_px,
                long_calibracion_mm=specimen.long_calibracion_mm,
                ancho_mm=specimen.ancho_mm,
                espesor_mm=specimen.espesor_mm,
                long_calibre_mm=specimen.long_calibre_mm,
            )
        )
        nodos_ref = mesh.nodos
        subset_size = int(params.get("subset_size", 32))
        search_range = int(params.get("search_range", 20))
        frame_inicio = int(params.get("frame_inicio", 0))

        output_dir = Path(settings.STORAGE_DIR) / "analyses" / analysis_id
        analisis = Analisis(output_dir=str(output_dir))

        device_service = DeviceService()
        try:
            cap = device_service.open_capture_for_source_id(source_id)
        except DeviceServiceError as exc:
            raise AnalysisPipelineError(str(exc)) from exc

        coef_muestras: list[float] = []
        esfuerzo_max_mpa = 0.0
        strain_max = 0.0
        ultimo_campo = None
        frames_ok = 0

        try:
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
                        imagen_ref, imagen_def, nodos_ref, probeta.mm_por_px, subset_size, search_range
                    )
                except ValueError:
                    continue

                frames_ok += 1
                coef_muestras.append(resultado.coef_correlacion_medio)
                ultimo_campo = resultado.campo

                carga_n = CARGA_N_PLACEHOLDER
                if specimen.roi_carga:
                    try:
                        carga_n = extract_load_value(frame, specimen.roi_carga)
                    except Exception:
                        carga_n = CARGA_N_PLACEHOLDER

                datos = probeta.preparar_datos_analisis(
                    u_px=resultado.nodos[4].u_px,
                    v_px=resultado.nodos[4].v_px,
                    eps_xx=resultado.campo.eps_xx_medio,
                    eps_yy=resultado.campo.eps_yy_medio,
                    eps_xy=resultado.campo.eps_xy_medio,
                    carga_n=carga_n,
                )
                analisis.procesar_frame(datos, frame_id=frame_inicio + idx)

                esfuerzo_max_mpa = max(esfuerzo_max_mpa, datos["esfuerzo_mpa"])
                strain_max = max(strain_max, abs(datos["eps_yy"]))

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(idx / total_frames * 100),
                        "frames_procesados": idx,
                        "frames_total": total_frames,
                        "mensaje": f"Procesando frame {idx}/{total_frames}",
                    },
                )

            if frames_ok == 0:
                raise AnalysisPipelineError("No fue posible rastrear ningun frame del video")
        finally:
            cap.release()

        guardar_mapa(ultimo_campo.eps_xx, "Deformacion XX", output_dir / "mapa_xx.jpg")
        guardar_mapa(ultimo_campo.eps_yy, "Deformacion YY", output_dir / "mapa_yy.jpg")
        guardar_mapa(ultimo_campo.eps_xy, "Deformacion XY", output_dir / "mapa_xy.jpg")

        data = {
            "curva_desplaz_carga": analisis.curva_desplaz_carga,
            "curva_esfuerzo_strain": analisis.curva_esfuerzo_strain,
            "mapa_xx_path": f"/storage/analyses/{analysis_id}/mapa_xx.jpg",
            "mapa_yy_path": f"/storage/analyses/{analysis_id}/mapa_yy.jpg",
            "mapa_xy_path": f"/storage/analyses/{analysis_id}/mapa_xy.jpg",
            "esfuerzo_max_mpa": esfuerzo_max_mpa,
            "strain_max": strain_max,
            "coef_correlacion_medio": float(np.mean(coef_muestras)) if coef_muestras else 0.0,
        }

        analysis_row = db.get(Analysis, analysis_id)
        if analysis_row is not None:
            analysis_row.status = "success"
        db.add(Result(analysis_id=analysis_id, data=data))
        project = db.get(Project, project_id)
        if project is not None:
            project.status = "completed"
        db.commit()

        return {
            "status": "success",
            "progress": 100,
            "frames_procesados": frames_ok,
            "frames_total": total_frames,
            "mensaje": "Analisis completado",
        }
    except Exception:
        db.rollback()
        analysis_row = db.get(Analysis, analysis_id)
        if analysis_row is not None:
            analysis_row.status = "failed"
            db.commit()
        raise
    finally:
        db.close()
