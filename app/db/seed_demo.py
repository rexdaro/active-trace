"""
Seed masivo de datos demo para presentación.
Correr: python -m app.db.seed_demo
"""
import asyncio, uuid, bcrypt, random
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_role import UserRole
from app.models.rbac import Role
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
from app.models.encuentro import InstanciaEncuentro, SlotEncuentro, EstadoInstancia
from app.models.coloquio import Evaluacion, ReservaEvaluacion, TipoEvaluacion, EstadoReserva
from app.models.tarea import Tarea, EstadoTarea
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.models.guardia import Guardia, EstadoGuardia
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion, CalificacionOrigen
from app.models.salario import SalarioBase, SalarioPlus
from app.models.liquidacion import Liquidacion, Factura


DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
HORARIOS = ["08:00-10:00", "10:15-12:15", "14:00-16:00", "16:15-18:15"]

CARRERAS = [
    ("Licenciatura en Administración", "LIC-ADM"),
    ("Ingeniería en Sistemas", "ING-SIS"),
    ("Contador Público", "CONT-PUB"),
]

MATERIAS_POR_CARRERA = {
    "LIC-ADM": ["Introducción a la Administración", "Marketing Digital", "Recursos Humanos",
                "Gestión Financiera", "Comercio Internacional", "Legislación Laboral",
                "Estadística Aplicada", "Planificación Estratégica"],
    "ING-SIS": ["Programación I", "Programación II", "Base de Datos",
                "Redes", "Ingeniería de Software", "Sistemas Operativos",
                "Inteligencia Artificial", "Seguridad Informática"],
    "CONT-PUB": ["Contabilidad Básica", "Contabilidad de Costos", "Impuestos I",
                 "Auditoría", "Matemática Financiera", "Derecho Comercial",
                 "Práctica Profesional", "Análisis de Estados Contables"],
}

ALUMNOS = [
    ("Lucía","García"),("Mateo","Rodríguez"),("Valentina","López"),
    ("Santiago","Martínez"),("Camila","Fernández"),("Benjamín","González"),
    ("Isabella","Pérez"),("Sebastián","Sánchez"),("Emilia","Ramírez"),
    ("Joaquín","Torres"),("Martina","Flores"),("Lucas","Rivera"),
    ("Catalina","Díaz"),("Facundo","Moreno"),("Julieta","Álvarez"),
    ("Nicolás","Sosa"),("Sofía","Acosta"),("Tomás","Medina"),
    ("Agustina","Herrera"),("Matías","Castro"),
]

PROFESORES = [
    ("Ricardo","Méndez",["PROFESOR","COORDINADOR"]),
    ("Gabriela","Linares",["PROFESOR"]),
    ("Héctor","Rivas",["PROFESOR"]),
    ("Verónica","Paredes",["PROFESOR","TUTOR"]),
    ("Fernando","Álvarez",["PROFESOR"]),
    ("Andrea","Benítez",["PROFESOR"]),
    ("Pablo","Castillo",["TUTOR"]),
    ("María","Luna",["PROFESOR"]),
]

AVISOS_TITLES = [
    ("📢 Inicio de clases 2026", "Las clases comenzarán el 15 de marzo. Los horarios ya están disponibles.", AlcanceAviso.GLOBAL, SeveridadAviso.INFO),
    ("⚠️ Cierre de inscripciones", "La inscripción cierra el 28 de febrero. Regularizá tu situación.", AlcanceAviso.GLOBAL, SeveridadAviso.ADVERTENCIA),
    ("📝 Fechas de parciales", "Los parciales del primer cuatrimestre están publicados en el calendario.", AlcanceAviso.GLOBAL, SeveridadAviso.INFO),
    ("🔴 Cierre de actas", "El cierre de actas anteriores vence el 10 de marzo. Regularizar.", AlcanceAviso.GLOBAL, SeveridadAviso.CRITICO),
    ("📄 Becas 2026", "Formulario de becas disponible hasta el 31 de marzo.", AlcanceAviso.GLOBAL, SeveridadAviso.INFO),
    ("👩‍🏫 Capacitación docente", "Jornada de capacitación el 5 de marzo. Obligatoria.", AlcanceAviso.POR_ROL, SeveridadAviso.INFO),
    ("📚 Biblioteca virtual", "Nuevo acceso a la biblioteca virtual disponible para todos.", AlcanceAviso.GLOBAL, SeveridadAviso.INFO),
    ("🎓 Charla informativa", "Charla sobre salida laboral el 20 de marzo. Abierta a todos.", AlcanceAviso.GLOBAL, SeveridadAviso.INFO),
]

