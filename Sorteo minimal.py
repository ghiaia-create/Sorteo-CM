import streamlit as st
import pandas as pd
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

# -------------------------
# CONFIGURACIÓN PÁGINA
# -------------------------
st.set_page_config(
    page_title="Sistema de Sorteo de Plazas",
    layout="centered"
)

# -------------------------
# ESTILO MINIMALISTA
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
    <h1 style="margin:0;">Sistema de Sorteo de Plazas</h1>
    <p style="margin:0;color:#6b7280;">Gestión y asignación de plazas de bicicleta</p>
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
# RANGOS DE PLAZAS
# -------------------------
RANGOS = {
    1: list(range(1, 27)) + [80, 81],
    2: list(range(27, 43)) + [79],
    3: [n for n in range(43, 53) if n != 43],
    4: list(range(53, 79)),
    5: list(range(82, 93)),
    6: list(range(93, 110)),
}

# -------------------------
# FUNCIONES
# -------------------------
def generar_plazas():
    plazas = {}
    for rango, numeros in RANGOS.items():
        for n in numeros:
            tipo = "doble_fisica" if n in st.session_state.plazas_dobles_fisicas else "sencilla"
            plazas[n] = {"numero": n, "rango": rango, "tipo": tipo, "ocupada": False}
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
                    resultados.append({"nombre": nombre, "plazas":[plaza["numero"]], "rango": plaza["rango"]})
                    asignado = True
                    break

        elif tipo == "doble":
            # 1️⃣ Doble física
            for plaza in plazas.values():
                if plaza["tipo"] == "doble_fisica" and not plaza["ocupada"]:
                    plaza["ocupada"] = True
                    resultados.append({"nombre": nombre, "plazas":[plaza["numero"], plaza["numero"]], "rango": plaza["rango"]})
                    asignado = True
                    break

            # 2️⃣ Dos consecutivas
            if not asignado:
                for rango, numeros in RANGOS.items():
                    for i in range(len(numeros)-1):
                        p1 = plazas[numeros[i]]
                        p2 = plazas[numeros[i+1]]
                        if not p1["ocupada"] and not p2["ocupada"]:
                            p1["ocupada"] = True
                            p2["ocupada"] = True
                            resultados.append({"nombre": nombre, "plazas":[p1["numero"], p2["numero"]], "rango": rango})
                            asignado = True
                            break
                    if asignado: break

        if not asignado:
            resultados.append({"nombre": nombre, "plazas":["LISTA DE ESPERA"], "rango": None})

    return resultados

def exportar_pdf(resultados):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 770, "Resultados del Sorteo")
    c.setFont("Helvetica", 10)
    c.drawString(220, 755, datetime.now().strftime("%d/%m/%Y %H:%M"))

    y = 730
    c.setFont("Helvetica", 11)
    for r in resultados:
        plazas_text = ", ".join(str(p) for p in r["plazas"])
        rango_text = r["rango"] if r["rango"] else "-"
        line = f"{r['nombre']} | Plazas: {plazas_text} | Rango: {rango_text}"
        c.drawString(50, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    buffer.seek(0)
    return buffer

# -------------------------
# TABS
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Solicitantes", "Configuración", "Sorteo", "Exportar"])

# -------------------------
# TAB 1 - SOLICITANTES
# -------------------------
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Añadir solicitante manual")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre")
    with col2:
        tipo = st.selectbox("Tipo de plaza", ["sencilla","doble"])
    if st.button("Añadir"):
        if nombre.strip():
            nombres_existentes = {s["nombre"] for s in st.session_state.solicitantes}
            if nombre.strip() in nombres_existentes:
                st.warning("Este participante ya está registrado")
            else:
                st.session_state.solicitantes.append({"nombre": nombre.strip(), "tipo": tipo})
                st.success("Solicitante añadido correctamente")
        else:
            st.warning("Introduce un nombre válido")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Importar desde Excel")
    archivo = st.file_uploader("Subir archivo (.xlsx)", type=["xlsx"])
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            df.columns = df.columns.str.strip().str.lower()
            if not {"nombre","tipo"}.issubset(df.columns):
                st.error("El archivo debe contener 'nombre' y 'tipo'")
            else:
                df = df[["nombre","tipo"]]
                df["nombre"] = df["nombre"].astype(str).str.strip()
                df["tipo"] = df["tipo"].astype(str).str.strip().str.lower()
                if not df["tipo"].isin(["sencilla","doble"]).all():
                    st.error("La columna 'tipo' solo puede contener 'sencilla' o 'doble'")
                else:
                    registros = df.to_dict(orient="records")
                    nombres_existentes = {s["nombre"] for s in st.session_state.solicitantes}
                    nuevos = [r for r in registros if r["nombre"] not in nombres_existentes]
                    st.session_state.solicitantes.extend(nuevos)
                    st.success(f"{len(nuevos)} participantes añadidos, {len(registros)-len(nuevos)} duplicados ignorados.")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Listado actual")
    if st.session_state.solicitantes:
        df_actual = pd.DataFrame(st.session_state.solicitantes)
        st.dataframe(df_actual, use_container_width=True)
        st.caption(f"Total participantes: {len(df_actual)}")
    else:
        st.caption("No hay participantes registrados")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# TAB 2 - CONFIGURACIÓN PLAZAS DOBLES
# -------------------------
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Configurar plazas dobles físicas")
    nuevas_dobles = []
    for rango, numeros in RANGOS.items():
        st.markdown(f"**Rango {rango}**")
        cols = st.columns(6)
        for i, numero in enumerate(numeros):
            col = cols[i % 6]
            with col:
                marcado = st.checkbox(str(numero),
                    value=(numero in st.session_state.plazas_dobles_fisicas),
                    key=f"doble_{numero}")
                if marcado: nuevas_dobles.append(numero)
    st.session_state.plazas_dobles_fisicas = nuevas_dobles
    st.caption(f"Total plazas dobles físicas: {len(nuevas_dobles)}")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# TAB 3 - SORTEO
# -------------------------
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Realizar sorteo")
    if st.button("Ejecutar sorteo"):
        if not st.session_state.solicitantes:
            st.warning("No hay solicitantes registrados")
        else:
            with st.spinner("Procesando asignación..."):
                st.session_state.resultados = asignar_plazas()
            st.success("Sorteo realizado correctamente")
    if st.session_state.resultados:
        df_resultados = pd.DataFrame(st.session_state.resultados)
        df_resultados["plazas"] = df_resultados["plazas"].apply(lambda x: ", ".join(map(str,x)))
        st.dataframe(df_resultados, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# TAB 4 - EXPORTAR
# -------------------------
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Exportar resultados")
    if st.session_state.resultados:
        pdf_bytes = exportar_pdf(st.session_state.resultados)
        st.download_button("Descargar PDF", data=pdf_bytes, file_name="resultado_sorteo.pdf", mime="application/pdf")
    else:
        st.caption("No hay resultados disponibles")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# REINICIO
# -------------------------
st.markdown("---")
if st.button("Reiniciar aplicación"):
    st.session_state.clear()
    st.rerun()
