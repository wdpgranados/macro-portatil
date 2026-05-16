# 🖥️ Taller de Computadoras — Sistema de Gestión v2.0

> **Stack:** Python 3.10+ · Tkinter · SQLite · Pandas · NumPy · Matplotlib  
> **Arquitectura:** Repository Pattern + Service Layer + Domain Model

---

## 📁 Estructura del Proyecto

```
taller_v2/
├── README.md                  ← Este archivo
├── main.py                    ← Punto de entrada
├── config.py                  ← Configuración global, tema visual y logging
│
├── domain/                    ← Entidades del negocio (sin dependencias externas)
│   ├── __init__.py
│   ├── pieza.py               ← Entidad Pieza (dataclass + validaciones)
│   └── venta.py               ← Entidad Venta (dataclass + UUID)
│
├── repositories/              ← Acceso a datos (abstracción + SQLite)
│   ├── __init__.py
│   ├── interfaces.py          ← Contratos abstractos (ABCs)
│   ├── inventario_repo.py     ← Implementación SQLite para Inventario
│   └── ventas_repo.py         ← Implementación SQLite para Ventas
│
├── services/                  ← Lógica de negocio (orquesta repos + dominio)
│   ├── __init__.py
│   ├── inventario_service.py  ← Operaciones de inventario y KPIs
│   └── ventas_service.py      ← Registro de ventas, filtros y KPIs
│
├── database/                  ← Infraestructura de base de datos
│   ├── __init__.py
│   └── connection.py          ← Context manager SQLite seguro
│
└── ui/                        ← Capa de presentación (Tkinter)
    ├── __init__.py
    ├── app.py                 ← Ventana principal + inyección de dependencias
    ├── dashboard.py           ← Tab: KPI cards + gráficos
    ├── inventario.py          ← Tab: CRUD de inventario
    ├── ventas.py              ← Tab: Registro de salidas
    └── reportes.py            ← Tab: Reportes con filtro por fecha
```

---

## 🏗️ Arquitectura por Capas

```
┌─────────────────────────────────────────┐
│           UI (Tkinter Tabs)             │  ← Solo presenta datos
├─────────────────────────────────────────┤
│         Services (Lógica negocio)       │  ← Reglas, validaciones, KPIs
├─────────────────────────────────────────┤
│      Repositories (Acceso a datos)      │  ← CRUD contra SQLite
├─────────────────────────────────────────┤
│        Domain (Entidades puras)         │  ← Pieza, Venta (sin IO)
├─────────────────────────────────────────┤
│         Database (Infraestructura)      │  ← Conexión y transacciones
└─────────────────────────────────────────┘
```

**Principio clave:** cada capa solo conoce a la capa inmediatamente inferior.  
La UI nunca toca la base de datos directamente; los repositorios nunca aplican reglas de negocio.

---

## ⚙️ Requisitos e Instalación

```bash
# 1. Clonar / descomprimir el proyecto
cd taller_v2

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Instalar dependencias
pip install pandas numpy matplotlib

# 4. Ejecutar
python main.py
```

**Dependencias:**

| Paquete      | Versión mín. | Uso                              |
|--------------|-------------|----------------------------------|
| Python       | 3.10        | f-strings, match, type hints     |
| pandas       | 1.5         | DataFrames para reportes         |
| numpy        | 1.23        | Cálculos vectorizados (KPIs)     |
| matplotlib   | 3.6         | Gráficos de barras, pie y línea  |
| tkinter      | built-in    | Interfaz gráfica                 |
| sqlite3      | built-in    | Base de datos local              |

---

## 🗄️ Esquema de Base de Datos

