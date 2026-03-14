from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="UN-DICAM Backend",
    description="API para la aplicación móvil",
    version="1.0.0"
)

# Configuración de CORS: Permite a tu app móvil (React Native/Expo) comunicarse con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, reemplaza "*" por los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos de ejemplo (Pydantic valida los datos automáticamente)
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float

@app.get("/", tags=["Health"])
def read_root():
    """
    Ruta raíz para verificar que el servidor está funcionando.
    """
    return {"message": "¡El servidor FastAPI de UN-DICAM está en línea!"}

@app.get("/api/status", tags=["Health"])
def get_status():
    """
    Ruta de estado para la app móvil.
    """
    return {"status": "ok", "service": "UN-DICAM API"}

# Ejemplo de una ruta que recibe datos (POST)
@app.post("/api/items/", tags=["Ejemplo"])
def create_item(item: Item):
    """
    Ejemplo de cómo recibir datos desde la aplicación móvil.
    """
    return {"message": "Item recibido correctamente", "data": item}
