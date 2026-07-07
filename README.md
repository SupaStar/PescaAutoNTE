# NTE Automatic Fishing Bot (AI Adaptive Edition)

Un bot de pesca automático avanzado con Interfaz Gráfica para el videojuego **Neverness to Everness (NTE)**. Utiliza procesamiento de imágenes con OpenCV y una red neuronal (o controlador PID adaptativo) para resolver el minijuego de pesca sin intervención humana.

---

## ✨ Características Principales

1. **Interfaz Gráfica y Calibración Visual:**
   No tienes que editar código. El bot cuenta con una ventana (`fishing_bot_gui.py`) que te permite **arrastrar y soltar rectángulos** sobre los elementos clave de la pantalla de tu juego para calibrarlo visualmente. Tu configuración se guarda para siempre en `config.json`.

2. **Detección de Picada Inteligente (A prueba de Día/Noche):**
   Vigila el botón de pesca en pantalla y realiza un escaneo de cuadrantes en base al centro de masa del icono blanco. Evita al 100% las falsas alarmas provocadas por reflejos en el agua o la iluminación del día.

3. **Autocierre de Pantalla de Victoria:**
   Cuando atrapas un pez (detecta que hay letras blancas en la zona inferior), el bot presiona `ESC` y automáticamente hace clic en una zona vacía de la pantalla para cerrar la ventana y lanzar la caña de nuevo al instante.

4. **Inteligencia Artificial Integrada:**
   Usa un sistema de control de impulsos que mueve el indicador (`A` y `D`) para mantenerlo siempre centrado dentro de la barra verde del minijuego. Puedes alternar entre un modo Adaptativo o cargar un modelo de red neuronal entrenado (`ai_neural_net.json`).

---

## 🛠️ Requisitos e Instalación

### Opción 1: Ejecutable Standalone (.exe) - RECOMENDADO
1. Descarga o ve a la carpeta `dist/`.
2. Ejecuta `PescaAuto.exe`.
3. ¡Listo! El ejecutable pedirá permisos de administrador automáticamente y no necesitas instalar Python ni librerías.

### Opción 2: Usar código fuente (Python)
1. Instala Python 3.x.
2. Instala las dependencias:
   ```bash
   pip install opencv-python numpy mss pydirectinput keyboard
   ```
3. Ejecuta **PowerShell o CMD como Administrador** (crítico para que el juego reconozca las teclas falsas).
4. Ejecuta la interfaz gráfica:
   ```bash
   python fishing_bot_gui.py
   ```

---

## 🚀 Cómo Usar el Bot

1. Abre **Neverness to Everness (NTE)** (recomiendo modo ventana o ventana sin bordes).
2. Abre el Bot (`PescaAuto.exe` o `python fishing_bot_gui.py`).
3. Da clic en **Test Crop & Calibration**.
   - Aparecerá una ventana con la foto de tu juego.
   - **Arrastra el rectángulo Naranja** al icono del anzuelo.
   - **Arrastra el rectángulo Verde** a la barra de progreso del minijuego.
   - **Arrastra el rectángulo Amarillo** a la zona baja central, donde aparece el texto "Pez atrapado" (o haz que abarque bastante zona inferior).
   - Haz clic en **Save Calibration**.
4. En el juego, pon a tu personaje frente al agua, listo para lanzar.
5. En el bot, presiona **Start Bot** (o la tecla `F9`).
   - El bot te dará **1 segundo exacto** para hacer clic dentro de la ventana del juego y darle enfoque.
6. ¡Suelta el teclado y ratón! El bot lanzará, pescará, ganará el minijuego, cerrará la ventana y repetirá.
7. Para pausar, presiona `F9`. Para cerrarlo, presiona `F10`.

---

## 📂 Archivos Importantes
- `PescaAuto.exe` - Ejecutable listo para usarse.
- `fishing_bot_gui.py` - Interfaz gráfica principal.
- `fishing_bot.py` - Motor de detección visual y máquina de estados.
- `adaptive_controller.py` - Motor del minijuego (PID Controller / Neural Net).
- `config.json` - Coordenadas visuales guardadas.
- `ai_neural_net.json` - Red neuronal (si está entrenada).
