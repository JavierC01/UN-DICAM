from app.dic.probeta import MedidasProbeta, Probeta
from app.schemas.specimen import SpecimenConfigRequest
from app.services.specimen import SpecimenService


def test_specimen_config_calculates_px_ratio_and_area():
    service = SpecimenService()
    payload = SpecimenConfigRequest(
        project_id="test",
        long_calibracion_px=100,
        long_calibracion_mm=25,
        ancho_mm=5,
        espesor_mm=3,
        long_calibre_mm=25,
    )

    result = service.configure(payload)

    assert result.px_por_mm == 4
    assert result.area_mm2 == 15


def test_probeta_core_calculates_px_ratio_and_stress():
    probeta = Probeta(
        MedidasProbeta(
            long_calibracion_px=100,
            long_calibracion_mm=25,
            ancho_mm=5,
            espesor_mm=3,
            long_calibre_mm=25,
        )
    )

    assert probeta.px_por_mm == 4
    assert probeta.area_mm2 == 15
    assert probeta.calcular_esfuerzo(150) == 10