```sql
-- Inventario de piezas
CREATE TABLE inventario (
    id_pieza        TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    categoria       TEXT NOT NULL,
    cantidad        INTEGER NOT NULL CHECK(cantidad >= 0),
    precio_unitario REAL    NOT NULL CHECK(precio_unitario >= 0)
);

-- Registro de ventas / salidas
CREATE TABLE ventas (
    id_venta  TEXT PRIMARY KEY,          -- Ej: V3A1B2C3D
    id_pieza  TEXT NOT NULL,
    cantidad  INTEGER NOT NULL,
    total     REAL    NOT NULL,
    fecha     TEXT    NOT NULL,          -- ISO 8601: 2025-07-14T10:30:00
    FOREIGN KEY(id_pieza) REFERENCES inventario(id_pieza)
);
```

**Notas importantes:**
- La columna `cantidad` tiene `CHECK >= 0` a nivel DB (doble protección).
- El `upsert` en inventario **acumula** stock: si la pieza ya existe, suma la cantidad nueva al stock actual.
- Las ventas usan `FOREIGN KEY` con `PRAGMA foreign_keys = ON` para garantizar integridad referencial.

---

## 📦 Módulo: `domain/`

### `pieza.py`
Representa una pieza física del taller.

| Campo            | Tipo    | Descripción                          |
|-----------------|---------|--------------------------------------|
| `id_pieza`      | `str`   | Código único (ej: `RAM-DDR4-16G`)    |
| `nombre`        | `str`   | Nombre descriptivo                   |
| `categoria`     | `str`   | Grupo (Memoria, Disco, CPU, etc.)    |
| `cantidad`      | `int`   | Unidades en stock (≥ 0)              |
| `precio_unitario`| `float`| Precio por unidad (≥ 0)             |
| `valor_stock`   | `float` | **Propiedad calculada**: cant × precio|

### `venta.py`
Representa una transacción de salida de inventario.

| Campo       | Tipo       | Descripción                              |
|-------------|-----------|------------------------------------------|
| `id_venta`  | `str`      | UUID corto autogenerado (ej: `V3A1B2C3`) |
| `id_pieza`  | `str`      | Referencia a la pieza vendida            |
| `cantidad`  | `int`      | Unidades despachadas                     |
| `total`     | `float`    | Importe total de la venta                |
| `fecha`     | `datetime` | Marca de tiempo (auto: `datetime.now()`) |

---

## 🗃️ Módulo: `repositories/`

### `interfaces.py`
Define los **contratos abstractos** que cualquier implementación debe cumplir.  
Esto permite cambiar SQLite por PostgreSQL sin tocar servicios ni UI.

```python
class AbstractInventarioRepo(ABC):
    def upsert(self, pieza: Pieza) -> None: ...
    def get(self, id_pieza: str) -> Optional[Pieza]: ...
    def get_all(self) -> list[Pieza]: ...
    def restar_stock(self, id_pieza: str, cantidad: int) -> None: ...
    def buscar(self, query: str) -> list[Pieza]: ...          # NUEVO
    def get_stock_bajo(self, umbral: int) -> list[Pieza]: ... # NUEVO
```

### `inventario_repo.py`
Implementa `AbstractInventarioRepo` sobre SQLite con consultas parametrizadas.  
**Nunca concatena strings en SQL** → protección contra SQL injection.

### `ventas_repo.py`
Implementa `AbstractVentasRepo`.  
Usa `pd.read_sql_query` para cargar directamente a DataFrame con filtros opcionales de fecha.

---

## ⚙️ Módulo: `services/`

### `inventario_service.py`
Orquesta el repositorio de inventario y aplica reglas de negocio:
- Valida que precio ≥ 0 y cantidad ≥ 0 antes de persistir.
- Calcula `valor_total_inventario()` con `np.dot(cantidades, precios)`.
- Detecta piezas con stock bajo (`cantidad < umbral`).

### `ventas_service.py`
Orquesta inventario + ventas y aplica el flujo completo de una venta:
1. Verifica que la pieza exista.
2. Verifica stock suficiente.
3. Calcula el total con `np.multiply`.
4. Descuenta stock y persiste la venta en una sola operación lógica.
5. Calcula KPIs: total, transacciones, unidades, ticket promedio.

