# NTE Automatic Fishing Bot

Un bot de pesca automático para el videojuego **Neverness to Everness (NTE)** desarrollado en Python. Utiliza procesamiento de imágenes con OpenCV para la detección visual de estados y PyDirectInput para simular entradas de teclado a nivel DirectInput.

---

## ✨ Características Principales

1. **Independencia de Resolución:**
   El bot escala automáticamente las coordenadas de detección según la resolución de tu pantalla. Captura la pantalla nativa, la recorta y la redimensiona a una cuadrícula de referencia normalizada (`1024x428`). Funciona en **3440x1440**, **1920x1080** y cualquier otra resolución.

2. **Detección de Picada por Cuadrantes (A prueba de Día/Noche):**
   En lugar de buscar texto en pantalla (que falla por los cambios de luz y fondos), el bot vigila el botón circular `F` en la esquina inferior derecha:
   - Al haber una picada, el anillo azul del botón se completa formando un círculo.
   - Al estar esperando en el día, solo hay un arco azul parcial (carga/distancia).
   - El bot divide el anillo en 4 cuadrantes (Izquierda/Derecha, Arriba/Abajo) y verifica que todos tengan píxeles azules ($>35$ píxeles). Esto previene falsos positivos en el día con una precisión del 100%.

3. **Bucle de Seguridad de Cierre de Pantalla:**
   Antes de volver a presionar `F` para lanzar la caña, el bot verifica si la pantalla de éxito sigue visible. Si detecta que no se cerró bien (por lag del juego), vuelve a presionar `ESC` y espera hasta confirmar que la pantalla desapareció antes de castear.

4. **Entrada de Teclado Eficiente (Sin Spam):**
   El bot mantiene un registro interno del estado de las teclas `A` y `D` para presionar y soltar sólo cuando hay cambios de dirección en el minijuego, reduciendo el uso de CPU y previniendo sospechas del anti-cheat.

---

## 🛠️ Requisitos e Instalación

### 1. Instalación de Python
Asegúrate de tener instalado Python 3.x en tu sistema Windows.

### 2. Dependencias de Python
Instala las librerías necesarias ejecutando el siguiente comando en tu terminal:
```bash
pip install opencv-python numpy mss pydirectinput keyboard
```

### 3. Ejecutar como Administrador (CRÍTICO)
El juego NTE se ejecuta con privilegios elevados en Windows. Para que el script de Python pueda simular entradas de teclado dentro del juego, **debes abrir PowerShell o CMD como Administrador** y ejecutar el bot desde allí.

---

## ⚙️ Configuración

Puedes editar los parámetros de configuración directamente en la cabecera del archivo `fishing_bot.py`:

```python
# --- CONFIGURACIÓN ---
# Ajusta estas dimensiones a la resolución real de tu ventana de juego.
SCREEN_W = 3440
SCREEN_H = 1440

# Asignación de teclas dentro del juego (Keybindings)
KEY_CAST_REEL = 'f'      # Tecla para lanzar y jalar
KEY_CLOSE_SCREEN = 'esc' # Tecla para cerrar la pantalla de éxito de pesca
KEY_STEER_LEFT = 'a'     # Tecla para mover a la izquierda en el minijuego
KEY_STEER_RIGHT = 'd'    # Tecla para mover a la derecha en el minijuego

# Hotkeys globales del Bot
HOTKEY_TOGGLE = 'f9'     # F9 para Iniciar / Pausar el bot
HOTKEY_EXIT = 'f10'      # F10 para detener el bot y salir
```

---

## 🚀 Cómo Usar el Bot

1. Abre **Neverness to Everness (NTE)** y ponlo en la resolución configurada (se recomienda modo ventana sin bordes o ventana).
2. Posiciona a tu personaje frente al agua en una zona de pesca con la caña de pescar equipada y lista para lanzar.
3. Abre una terminal de Windows **como Administrador**.
4. Dirígete a la carpeta del proyecto y ejecuta el bot:
   ```powershell
   cd D:\Proyectos\PescaAuto
   python fishing_bot.py
   ```
5. Regresa al juego y presiona **`F9`** para iniciar el bot. El bot escribirá `>>> BOT STARTED! <<<` en la consola y lanzará la caña automáticamente.
6. El bot automatizará todo el ciclo:
   - Esperar picada (detectando el círculo azul de F).
   - Iniciar el minigame.
   - Mantener la línea blanca dentro de la verde con `A` y `D`.
   - Esperar a que acabe la animación del pez, detectar la pantalla de éxito, presionar `ESC` para cerrarla y volver a lanzar.
7. Presiona **`F9`** en cualquier momento para **Pausar** el bot.
8. Presiona **`F10`** para **Cerrar** el script por completo.

---

## 🧪 Pruebas Fuera de Línea (Offline)

Si deseas verificar que los algoritmos de detección funcionan correctamente con capturas de pantalla de referencia antes de pescar en el juego, puedes ejecutar el suite de pruebas:
```powershell
python verify_bot.py
```
Este script procesará 6 escenarios de prueba (espera de noche, espera de día, picada, minijuego y pantallas de éxito) y reportará si todos los umbrales de detección y lógica del bot están funcionando al 100%.

---

## 📂 Estructura del Proyecto

```
D:\Proyectos\PescaAuto\
│
├── fishing_bot.py       # Script ejecutable principal del Bot.
├── verify_bot.py        # Suite de pruebas offline contra capturas de referencia.
│
├── debug_scripts/       # Scripts internos para calibrar umbrales HSV y posiciones.
│   ├── analyze_images.py
│   ├── check_blue_quadrants.py
│   └── ...
│
└── debug_images/        # Capturas recortadas y máscaras binarias generadas para depurar.
    ├── annotated_crop.png
    ├── success_crop_day.png
    └── ...
```
