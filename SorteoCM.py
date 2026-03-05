import streamlit as st
import pandas as pd
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Sorteo de Plazas Carlos Marx 1-3",
    layout="centered"
)

# -------------------------
# ESTILO
# -------------------------

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1000px;}
.card {background: white; padding: 1.8rem; border-radius: 10px; border: 1px solid #e5e7eb; margin-bottom: 1.5rem;}
.stButton>button {background-color: #111827; color: white; border-radius: 6px; height: 2.7em; font-weight: 500; border: none;}
.stButton>button:hover {background-color: #374151;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------

st.markdown("""
<div style="padding-bottom:1.5rem;border-bottom:1px solid #e5e7eb;margin-bottom:2rem;">
<h1 style="margin:0;">Sorteo de Plazas Carlos Marx 1-3</h1>
<p style="margin:0;color:#6b7280;">Alba Fons · 2026</p>
</div>
""", unsafe_allow_html=True)

# -------------------------
# ESTADO
# -------------------------

if "solicitantes" not in st.session_state:
    st.session_state.solicitantes = []

if "resultados" not in st.session_state:
    st.session_state.resultados = []

if "plazas_dobles_fisicas" not in st.session_state:
    st.session_state.plazas_dobles_fisicas = []

# -------------------------
# RANGOS
# -------------------------

RANGOS = {
    1: list(range(1, 27)) + [80, 81] + [94],
    2: list(range(27, 43)) + [79],
    3: [n for n in range(43, 53) if n != 43],
    4: list(range(53, 79)),
    5: list(range(82, 93)),
}

# NOMBRES PARA PDF
NOMBRES_RANGO = {
    1: "R",
    2: "B1",
    3: "B2",
    4: "S-2G",
    5: "S-2P"
}

# -------------------------
# FUNCIONES
# -------------------------

def generar_plazas():
    plazas = {}

    for rango, numeros in RANGOS.items():
        for n in numeros:

            tipo = "doble_fisica" if n in st.session_state.plazas_dobles_fisicas else "sencilla"

            plazas[n] = {
                "numero": n,
                "rango": rango,
                "tipo": tipo,
                "ocupada": False
            }

    return plazas


def asignar_plazas():

    solicitantes = st.session_state.solicitantes.copy()
    random.shuffle(solicitantes)

    plazas = generar_plazas()
    resultados = []

    for s in solicitantes:

        nombre = s["nombre"]
        tipo = s["tipo"]
        asignado = False

        if tipo == "sencilla":

            for plaza in plazas.values():
                if not plaza["ocupada"]:
                    plaza["ocupada"] = True

                    resultados.append({
                        "nombre": nombre,
                        "plazas": [plaza["numero"]],
                        "rango": plaza["rango"]
                    })

                    asignado = True
                    break

        elif tipo == "doble":

            # DOBLE FÍSICA
            for plaza in plazas.values():

                if plaza["tipo"] == "doble_fisica" and not plaza["ocupada"]:

                    plaza["ocupada"] = True

                    resultados.append({
                        "nombre": nombre,
                        "plazas": [plaza["numero"], plaza["numero"]],
                        "rango": plaza["rango"]
                    })

                    asignado = True
                    break

            # DOS CONSECUTIVAS
            if not asignado:

                for rango, numeros in RANGOS.items():

                    for i in range(len(numeros) - 1):

                        p1 = plazas[numeros[i]]
                        p2 = plazas[numeros[i + 1]]

                        if not p1["ocupada"] and not p2["ocupada"]:

                            p1["ocupada"] = True
                            p2["ocupada"] = True

                            resultados.append({
                                "nombre": nombre,
                                "plazas": [p1["numero"], p2["numero"]],
                                "rango": rango
                            })

                            asignado = True
                            break

                    if asignado:
                        break

        if not asignado:

            resultados.append({
                "nombre": nombre,
                "plazas": ["LISTA DE ESPERA"],
                "rango": None
            })

    return resultados


def exportar_pdf(resultados):

    buffer = BytesIO()

    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 770, "Resultados del Sorteo")

    c.setFont("Helvetica", 10)
    c.drawString(220, 755, datetime.now().strftime("%d/%m/%Y %H:%M"))

    # ordenar por rango
    ordenados = sorted(resultados, key=lambda x: (x["rango"] is None, x["rango"]))

    y = 730

    lista_espera = []

    for r in ordenados:

        if r["rango"] is None:
            lista_espera.append(r)
            continue

        plazas_text = ", ".join(str(p) for p in r["plazas"])

        rango_text = NOMBRES_RANGO.get(r["rango"], r["rango"])

        line = f"{r['nombre']}  →  {plazas_text} ({rango_text})"

        c.drawString(60, y, line)

        y -= 18

        if y < 60:
            c.showPage()
            y = 750

    if lista_espera:

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(60, y, "Lista de espera")
        y -= 20
        c.setFont("Helvetica", 11)

        for r in lista_espera:

            c.drawString(60, y, r["nombre"])

            y -= 18

            if y < 60:
                c.showPage()
                y = 750

    c.save()

    buffer.seek(0)

    return buffer


# -------------------------
# TABS
# -------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    ["Solicitantes", "Configuración", "Sorteo", "Exportar"]
)

# -------------------------
# SOLICITANTES
# -------------------------

with tab1:

    st.subheader("Añadir solicitante")

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre")

    with col2:
        tipo = st.selectbox("Tipo de plaza", ["sencilla", "doble"])

    if st.button("Añadir"):

        if nombre.strip():

            nombres_existentes = {s["nombre"].lower() for s in st.session_state.solicitantes}

            if nombre.strip().lower() in nombres_existentes:

                st.warning("Este participante ya está registrado")

            else:

                st.session_state.solicitantes.append({
                    "nombre": nombre.strip(),
                    "tipo": tipo
                })

                st.success("Solicitante añadido")

        else:
            st.warning("Introduce un nombre válido")

    st.subheader("Importar Excel")

    archivo = st.file_uploader("Subir archivo", type=["xlsx"])

    if archivo is not None:

        df = pd.read_excel(archivo)

        df.columns = df.columns.str.strip().str.lower()

        if not {"nombre", "tipo"}.issubset(df.columns):

            st.error("El archivo debe contener columnas 'nombre' y 'tipo'")

        else:

            df = df[["nombre", "tipo"]]

            df["nombre"] = df["nombre"].astype(str).str.strip()
            df["tipo"] = df["tipo"].astype(str).str.strip().str.lower()

            nombres_existentes = {s["nombre"].lower() for s in st.session_state.solicitantes}

            nuevos = []

            for _, row in df.iterrows():

                if row["nombre"].lower() not in nombres_existentes:

                    nuevos.append({
                        "nombre": row["nombre"],
                        "tipo": row["tipo"]
                    })

                    nombres_existentes.add(row["nombre"].lower())

            st.session_state.solicitantes.extend(nuevos)

            st.success(f"{len(nuevos)} participantes añadidos")

    st.subheader("Listado")

    if st.session_state.solicitantes:

        df = pd.DataFrame(st.session_state.solicitantes)

        st.dataframe(df)

        st.caption(f"Total participantes: {len(df)}")

# -------------------------
# CONFIGURACIÓN
# -------------------------

with tab2:

    st.subheader("Plazas dobles físicas")

    nuevas = []

    for rango, numeros in RANGOS.items():

        st.markdown(f"**Rango {rango}**")

        cols = st.columns(6)

        for i, numero in enumerate(numeros):

            col = cols[i % 6]

            with col:

                marcado = st.checkbox(
                    str(numero),
                    value=(numero in st.session_state.plazas_dobles_fisicas),
                    key=f"doble_{numero}"
                )

                if marcado:
                    nuevas.append(numero)

    st.session_state.plazas_dobles_fisicas = nuevas

# -------------------------
# SORTEO
# -------------------------

with tab3:

    if st.button("Ejecutar sorteo"):

        if not st.session_state.solicitantes:

            st.warning("No hay solicitantes")

        else:

            with st.spinner("Realizando sorteo..."):

                st.session_state.resultados = asignar_plazas()

            st.success("Sorteo realizado")

    if st.session_state.resultados:

        df = pd.DataFrame(st.session_state.resultados)

        df["plazas"] = df["plazas"].apply(lambda x: ", ".join(map(str, x)))

        st.dataframe(df)

# -------------------------
# EXPORTAR
# -------------------------

with tab4:

    if st.session_state.resultados:

        pdf = exportar_pdf(st.session_state.resultados)

        st.download_button(
            "Descargar PDF",
            pdf,
            "resultado_sorteo.pdf",
            "application/pdf"
        )

# -------------------------
# REINICIAR
# -------------------------

st.markdown("---")

if st.button("Reiniciar aplicación"):

    st.session_state.clear()

    st.rerun()
