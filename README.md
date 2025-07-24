# Consulta Automatizada de Antecedentes Judiciales (Colombia)

Este proyecto automatiza la consulta de antecedentes judiciales en el sitio oficial de la Policía Nacional de Colombia, resolviendo el reCAPTCHA de manera automática (usando 2Captcha) o manual si es necesario. El resultado se guarda como PDF y los errores se documentan con capturas de pantalla.

## ¿Por qué existe este script?

Automatizar la obtención de certificados de antecedentes judiciales puede ahorrar tiempo y evitar errores manuales, especialmente en procesos repetitivos o de alto volumen. Este script está pensado para ser usado en entornos donde se requiere consultar múltiples cédulas de manera eficiente y trazable.

## Dominio y Arquitectura

- **Dominio:** Legal, automatización de trámites públicos en Colombia.
- **Tipo de aplicación:** Script Python standalone (no web, no microservicio).
- **Integraciones:**
  - API de 2Captcha para resolver reCAPTCHA.
  - Navegación web automatizada con Selenium y undetected-chromedriver.
  - Variables de entorno para configuración segura.

## Requisitos

- Python 3.8+
- Google Chrome instalado
- Dependencias listadas en `requirements.txt`
- Cuenta y API Key de [2Captcha](https://2captcha.com/)

## Instalación

1. **Clona el repositorio y entra al directorio:**
   ```bash
   git clone <repo_url>
   cd <repo_dir>
   ```
2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configura las variables de entorno:**
   - Copia el archivo de ejemplo:
     ```bash
     cp env.example .env
     ```
   - Edita `.env` y coloca tu API Key de 2Captcha:
     ```
     API_KEY_2CAPTCHA=tu_api_key_aqui
     ```

## Uso

1. **Edita el archivo `main.py`** y cambia la variable `numero_de_cedula` al número de cédula que deseas consultar:
   ```python
   if __name__ == "__main__":
       numero_de_cedula = "1001298785"  # Cambia este valor
       consultar_antecedentes(numero_de_cedula)
   ```
2. **Ejecuta el script:**
   ```bash
   python main.py
   ```
3. **Resultado:**
   - El PDF generado se guardará en la carpeta `antecedentes/` con el nombre `antecedentes_<cedula>.pdf`.
   - Si ocurre un error, se guardará una captura de pantalla en la carpeta `errors/`.

## Estrategia de Manejo de Errores

- **Validaciones de entrada:** El script espera un número de cédula válido (solo números).
- **Errores de red, CAPTCHA o página:**
  - Reintenta automáticamente hasta 2 veces si el flujo falla.
  - Si el CAPTCHA no puede resolverse automáticamente, solicita intervención manual.
- **Logging:**
  - Todos los eventos importantes y errores se registran en consola con nivel INFO o ERROR.
  - Capturas de pantalla de errores se guardan en `errors/` para trazabilidad.

## Consideraciones de Seguridad y Privacidad

- No compartas tu `.env` ni tu API Key de 2Captcha.
- Los archivos generados pueden contener información sensible.

## Pruebas y Extensibilidad

- El código está modularizado para facilitar pruebas unitarias de funciones como `extract_recaptcha_sitekey` o `save_result_as_pdf`.
- Puedes adaptar el script para recibir la cédula por argumento de línea de comandos o integrarlo en otros sistemas.

## Limitaciones y Notas

- El sitio web de la Policía puede cambiar su estructura, lo que podría requerir ajustes en el script.
- El uso de servicios de resolución de CAPTCHA puede tener costos asociados.
- El script está pensado para uso personal o institucional legítimo, no para automatización masiva sin autorización.

## Licencia

Este proyecto se distribuye bajo licencia MIT. Consulta el archivo LICENSE para más detalles.
