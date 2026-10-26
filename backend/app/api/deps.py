from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.Core.config import settings
from app.Core.security import verificar_token
from app.db.models import User
from app.db.session import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    encabezado = request.headers.get("Authorization", "")
    token = encabezado[7:] if encabezado.lower().startswith("bearer ") else None
    # shortcut: las descargas abiertas en el navegador del telefono no pueden mandar encabezados, asi que
    # se acepta ?token=; el token queda en logs de acceso. Cambiar a enlaces firmados de un solo uso si se expone a internet.
    token = token or request.query_params.get("token")
    user_id = verificar_token(token, settings.SECRET_KEY) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesion invalida o expirada; inicia sesion de nuevo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
