import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twocaptcha import TwoCaptcha
import logging
import time
import os
import base64
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchWindowException, TimeoutException, NoSuchElementException
import re

# --- Configuración Básica ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def save_result_as_pdf(driver, cedula):
    """Guarda la página de resultados como PDF en la carpeta 'antecedentes'."""
    try:
        pdf_dir = "antecedentes"
        os.makedirs(pdf_dir, exist_ok=True)
        filepath = os.path.join(pdf_dir, f"antecedentes_{cedula}.pdf")
        print_options = {
            'landscape': False, 'displayHeaderFooter': False, 'printBackground': True,
        }
        result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
        pdf_data = base64.b64decode(result['data'])
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        logging.info(f"Antecedentes guardados exitosamente en: {filepath}")
    except Exception as e:
        logging.error(f"No se pudo guardar el archivo PDF: {e}")

def is_driver_alive(driver):
    try:
        return driver is not None and driver.session_id and driver.title is not None
    except Exception:
        return False

def extract_recaptcha_sitekey(driver, wait):
    strategies = [
        {'selector': '[data-sitekey]', 'attribute': 'data-sitekey', 'description': 'Elemento con atributo data-sitekey'},
        {'selector': 'iframe[src*="recaptcha"]', 'attribute': 'src', 'description': 'iframe de reCAPTCHA', 'extract_from_src': True},
        {'selector': '.g-recaptcha', 'attribute': 'data-sitekey', 'description': 'Div con clase g-recaptcha'},
        {'selector': 'script[src*="recaptcha"]', 'attribute': 'src', 'description': 'Script de reCAPTCHA', 'extract_from_src': True}
    ]
    for i, strategy in enumerate(strategies, 1):
        try:
            logging.info(f"Estrategia {i}: Buscando {strategy['description']}")
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, strategy['selector'])))
            if strategy.get('extract_from_src'):
                src = element.get_attribute(strategy['attribute'])
                if src and 'k=' in src:
                    sitekey = src.split('k=')[1].split('&')[0]
                    logging.info(f"Sitekey extraído de URL: {sitekey}")
                    return sitekey
            else:
                sitekey = element.get_attribute(strategy['attribute'])
                if sitekey:
                    logging.info(f"Sitekey encontrado: {sitekey}")
                    return sitekey
        except (TimeoutException, NoSuchElementException) as e:
            logging.warning(f"Estrategia {i} falló: {e}")
            continue
    try:
        logging.info("Estrategia final: Buscando en JavaScript de la página")
        page_source = driver.page_source
        patterns = [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'sitekey["\']?\s*:\s*["\']([^"\']+)["\']',
            r'k=([a-zA-Z0-9_-]+)',
            r'recaptcha.*?["\']([a-zA-Z0-9_-]{40})["\']'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                sitekey = matches[0]
                logging.info(f"Sitekey encontrado en JavaScript: {sitekey}")
                return sitekey
    except Exception as e:
        logging.error(f"Error en estrategia final: {e}")
    raise Exception("No se pudo encontrar el sitekey del reCAPTCHA en ninguna estrategia")

def consultar_antecedentes_headless(cedula):
    """
    Automatiza la consulta usando Selenium en modo headless (sin UI visible).
    """
    max_intentos = 2
    intentos = 0
    proceso_exitoso = False
    while not proceso_exitoso and intentos < max_intentos:
        intentos += 1
        driver = None
        try:
            logging.info(f"--- Iniciando Intento #{intentos} de {max_intentos} ---")
            def create_new_driver():
                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
                return uc.Chrome(options=options)
            if not is_driver_alive(driver):
                driver = create_new_driver()
            wait = WebDriverWait(driver, 20)
            driver.get("https://antecedentes.policia.gov.co:7005/WebJudicial/")
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "preloader")))
            wait.until(EC.element_to_be_clickable((By.ID, "aceptaOption:0"))).click()
            time.sleep(1.5)
            try:
                if not is_driver_alive(driver):
                    logging.warning("El driver está dañado antes de buscar 'continuarBtn'. Creando uno nuevo.")
                    driver.quit()
                    driver = create_new_driver()
                    wait = WebDriverWait(driver, 20)
                    driver.get("https://antecedentes.policia.gov.co:7005/WebJudicial/")
                    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "preloader")))
                    wait.until(EC.element_to_be_clickable((By.ID, "aceptaOption:0"))).click()
                    time.sleep(1.5)
                enviar_button = driver.find_element(By.ID, "continuarBtn")
            except NoSuchWindowException as e:
                logging.error(f"NoSuchWindowException al buscar 'continuarBtn': {e}")
                raise
            if not enviar_button.is_enabled():
                logging.warning("El botón 'Enviar' está desactivado. Reiniciando el flujo...")
                error_dir = "errors"
                os.makedirs(error_dir, exist_ok=True)
                error_filepath = os.path.join(error_dir, f"error_{cedula}_intento_{intentos}.png")
                try:
                    if is_driver_alive(driver):
                        driver.save_screenshot(error_filepath)
                        logging.info(f"Captura de error guardada en: {error_filepath}")
                except NoSuchWindowException as save_err:
                    logging.error(f"NoSuchWindowException al guardar la captura de error: {save_err}")
                except Exception as save_err:
                    logging.error(f"No se pudo guardar la captura de error: {save_err}")
                driver.quit()
                continue
            try:
                if not is_driver_alive(driver):
                    logging.warning("El driver está dañado antes de hacer click en 'continuarBtn'. Creando uno nuevo.")
                    driver.quit()
                    driver = create_new_driver()
                    wait = WebDriverWait(driver, 20)
                    driver.get("https://antecedentes.policia.gov.co:7005/WebJudicial/")
                    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "preloader")))
                    wait.until(EC.element_to_be_clickable((By.ID, "aceptaOption:0"))).click()
                    time.sleep(1.5)
                    enviar_button = driver.find_element(By.ID, "continuarBtn")
                enviar_button.click()
            except NoSuchWindowException as e:
                logging.error(f"NoSuchWindowException al hacer click en 'continuarBtn': {e}")
                raise
            cedula_input = wait.until(EC.visibility_of_element_located((By.ID, "cedulaInput")))
            cedula_input.send_keys(cedula)
            try:
                logging.info("Intentando resolver el reCAPTCHA automáticamente...")
                api_key = os.getenv('API_KEY_2CAPTCHA', 'TU_API_KEY_DE_2CAPTCHA')
                if 'TU_API_KEY' in api_key: raise Exception("API Key no configurada")
                sitekey = extract_recaptcha_sitekey(driver, wait)
                solver = TwoCaptcha(api_key)
                result = solver.recaptcha(sitekey=sitekey, url=driver.current_url)
                g_response = result.get('code') or result.get('token') or result.get('gRecaptchaResponse')
                if not g_response:
                    raise Exception(f"Respuesta inesperada de 2Captcha: {result}")
                driver.execute_script(
                    "document.getElementById('g-recaptcha-response').style.display = 'block';"
                    "document.getElementById('g-recaptcha-response').value = arguments[0];"
                    "document.getElementById('g-recaptcha-response').dispatchEvent(new Event('change'));",
                    g_response
                )
                logging.info("reCAPTCHA resuelto automáticamente.")
                time.sleep(2)
                driver.find_element(By.ID, "j_idt17").click()
            except Exception as e:
                logging.warning(f"No se pudo resolver el CAPTCHA automáticamente: {e}. Pasando a modo manual.")
                input(
                    "\n❗ MODO MANUAL ACTIVADO:\n"
                    "   1. Resuelve el CAPTCHA en el navegador.\n"
                    "   2. HAZ CLIC en el botón 'Consultar'.\n"
                    "   3. Cuando veas los resultados, presiona 'Enter' aquí para continuar...\n"
                )
            logging.info("Esperando los resultados de la consulta...")
            time.sleep(10)
            save_result_as_pdf(driver, cedula)
            proceso_exitoso = True
            print("\n✅ Proceso completado exitosamente.")
        except NoSuchWindowException as e:
            logging.error(f"NoSuchWindowException capturada en el intento #{intentos}: {e}")
        except Exception as e:
            logging.error(f"Ocurrió un error en el intento #{intentos}: {e}")
            if driver:
                try:
                    if is_driver_alive(driver):
                        error_dir = "errors"
                        os.makedirs(error_dir, exist_ok=True)
                        error_filepath = os.path.join(error_dir, f"error_{cedula}_intento_{intentos}.png")
                        driver.save_screenshot(error_filepath)
                        logging.info(f"Captura de error guardada en: {error_filepath}")
                except NoSuchWindowException as save_err:
                    logging.error(f"NoSuchWindowException al guardar la captura de error en except: {save_err}")
                except Exception as save_err:
                    logging.error(f"No se pudo guardar la captura de error: {save_err}")
            if "TU_API_KEY" in str(e):
                 break
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as quit_err:
                    logging.error(f"Error al cerrar el driver: {quit_err}")
    if not proceso_exitoso:
        print(f"\n❌ El proceso falló después de {max_intentos} intentos.")

if __name__ == "__main__":
    cedulas_input = input("Ingrese una o varias cédulas separadas por coma: ").strip()
    cedulas = [c.strip() for c in cedulas_input.split(',') if c.strip().isdigit()]
    if not cedulas:
        print("No se ingresaron cédulas válidas. El programa terminará.")
    else:
        for cedula in cedulas:
            print(f"\nConsultando antecedentes para la cédula: {cedula}")
            consultar_antecedentes_headless(cedula) 