---

## 🖥️ Módulo: `ui/`

### `app.py`
- Configura la ventana raíz (`TallerApp(tk.Tk)`).
- Realiza la **inyección de dependencias**: crea repos → servicios → pasa a tabs.
- Expone `refresh()` global que actualiza todos los tabs.
- Mantiene el reloj en tiempo real en el header.

### Tabs disponibles

| Tab            | Archivo         | Función                                        |
|----------------|-----------------|------------------------------------------------|
| 📊 Dashboard   | `dashboard.py`  | KPI cards + gráfico de barras + pie chart      |
| 📦 Inventario  | `inventario.py` | CRUD de piezas + búsqueda en tiempo real       |
| 🛒 Salidas     | `ventas.py`     | Registrar salida de inventario + historial     |
| 📈 Reportes    | `reportes.py`   | Filtro por fecha + gráfico diario + resumen    |

---

## 🔒 Seguridad y Buenas Prácticas

| Práctica                  | Implementación                                               |
|---------------------------|--------------------------------------------------------------|
| SQL injection prevention  | Todas las queries usan `?` como placeholder parametrizado    |
| Integridad referencial    | `PRAGMA foreign_keys = ON` en cada conexión                  |
| Rollback automático       | `SQLiteConnection.__exit__` hace rollback si hay excepción   |
| Validación en dominio     | `Pieza.__post_init__` valida precio ≥ 0 y cantidad ≥ 0       |
| Validación en servicio    | `VentasService` verifica existencia y stock antes de vender  |
| Logging estructurado      | `logging.basicConfig` con nivel INFO y formato timestamp     |
| Sin hardcoding de rutas   | `DB_PATH = Path("taller_v2.db")` configurable en `config.py`|

---

## 📊 KPIs del Dashboard

| KPI               | Fórmula                                      | Color    |
|-------------------|----------------------------------------------|----------|
| Valor Inventario  | `Σ(cantidad × precio_unitario)`  — NumPy dot | 🟢 Verde |
| SKUs en Stock     | `COUNT(DISTINCT id_pieza)`                   | 🔵 Azul  |
| Ingresos Totales  | `Σ(total)` de todas las ventas               | 🟣 Morado|
| Transacciones     | `COUNT(id_venta)`                            | 🟡 Ámbar |
| Ticket Promedio   | `Σ(total) / COUNT(id_venta)`                 | 🔴 Rojo  |

---

## 🔄 Flujo de una Venta

```
UI (ventas.py)
  └─► VentasService.registrar_venta(id_pieza, cantidad)
        ├─► InventarioRepo.get(id_pieza)       → ¿existe?
        ├─► Pieza.cantidad >= cantidad          → ¿hay stock?
        ├─► total = np.multiply(cant, precio)
        ├─► InventarioRepo.restar_stock(...)   → UPDATE inventario
        └─► VentasRepo.insertar(venta)         → INSERT ventas
```

---

## 🚀 Extensibilidad

Para agregar una nueva base de datos (ej. PostgreSQL):
1. Crear `repositories/postgres_inventario_repo.py` implementando `AbstractInventarioRepo`.
2. En `ui/app.py`, reemplazar `SQLiteInventarioRepo(DB_PATH)` por `PostgresInventarioRepo(conn_str)`.
3. Cero cambios en servicios, dominio ni UI.

Para agregar un nuevo tab:
1. Crear `ui/mi_tab.py` con una clase que reciba los servicios necesarios.
2. Registrarlo en `ui/app.py` dentro de `_build_tabs()`.

---

## 📝 Convenciones de Código

- **Nombres en español** para dominio y UI (refleja el negocio real).
- **Type hints** en todas las funciones públicas.
- **Dataclasses** para entidades inmutables del dominio.
- **ABCs** para contratos de repositorio (patrón Strategy implícito).
- **Context managers** para todas las conexiones de base de datos.
- **`log.info/error`** en lugar de `print()` para trazabilidad.
