"""
db.py — Configuración central de SQLAlchemy para Persico Suite.

Patrón de datos elegido: cada colección se guarda en su propia tabla con
columnas indexadas para las búsquedas más comunes (año, cliente, job, etc.)
más una columna JSONB ("data") con el registro completo tal como vivía en
el JSON original. Esto evita rediseñar cada campo como columna separada
(riesgoso, dado que estas estructuras crecieron orgánicamente durante mucho
tiempo) mientras sí da los beneficios reales de una base de datos: sin
candado único global, índices, y transacciones ACID.

Ventas (Quote / CPO) ya fue migrado antes de este proyecto usando psycopg2
directo — se deja tal cual (ya está probado en producción) y aquí solo se
definen sus modelos SQLAlchemy en modo "espejo" para que el esquema quede
documentado y consultable de forma consistente con el resto.
"""
import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Railway a veces entrega la URL con el esquema viejo "postgres://" — SQLAlchemy
# 1.4+/2.x requiere "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

DB_ENABLED = bool(DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10) if DB_ENABLED else None
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False)) if DB_ENABLED else None
Base = declarative_base()


def now():
    return datetime.datetime.utcnow()


class JSONBMixin:
    """Columnas comunes a (casi) todas las tablas de este patrón."""
    id = Column(Integer, primary_key=True)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


# ══════════════════════════════════════════════════════════════════
#  VENTAS — modelos "espejo" (la app sigue usando psycopg2 directo para
#  estas dos tablas; se definen aquí solo para documentación de esquema
#  y para que Alembic las reconozca sin intentar recrearlas).
# ══════════════════════════════════════════════════════════════════
class Quote(Base, JSONBMixin):
    __tablename__ = "quotes"
    qnum = Column(String, unique=True)
    customer = Column(String, index=True)


class CPO(Base, JSONBMixin):
    __tablename__ = "cpos"
    cpo_id = Column(String, unique=True, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    job = Column(String, index=True)
    customer = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  JOBS
# ══════════════════════════════════════════════════════════════════
class Job(Base, JSONBMixin):
    __tablename__ = "jobs"
    job_number = Column(String, unique=True, nullable=False, index=True)
    customer = Column(String, index=True)
    status = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  COMPRAS
# ══════════════════════════════════════════════════════════════════
class HourlyRate(Base, JSONBMixin):
    __tablename__ = "hourly_rates"
    year = Column(Integer, nullable=False, index=True)
    employee = Column(String, index=True)


class PurchaseOrder(Base, JSONBMixin):
    __tablename__ = "purchase_orders"
    year = Column(Integer, nullable=False, index=True)
    po_number = Column(String, index=True)
    job = Column(String, index=True)


class InvoicedPO(Base, JSONBMixin):
    __tablename__ = "invoiced_pos"
    year = Column(Integer, nullable=False, index=True)
    job = Column(String, index=True)


class Proveedor(Base, JSONBMixin):
    __tablename__ = "proveedores"
    nombre = Column(String, index=True)


class GeneratedPO(Base, JSONBMixin):
    __tablename__ = "generated_pos"
    folio = Column(String, unique=True, index=True)


class CatalogoCompra(Base, JSONBMixin):
    """Unifica catalogo_electrico / catalogo_mecanico / catalogo_servicios
    (mismo formato, distinta 'familia')."""
    __tablename__ = "catalogos_compra"
    familia = Column(String, nullable=False, index=True)  # electrico | mecanico | servicios


# ══════════════════════════════════════════════════════════════════
#  WORK HOURS (la colección más grande — 4,253+ registros y creciendo)
# ══════════════════════════════════════════════════════════════════
class WorkHour(Base, JSONBMixin):
    __tablename__ = "work_hours"
    year = Column(Integer, nullable=False, index=True)
    employee = Column(String, index=True)
    job = Column(String, index=True)
    date_worked = Column(String, index=True)  # se guarda como texto AAAA-MM-DD, igual que en JSON


# ══════════════════════════════════════════════════════════════════
#  FX
# ══════════════════════════════════════════════════════════════════
class FXRate(Base, JSONBMixin):
    __tablename__ = "fx_rates"
    year = Column(Integer, nullable=False, index=True)
    fecha = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  PERSONAL / RRHH
# ══════════════════════════════════════════════════════════════════
class Personal(Base, JSONBMixin):
    __tablename__ = "personal"
    tid = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, index=True)
    area = Column(String, index=True)


class Area(Base, JSONBMixin):
    __tablename__ = "areas"
    nombre = Column(String, index=True)


class Perfil(Base, JSONBMixin):
    __tablename__ = "perfiles"
    pid = Column(String, unique=True, index=True)


class Vacacion(Base, JSONBMixin):
    __tablename__ = "vacaciones"
    tid = Column(String, unique=True, nullable=False, index=True)


class Permiso(Base, JSONBMixin):
    __tablename__ = "permisos"
    pid = Column(String, unique=True, index=True)
    tid = Column(String, index=True)
    estatus = Column(String, index=True)


class Sueldo(Base, JSONBMixin):
    __tablename__ = "sueldos"
    tid = Column(String, unique=True, nullable=False, index=True)


class IsrTabla(Base, JSONBMixin):
    __tablename__ = "isr_tablas"
    periodo = Column(String, unique=True, index=True)  # quincenal | mensual


