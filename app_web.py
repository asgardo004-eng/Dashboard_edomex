import time
import pandas as pd
import streamlit as st

# Configuración de la página web
st.set_page_config(
    page_title="Consulta de Órdenes - Estado de México",
    page_icon="🏛️",
    layout="wide",
)


# Función de autenticación por contraseña usando Streamlit Secrets
def verificar_password():
  if "PASSWORD" not in st.secrets:
    st.error(
        "⚠️ Error de configuración: La contraseña no está definida en los"
        " Secrets de Streamlit."
    )
    return False

  if st.session_state.get("password_correct", False):
    return True

  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    st.markdown("## 🏛️ Gobierno del Estado de México")
    st.subheader("Acceso Restringido - Sistema de Órdenes")
    st.markdown("Por favor, introduce la contraseña de acceso autorizado.")

    with st.form("form_login"):
      input_password = st.text_input("Contraseña", type="password")
      submit_btn = st.form_submit_button("Entrar al Sistema", use_container_width=True)

      if submit_btn:
        if input_password == st.secrets["PASSWORD"]:
          st.session_state["password_correct"] = True
          st.rerun()
        else:
          st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")

  return False


if not verificar_password():
  st.stop()


# ==========================================
# CÓDIGO DEL TABLERO
# ==========================================

SHEET_ID = "1sAIQK7-26p6n2kF93JNpfoMXDzKwjOEo"


# SIN CACHÉ (ttl=0) y con parámetro dinámico para romper la caché de Google Sheets
@st.cache_data(ttl=0)
def cargar_datos():
  try:
    # Añadimos un timestamp dinámico para evitar que Google devuelva una versión vieja guardada en caché
    timestamp = int(time.time() // 15)  # Se actualiza cada 15 segundos
    url_dinamica = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx&t={timestamp}"
    )

    df = pd.read_excel(url_dinamica, engine="openpyxl", dtype=str)
    return df.fillna("")
  except Exception as e:
    st.error(
        f"No se pudo cargar el archivo desde Google Drive. Verifica los permisos"
        f" de lectura: {e}"
    )
    return pd.DataFrame()


# Título y encabezado institucional
st.title("🏛️ Gobierno del Estado de México")
st.subheader(
    "Sistema de Consulta y Monitoreo de Órdenes de Verificación (Solo Lectura)"
)
st.markdown("---")

# Botón en la barra lateral para limpiar la caché manualmente y forzar recarga fresca
if st.sidebar.button("🔄 Sincronizar / Refrescar Datos"):
  st.cache_data.clear()
  st.rerun()

# Carga de datos con enlace dinámico
df_ordenes = cargar_datos()

if df_ordenes.empty:
  st.warning(
      "⚠️ No se encontraron datos o el archivo en Google Drive está vacío/no"
      " es accesible."
  )
else:
  # Barra lateral de filtros para los usuarios
  st.sidebar.header("🔍 Filtros de Búsqueda")

  # 1. Filtro por Estatus
  if "Estatus Devolución" in df_ordenes.columns:
    opciones_estatus = [
        "TODOS"
    ] + sorted(df_ordenes["Estatus Devolución"].unique().tolist())
    filtro_estatus = st.sidebar.selectbox("Estatus de Devolución", opciones_estatus)
  else:
    filtro_estatus = "TODOS"

  # 2. Filtro por Jurisdicción
  if "Jurisdicción" in df_ordenes.columns:
    opciones_muni = ["TODOS"] + sorted(df_ordenes["Jurisdicción"].unique().tolist())
    filtro_muni = st.sidebar.selectbox("Jurisdicción", opciones_muni)
  else:
    filtro_muni = "TODOS"

  # 3. Buscador de texto libre
  busqueda_texto = st.sidebar.text_input(
      "Buscar por Clave, Establecimiento o Actividad:"
  )

  # Aplicar filtros
  df_filtrado = df_ordenes.copy()

  if filtro_estatus != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["Estatus Devolución"] == filtro_estatus]

  if filtro_muni != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["Jurisdicción"] == filtro_muni]

  if busqueda_texto:
    mask = (
        df_filtrado.astype(str)
        .apply(
            lambda row: row.str.lower()
            .str.contains(busqueda_texto.lower())
            .any(),
            axis=1,
        )
    )
    df_filtrado = df_filtrado[mask]

  # Métricas rápidas en la parte superior
  col1, col2, col3 = st.columns(3)
  total_registros = len(df_ordenes)
  pendientes = (
      len(df_ordenes[df_ordenes["Estatus Devolución"] == "Pendiente"])
      if "Estatus Devolución" in df_ordenes.columns
      else 0
  )
  devueltas = (
      len(df_ordenes[df_ordenes["Estatus Devolución"] == "Devuelta"])
      if "Estatus Devolución" in df_ordenes.columns
      else 0
  )

  col1.metric("Total de Órdenes", total_registros)
  col2.metric("Órdenes Pendientes", pendientes)
  col3.metric("Órdenes Devueltas", devueltas)

  st.markdown("### 📋 Listado de Órdenes Registradas")

  # Mostrar la tabla interactiva de solo lectura
  st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

  # Nota al pie
  st.info(
      "💡 **Nota:** Este apartado es exclusivamente de consulta en la nube"
      " (actualizado automáticamente)."
  )

  # Botón de cerrar sesión en la barra lateral
  st.sidebar.markdown("---")
  if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["password_correct"] = False
    st.rerun()