TAREAS = [
    "Corregir trabajos prácticos de la Comisión A",
    "Preparar material para la clase del jueves",
    "Actualizar el aula virtual con calificaciones",
    "Revisar entregas pendientes en el sistema",
    "Completar planilla de seguimiento de alumnos",
    "Subir bibliografía actualizada al campus",
    "Preparar enunciado del trabajo final",
    "Enviar informe de alumnos atrasados",
    "Organizar reunión de padres",
    "Revisar programa de la materia",
]

COM_ASUNTOS = [
    "Resultados del parcial",
    "Recordatorio de entrega de TP",
    "Clase de consulta adicional",
    "Material de lectura obligatoria",
    "Cambio de fecha de examen",
    "Consulta sobre trabajos prácticos",
    "Recordatorio: clase del jueves",
    "Invitación a taller extracurricular",
]


async def seed():
    async with AsyncSessionLocal() as s:
        print("🚀 Cargando datos demo masivos...\n")

        tenant = (await s.execute(select(Tenant).limit(1))).scalar_one()
        roles_map = {r.name: r for r in (await s.execute(select(Role))).scalars().all()}
        # Get admin user - verify it exists
        admin_result = await s.execute(select(User).where(User.email == "admin@activia-trace.com"))
        admin = admin_result.scalar_one()
        admin_id = admin.id
        print(f"   Admin ID: {admin_id}")
        now = datetime.utcnow()

        # =========== CARRERAS ===========
        carrera_map = {}
        for name, code in CARRERAS:
            c = Carrera(id=uuid.uuid4(), name=name, code=code, tenant_id=tenant.id)
            s.add(c)
            carrera_map[code] = c
        await s.flush()
        print(f"✅ {len(CARRERAS)} carreras")

        # =========== COHORTES ===========
        cohorte_map = {}
        for code, c in carrera_map.items():
            for anio in [2025, 2026]:
                coh = Cohorte(id=uuid.uuid4(), carrera_id=c.id, name=str(anio), tenant_id=tenant.id)
                s.add(coh)
                cohorte_map[(code, anio)] = coh
        await s.flush()
        print(f"✅ {len(cohorte_map)} cohortes")

        # =========== MATERIAS ===========
        materia_map = {}
        for code, mats in MATERIAS_POR_CARRERA.items():
            for i, mat_name in enumerate(mats):
                m = Materia(id=uuid.uuid4(), name=mat_name, code=f"{code}-{i+1:02d}", tenant_id=tenant.id)
                s.add(m)
                materia_map[(code, i)] = m
        await s.flush()
        print(f"✅ {len(materia_map)} materias")

        # =========== PROFESORES ===========
        profes = []
        for nombre, apellido, roles_list in PROFESORES:
            email = f"{nombre.lower()}.{apellido.lower()}@trace.com"
            u = User(
                id=uuid.uuid4(), email=email, nombre=f"{nombre} {apellido}",
                hashed_password=bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode(),
                tenant_id=tenant.id, activo=True,
                dni=str(random.randint(10000000, 99999999)),
                cuil=f"20-{random.randint(10000000, 99999999)}-9",
            )
            s.add(u)
            await s.flush()
            for rn in roles_list:
                rol = roles_map.get(rn)
                if rol:
                    s.add(UserRole(user_id=u.id, role_id=rol.id))
            profes.append(u)
        await s.flush()
        print(f"✅ {len(profes)} profesores/tutores")

        # =========== ALUMNOS ===========
        alumno_rol = roles_map["ALUMNO"]
        alumnos = []
        for nombre, apellido in ALUMNOS:
            email = f"{nombre.lower()}.{apellido.lower()}@alumno.trace.com"
            u = User(
                id=uuid.uuid4(), email=email, nombre=f"{nombre} {apellido}",
                hashed_password=bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode(),
                tenant_id=tenant.id, activo=True,
                dni=str(random.randint(10000000, 99999999)),
            )
            s.add(u)
            await s.flush()
            s.add(UserRole(user_id=u.id, role_id=alumno_rol.id))
            alumnos.append(u)
        await s.flush()
        print(f"✅ {len(alumnos)} alumnos")

        # =========== EQUIPOS DOCENTES COMPLETOS ===========
        eq_count = 0
        for (code, i), m in materia_map.items():
            # 1 profesor por materia
            prof = random.choice(profes)
            s.add(Asignacion(
                id=uuid.uuid4(), user_id=prof.id,
                role_id=roles_map["PROFESOR"].id,
                contexto_id=m.id, responsable_id=admin.id,
                desde=datetime(2025, 3, 1), tenant_id=tenant.id,
            ))
            eq_count += 1
            # 1-2 tutores por materia
            for _ in range(random.randint(1, 2)):
                tutor = random.choice([p for p in profes if p.id != prof.id])
                s.add(Asignacion(
                    id=uuid.uuid4(), user_id=tutor.id,
                    role_id=roles_map["TUTOR"].id,
                    contexto_id=m.id, responsable_id=admin.id,
                    desde=datetime(2025, 3, 1), tenant_id=tenant.id,
                ))
                eq_count += 1
        await s.flush()
        print(f"✅ {eq_count} asignaciones (equipos docentes completos)")

        # =========== SALARIOS BASE ===========
        salarios_base_data = [
            ("PROFESOR",  Decimal("850000.00"), date(2026, 1, 1), None),
            ("TUTOR",     Decimal("450000.00"), date(2026, 1, 1), None),
            ("COORDINADOR", Decimal("950000.00"), date(2026, 1, 1), None),
            ("NEXO",      Decimal("600000.00"), date(2026, 1, 1), None),
        ]
        for rol, monto, desde, hasta in salarios_base_data:
            s.add(SalarioBase(id=uuid.uuid4(), rol=rol, monto=monto, desde=desde, hasta=hasta, tenant_id=tenant.id))
        await s.flush()
        print(f"✅ {len(salarios_base_data)} salarios base")

        # =========== SALARIOS PLUS ===========
        salarios_plus_data = [
            ("Antigüedad",     "PROFESOR",  "Plus por 5+ años antigüedad",       Decimal("120000.00")),
            ("Antigüedad",     "TUTOR",     "Plus por 5+ años antigüedad",       Decimal("80000.00")),
            ("Responsabilidad","PROFESOR",  "Plus por responsable de cátedra",    Decimal("150000.00")),
            ("Capacitación",   "PROFESOR",  "Plus por capacitación continua",     Decimal("60000.00")),
            ("Capacitación",   "TUTOR",     "Plus por capacitación continua",     Decimal("40000.00")),
        ]
        for grupo, rol, desc, monto in salarios_plus_data:
            s.add(SalarioPlus(id=uuid.uuid4(), grupo=grupo, rol=rol, descripcion=desc, monto=monto,
                              desde=date(2026, 1, 1), tenant_id=tenant.id))
        await s.flush()
        print(f"✅ {len(salarios_plus_data)} salarios plus")

        # =========== PADRON + CALIFICACIONES ===========
        calif_count = 0
        for (code, i), m in list(materia_map.items())[:10]:
            coh = cohorte_map[(code, 2026)]
            v = VersionPadron(
                id=uuid.uuid4(), materia_id=m.id, cohorte_id=coh.id,
                archivo_nombre="demo.csv", archivo_hash="demo",
                origen="csv", cargado_por=admin.id, activa=True,
                tenant_id=tenant.id,
            )
            s.add(v)
            await s.flush()
            for alumno in random.sample(alumnos, k=min(8, len(alumnos))):
                ep = EntradaPadron(
                    id=uuid.uuid4(), version_id=v.id, usuario_id=alumno.id,
                    nombre=alumno.nombre or "", apellidos="Apellido",
                    _email=alumno.email, comision=random.choice(["Com A","Com B","Com C"]),
                    regional="CABA", tenant_id=tenant.id,
                )
                s.add(ep)
                await s.flush()

                for act in ["TP1", "TP2", "Parcial 1"]:
                    nota = round(random.uniform(3.0, 9.5), 2)
                    s.add(Calificacion(
                        id=uuid.uuid4(), entrada_padron_id=ep.id,
                        materia_id=m.id, actividad=act,
                        nota_numerica=nota, aprobado=nota >= 6,
                        origen=CalificacionOrigen.IMPORTADO.value,
                        importado_por=random.choice(profes).id,
                        importado_at=now - timedelta(days=random.randint(1, 60)),
                        tenant_id=tenant.id,
                    ))
                    calif_count += 1
        await s.flush()
        print(f"✅ {calif_count} calificaciones")

        # =========== AVISOS ===========
        for titulo, cuerpo, alcance, severidad in AVISOS_TITLES:
            s.add(Aviso(
                id=uuid.uuid4(), alcance=alcance.value, titulo=titulo, cuerpo=cuerpo,
                severidad=severidad.value,
                inicio_en=now - timedelta(days=5), fin_en=now + timedelta(days=60),
                orden=0, activo=True, requiere_ack=random.choice([True, False]),
                tenant_id=tenant.id,
                rol_destino="PROFESOR" if alcance == AlcanceAviso.POR_ROL else None,
            ))
        await s.flush()
        print(f"✅ {len(AVISOS_TITLES)} avisos")

        # =========== ENCUENTROS ===========
        slot_count = 0
        for (code, i), m in list(materia_map.items())[:6]:
            for turno in range(2):
                prof = random.choice(profes)
                s.add(SlotEncuentro(
                    id=uuid.uuid4(), materia_id=m.id, creado_por=prof.id,
                    dia_semana=random.choice(DIAS), horario=random.choice(HORARIOS),
                    titulo=f"{m.name} - Turno {turno+1}",
                    fecha_inicio=date(2026, 3, 15), cant_semanas=16, activo=True,
                    tenant_id=tenant.id,
                ))
                slot_count += 1
        await s.flush()

        slots = (await s.execute(select(SlotEncuentro).limit(30))).scalars().all()
        inst_count = 0
        for slot in slots:
            for sem in range(4):
                s.add(InstanciaEncuentro(
                    id=uuid.uuid4(), slot_id=slot.id, materia_id=slot.materia_id,
                    fecha=date(2026, 3, 15) + timedelta(weeks=sem), hora=slot.horario,
                    titulo=slot.titulo, estado=EstadoInstancia.REALIZADO.value if sem < 2 else EstadoInstancia.PROGRAMADO.value,
                    tenant_id=tenant.id,
                ))
                inst_count += 1
        await s.flush()
        print(f"✅ {slot_count} slots + {inst_count} instancias")

        # =========== TAREAS ===========
        all_materias = list(materia_map.values())
        for desc in TAREAS:
            prof = random.choice(profes)
            target = random.choice([p for p in profes if p.id != prof.id])
            s.add(Tarea(
                id=uuid.uuid4(), materia_id=random.choice(all_materias[:6]).id,
                asignado_a=target.id, asignado_por=prof.id,
                estado=random.choice([e.value for e in EstadoTarea]),
                descripcion=desc, tenant_id=tenant.id,
            ))
        await s.flush()
        print(f"✅ {len(TAREAS)} tareas")

        # =========== COLOQUIOS ===========
        evals_ok = 0
        res_ok = 0
        for (code, i), m in list(materia_map.items())[:4]:
            coh = cohorte_map[(code, 2026)]
            for tipo in [TipoEvaluacion.PARCIAL, TipoEvaluacion.COLOQUIO]:
                e = Evaluacion(
                    id=uuid.uuid4(), materia_id=m.id, cohorte_id=coh.id,
                    tipo=tipo.value, instancia=f"{tipo.value} 2026",
                    cupos_por_dia=15, tenant_id=tenant.id,
                )
                s.add(e)
                await s.flush()
                evals_ok += 1
                for alumno in random.sample(alumnos, k=min(5, len(alumnos))):
                    s.add(ReservaEvaluacion(
                        id=uuid.uuid4(), evaluacion_id=e.id, alumno_id=alumno.id,
                        fecha_hora=now + timedelta(days=random.randint(7, 60)),
                        estado=random.choice(["Activa", "Cancelada"]),
                        tenant_id=tenant.id,
                    ))
                    res_ok += 1
        await s.flush()
        print(f"✅ {evals_ok} evaluaciones + {res_ok} reservas")

        # =========== COMUNICACIONES ===========
        lote_a = uuid.uuid4()
        lote_b = uuid.uuid4()
        for i, asunto in enumerate(COM_ASUNTOS):
            prof = random.choice(profes)
            m = random.choice(all_materias[:6])
            s.add(Comunicacion(
                id=uuid.uuid4(), enviado_por=prof.id, materia_id=m.id,
                _destinatario=f"alumnos-{m.code}@trace.com",
                asunto=asunto,
                cuerpo="Mensaje generado con datos demo para la presentación del sistema.",
                estado=random.choice([e.value for e in ComunicacionEstado]),
                lote_id=lote_a if i < 4 else lote_b,
                lote_aprobado=True,
                enviado_at=now - timedelta(days=random.randint(1, 15)),
                tenant_id=tenant.id,
            ))
        await s.flush()
        print(f"✅ {len(COM_ASUNTOS)} comunicaciones")

        # =========== LIQUIDACIONES ===========
        all_cohortes = list(cohorte_map.values())
        liq_count = 0
        monto_base_prof = Decimal("850000.00")
        for prof in profes[:6]:
            for mes in range(1, 5):
                coh = random.choice(all_cohortes)
                monto_base = monto_base_prof
                monto_plus = Decimal(random.choice([0, 60000, 120000, 150000]))
                total = monto_base + monto_plus
                s.add(Liquidacion(
                    id=uuid.uuid4(), cohorte_id=coh.id, periodo=f"2026-{mes:02d}",
                    usuario_id=prof.id, rol="PROFESOR",
                    comisiones=f"Comisión A, Comisión B",
                    monto_base=monto_base, monto_plus=monto_plus, total=total,
                    es_nexo=False, excluido_por_factura=False,
                    estado=random.choice(["Abierta", "Cerrada"]),
                    tenant_id=tenant.id,
                ))
                liq_count += 1
        await s.flush()
        print(f"✅ {liq_count} liquidaciones")

        # =========== FACTURAS ===========
        fact_count = 0
        for prof in profes[:4]:
            for mes in range(1, 4):
                monto = Decimal(random.uniform(400000.0, 900000.0))
                abonada = random.random() < 0.5
                s.add(Factura(
                    id=uuid.uuid4(), usuario_id=prof.id, periodo=f"2026-{mes:02d}",
                    detalle=f"Honorarios {mes}/2026 - {prof.nombre}",
                    fecha=date(2026, mes, 15),
                    monto=monto,
                    referencia_archivo=f"factura_{prof.nombre.lower().split()[0]}_{mes}.pdf",
                    tamano_kb=Decimal(random.randint(50, 500)),
                    estado="Abonada" if abonada else "Pendiente",
                    abonada_at=now - timedelta(days=random.randint(5, 45)) if abonada else None,
                    tenant_id=tenant.id,
                ))
                fact_count += 1
        await s.flush()
        print(f"✅ {fact_count} facturas")

        # =========== GUARDIAS ===========
        for i in range(6):
            prof = random.choice(profes)
            m = random.choice(all_materias[:6])
            carrera_code = random.choice(list(carrera_map.keys()))
            carrera = carrera_map[carrera_code]
            coh = cohorte_map[(carrera_code, 2026)]
            asig = Asignacion(
                id=uuid.uuid4(), user_id=prof.id, role_id=roles_map["TUTOR"].id,
                contexto_id=m.id, responsable_id=admin.id,
                desde=datetime(2025, 3, 1), tenant_id=tenant.id,
            )
            s.add(asig)
            await s.flush()
            s.add(Guardia(
                id=uuid.uuid4(), asignacion_id=asig.id,
                materia_id=m.id, carrera_id=carrera.id,
                cohorte_id=coh.id, dia=random.choice(DIAS),
                horario=random.choice(HORARIOS),
                estado=random.choice([e.value for e in EstadoGuardia]),
                tenant_id=tenant.id,
            ))
        await s.flush()
        print(f"✅ 6 guardias")

        await s.commit()

        total_users = len((await s.execute(select(User))).scalars().all())
        print(f"\n{'='*50}")
        print(f"  ✅✅✅ SEED DEMO COMPLETO ✅✅✅")
        print(f"{'='*50}")
        print(f"  Total usuarios: {total_users}")
        print(f"  Admin:            admin@activia-trace.com  / admin123")
        print(f"  Alumnos:          *@alumno.trace.com        / demo123")
        print(f"  Profesores:       *@trace.com               / demo123")
        print(f"{'='*50}")
        print(f"\n  📊 Resumen:")
        print(f"     {len(CARRERAS)} carreras, {len(cohorte_map)} cohortes, {len(materia_map)} materias")
        print(f"     {len(profes)} docentes, {len(alumnos)} alumnos")
        print(f"     {calif_count} calificaciones, {len(AVISOS_TITLES)} avisos")
        print(f"     {slot_count} slots, {inst_count} instancias encuentro")
        print(f"     {evals_ok} evaluaciones, {res_ok} reservas")
        print(f"     {len(TAREAS)} tareas, {len(COM_ASUNTOS)} comunicaciones")
        print(f"     {liq_count} liquidaciones, {fact_count} facturas, {len(salarios_base_data)} salarios base, {len(salarios_plus_data)} salarios plus")
        print(f"     {eq_count} asignaciones (equipos docentes)")


if __name__ == "__main__":
    asyncio.run(seed())