class NominaPeriodo(Base, JSONBMixin):
    __tablename__ = "nomina_periodos"
    periodo_id = Column(String, unique=True, index=True)


class NominaRecibo(Base, JSONBMixin):
    __tablename__ = "nomina_recibos"
    recibo_id = Column(String, unique=True, index=True)
    periodo_id = Column(String, index=True)
    tid = Column(String, index=True)


class ControlHorasFirma(Base, JSONBMixin):
    __tablename__ = "control_horas_firmas"
    report_key = Column(String, index=True)


class ControlHorasExport(Base, JSONBMixin):
    __tablename__ = "control_horas_exports"
    report_key = Column(String, unique=True, index=True)


# ══════════════════════════════════════════════════════════════════
#  OPERACIONES
# ══════════════════════════════════════════════════════════════════
class Stock(Base, JSONBMixin):
    __tablename__ = "stock"
    job = Column(String, index=True)


class ReassignOrder(Base, JSONBMixin):
    __tablename__ = "reassign_orders"
    folio = Column(String, unique=True, index=True)


class Recovery(Base, JSONBMixin):
    __tablename__ = "recovery"
    job = Column(String, index=True)


class MovimientoStock(Base, JSONBMixin):
    __tablename__ = "movimientos_stock"
    job = Column(String, index=True)


class Capacidad(Base, JSONBMixin):
    __tablename__ = "capacidad"
    tid = Column(String, unique=True, index=True)


class CapacidadCodigo(Base, JSONBMixin):
    __tablename__ = "ops_capacidad_codigos"
    codigo = Column(String, unique=True, index=True)


class OrdenServicio(Base, JSONBMixin):
    __tablename__ = "ordenes_servicio"
    os_id = Column(String, unique=True, nullable=False, index=True)
    estatus = Column(String, index=True)


class TareaAsignada(Base, JSONBMixin):
    __tablename__ = "tareas_asignadas"
    ta_id = Column(String, unique=True, nullable=False, index=True)
    estatus = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  FINANZAS
# ══════════════════════════════════════════════════════════════════
class EsquemaTributario(Base, JSONBMixin):
    __tablename__ = "esquemas_tributarios"


class Recepcion(Base, JSONBMixin):
    __tablename__ = "recepciones"
    job = Column(String, index=True)


class ProcesarCompra(Base, JSONBMixin):
    __tablename__ = "procesar_compra"
    job = Column(String, index=True)


class CPP(Base, JSONBMixin):
    __tablename__ = "cpp"
    cpp_number = Column(String, unique=True, index=True)


class Pago(Base, JSONBMixin):
    __tablename__ = "pagos"
    folio = Column(String, unique=True, index=True)


class CPC(Base, JSONBMixin):
    __tablename__ = "cpc"
    year = Column(Integer, index=True)
    cpc_id = Column(String, unique=True, index=True)
    job = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PROYECTO
# ══════════════════════════════════════════════════════════════════
class ProjectConfig(Base, JSONBMixin):
    __tablename__ = "project_configs"
    job = Column(String, unique=True, nullable=False, index=True)


# ══════════════════════════════════════════════════════════════════
#  LOGÍSTICA / OTROS
# ══════════════════════════════════════════════════════════════════
class Ingreso(Base, JSONBMixin):
    __tablename__ = "ingresos"
    job = Column(String, index=True)


class Apartado(Base, JSONBMixin):
    __tablename__ = "apartados"
    job = Column(String, index=True)


class Salida(Base, JSONBMixin):
    __tablename__ = "salidas"
    job = Column(String, index=True)


class Viatico(Base, JSONBMixin):
    __tablename__ = "viaticos"
    job = Column(String, index=True)


class GastoViaje(Base, JSONBMixin):
    __tablename__ = "gastos_viaje"
    job = Column(String, index=True)


class Envio(Base, JSONBMixin):
    __tablename__ = "envios"
    job = Column(String, index=True)


# ══════════════════════════════════════════════════════════════════
#  SISTEMA
# ══════════════════════════════════════════════════════════════════
class User(Base, JSONBMixin):
    """Roles y permisos (users.json). Las contraseñas siguen en users_auth.json
    / UserAuth — se separan a propósito para no mezclar credenciales con
    configuración de permisos en la misma fila."""
    __tablename__ = "users"
    username = Column(String, unique=True, nullable=False, index=True)


class UserAuth(Base, JSONBMixin):
    __tablename__ = "users_auth"
    username = Column(String, unique=True, nullable=False, index=True)


class DocCounter(Base, JSONBMixin):
    __tablename__ = "doc_counters"
    prefix = Column(String, unique=True, nullable=False, index=True)


class PTNumber(Base, JSONBMixin):
    __tablename__ = "pt_numbers"
    pt_number = Column(String, unique=True, nullable=False, index=True)


class SVNumber(Base, JSONBMixin):
    __tablename__ = "sv_numbers"
    sv_number = Column(String, unique=True, nullable=False, index=True)


def init_db():
    """Crea todas las tablas que no existan. Nunca borra ni modifica una
    tabla existente (eso lo maneja Alembic vía migraciones versionadas)."""
    if not DB_ENABLED:
        print("  [DB] DATABASE_URL no configurada — el sistema sigue usando JSON.")
        return
    Base.metadata.create_all(bind=engine)
    print(f"  [DB] {len(Base.metadata.tables)} tablas verificadas/creadas en PostgreSQL.")


def get_session():
    return SessionLocal()
