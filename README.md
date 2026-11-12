# Gestor Seguro

Aplicación web académica local para administrar notas privadas y documentos ficticios. Demuestra **cifrado AES-256-GCM** para el contenido de las notas y **firmas Ed25519** para comprobar autenticidad e integridad de documentos. Ambos mecanismos utilizan `cryptography`; las operaciones son reales y tienen pruebas automatizadas.

## Funcionalidades

- Administrador local, contraseñas con hash de Werkzeug, sesiones de 30 minutos y CSRF en todos los formularios.
- Crear, listar, consultar, editar y eliminar notas con confirmación. El contenido llega cifrado a SQLite.
- Cargar documentos TXT/PDF, firmar sus bytes exactos, descargar y verificar el archivo guardado.
- Verificar una copia candidata sin guardarla ni reemplazar el original; muestra «Firma válida» o «Firma inválida».
- Dashboard con conteos del usuario, navegación, tablas y estados vacíos en español.
- Bootstrap 5.3.8 incluido localmente, sin CDN, JavaScript, Node.js, Docker ni servicios externos en ejecución.

## Requisitos y tecnologías

Python **3.11 o superior** con `venv` y `pip`. Probado aquí con **Python 3.12.14 en Windows x64**. Flask/Jinja2, SQLite mediante `sqlite3`, `cryptography`, `python-dotenv`, Flask-WTF, Werkzeug, HTML/CSS/Bootstrap 5 y `pytest`. No requiere un servidor de base de datos ni claves de servicios externos.

`requirements.txt` describe las dependencias directas y sus intervalos compatibles; `requirements.lock.txt` conserva las versiones exactas del entorno verificado. Para reproducirlo, instala el archivo lock.

## Instalación en Windows (PowerShell)

Desde la carpeta del proyecto, con Python instalado:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe scripts/setup_env.py
.\.venv\Scripts\python.exe scripts/generate_keys.py
.\.venv\Scripts\python.exe scripts/init_db.py
.\.venv\Scripts\python.exe run.py
```

Si tu instalación usa `python` en lugar de `py`, ejecuta `python -m venv .venv`. No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell.

**En este directorio ya quedó preparado `.venv`**: puedes ejecutar directamente ` .\.venv\Scripts\python.exe run.py`. El Python de apoyo está en `.tools/python`, excluido de Git; no muevas esas carpetas para conservar este entorno. En otra computadora crea su propio `.venv` con los comandos anteriores.

## Instalación en Linux o macOS

```bash
python3 --version  # Debe indicar 3.11 o superior.
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/setup_env.py
.venv/bin/python scripts/generate_keys.py
.venv/bin/python scripts/init_db.py
.venv/bin/python run.py
```

En Linux puede hacer falta instalar el paquete `python3-venv` de la distribución. En macOS usa una instalación actual de Python. Estos pasos están documentados para portabilidad; la ejecución medida de este proyecto se hizo en Windows.

## Acceso y datos ficticios

Abre **http://127.0.0.1:5000**. El usuario es **`admin`**. La inicialización genera una **contraseña aleatoria local** y la guarda únicamente en `instance/demo_credentials.txt`, archivo ignorado por Git y con permisos restringidos. Consúltalo localmente:

```powershell
Get-Content instance/demo_credentials.txt -Encoding UTF8
```

En Linux/macOS: `cat instance/demo_credentials.txt`. Este comando muestra la contraseña: úsalo solo en tu equipo y evita incluirlo en capturas o grabaciones. No hay una contraseña universal en el código ni registro público. En SQLite solo se conserva el hash generado por `generate_password_hash`; el acceso usa `check_password_hash`.

Repetir `init_db.py` conserva usuarios, registros y contraseña. `python -m flask --app run:app init-db` crea únicamente las tablas faltantes; **no crea el administrador**. Para preparar el administrador usa el script documentado.

La prueba HTTP realizada dejó un documento **`comprobante_http_ficticio.txt`** firmado y verificado. Todo su contenido es inventado; la nota temporal de esa prueba se eliminó mediante confirmación.

## Configuración y secretos

`setup_env.py` copia `.env.example` y genera `SECRET_KEY` con `secrets.token_hex(32)` y una llave AES con `secrets.token_bytes(32)`, representada en Base64. No imprime sus valores. Si `.env` ya existe, lo conserva entero y no reemplaza secretos. Una copia manual del ejemplo contiene valores vacíos que debes generar antes de arrancar.

| Variable | Uso / valor local predeterminado |
| --- | --- |
| `SECRET_KEY` | Secreto aleatorio de Flask, mínimo 32 bytes; obligatorio. |
| `AES_KEY` | Base64 estándar de exactamente 32 bytes aleatorios; obligatorio. |
| `DATABASE_PATH` | `instance/gestor.sqlite3` |
| `STORAGE_PATH` | `storage/documents` |
| `ED25519_PRIVATE_KEY_PATH` | `instance/keys/ed25519_private.pem` |
| `ED25519_PUBLIC_KEY_PATH` | `instance/keys/ed25519_public.pem` |
| `MAX_UPLOAD_BYTES` | `5242880` (5 MiB), configurable de 1 byte a 50 MiB. |
| `SESSION_COOKIE_SECURE` | `false` para HTTP local; `true` requiere HTTPS. |

Las rutas relativas se resuelven contra la raíz del proyecto. Las variables ya presentes en el entorno del proceso tienen prioridad sobre `.env`. El límite del archivo es independiente del límite de la solicitud HTTP, que añade espacio para formularios y multipart. TXT debe ser UTF-8 no vacío y sin bytes nulos; PDF debe comenzar con `%PDF-`. Esto no sustituye un análisis completo de archivos.

Los scripts restringen los secretos al usuario ejecutor: permisos **0600** para archivos privados y **0700** para el nuevo directorio de claves en POSIX; ACL de usuario sin permisos heredados en Windows. La clave privada se serializa como PEM PKCS8 sin contraseña adicional y depende de esos permisos. La pública usa PEM SubjectPublicKeyInfo y puede descargarse desde la sesión para compartirla con la firma.

La aplicación valida ambas claves y su correspondencia al arrancar. Si faltan, indica `python scripts/generate_keys.py`. La generación se ejecuta una sola vez y **nunca sobrescribe archivos existentes**, aunque solo exista uno. Si un par está incompleto o no coincide, restaura el par original desde una copia de seguridad. No regeneres claves para «arreglar» firmas antiguas.

`.env`, las credenciales, `instance/`, `storage/`, archivos PEM/KEY, bases de datos, entornos y cachés están excluidos por `.gitignore`. **No adjuntes estas carpetas ni `.env` a una entrega pública o un ZIP.** Este directorio no era un repositorio Git y no se ha inicializado ni publicado uno.

## Cómo funciona AES-256-GCM

Cada creación o edición cifra el contenido UTF-8 **antes** de ejecutar INSERT/UPDATE. AES utiliza 32 bytes (256 bits). `os.urandom(12)` genera un nonce de 96 bits nuevo; no es secreto y debe ser distinto para una misma llave.

La tabla `notes` guarda dos campos Base64 inequívocos:

```text
nonce      = Base64(nonce de 12 bytes)
ciphertext = Base64(bytes cifrados || tag GCM de 16 bytes)
AAD        = UTF8("gestor-seguro:note:v1:<user_id>:<note_id>")
```

El AAD vincula la autenticación al propietario y al identificador de nota, sin cifrar esos metadatos. GCM detecta modificaciones del contenido, nonce o contexto, y una llave equivocada causa `InvalidTag`. La ruta captura ese error y devuelve un mensaje controlado (HTTP 422), sin mostrar contenido parcial ni trazas.

Una tabla histórica `encryption_nonces` con clave única `(SHA256(llave), nonce)` reserva cada nonce dentro de la misma transacción. Si hay una colisión se genera otro; tras cinco intentos se cancela la operación. El historial se conserva al editar o eliminar. Esta protección corresponde a **esta base de datos**: no coordina copias restauradas ni varias bases con la misma llave.

El contenido se descifra en el servidor al consultar o editar una nota propia. **Títulos, identificadores y fechas quedan visibles**. La aplicación no ofrece cifrado de extremo a extremo; el servidor tiene acceso a la llave y al texto durante una consulta autorizada.

## Cómo funciona Ed25519

Al cargar un documento se firman **todos sus bytes exactos** con la clave privada. Se guarda el archivo sin transformarlo, con un nombre interno UUID independiente del nombre seguro original, y una firma de 64 bytes codificada en Base64 en SQLite. Ed25519 **no cifra documentos**.

La verificación lee de nuevo el archivo actual y llama `public_key.verify(firma, bytes_actuales)`. No se verifica únicamente un hash guardado. Cambiar un byte, la firma o la clave pública produce un resultado inválido. El estado del listado es el último resultado conocido, acompañado de fecha en el detalle; hay que verificar otra vez para conocer el estado actual.

«Comprobar una copia» usa la firma guardada contra los bytes del candidato y solo conserva el resultado en esa respuesta. La copia no se almacena ni modifica el estado del original. Los archivos y las descargas requieren sesión y comprobación de propietario.

## Demostración académica (5–10 minutos)

1. Inicia sesión. Crea una nota con título `Reunión Aurora` y contenido `MISIÓN FICTICIA 729: exposición a las 10:30`. Ábrela y comprueba el texto original.
2. Consulta SQLite directamente, desde otra terminal en la raíz (sustituye `python` por el intérprete de tu `.venv`):

   ```bash
   python -c "import sqlite3; from config import load_settings, validate_settings; c=load_settings(); validate_settings(c); db=sqlite3.connect(c['DATABASE']); print(db.execute('SELECT id, title, nonce, ciphertext FROM notes').fetchall())"
   ```

   Se verá el título, un nonce y ciphertext Base64; el marcador no aparecerá en el contenido guardado. Edita la nota y repite la consulta: cambiarán el nonce y el ciphertext.
3. Crea localmente `comprobante_ficticio.txt` en UTF-8 con el texto `Comprobante FICTICIO Aurora. Folio 2042.`. Cárgalo y pulsa **Verificar firma**: aparece **Firma válida**.
4. Descarga el original, crea otra copia y cambia `2042` por `2043`. Envía la copia en **Comprobar una copia**: aparece **Firma inválida**. El original se conserva; vuelve a verificarlo para mostrar que sigue siendo válido.
5. Edita y elimina tu nota usando la confirmación. Cierra sesión y comprueba que las rutas privadas vuelven al acceso.

La alternativa automática, con base y archivos temporales aislados, no toca tus notas ni tus claves:

```powershell
.\.venv\Scripts\python.exe scripts/demo_crypto.py
```

Este script comprueba el almacenamiento cifrado con SQLite, la recuperación exacta y el rechazo de una llave incorrecta; después firma un original, altera una copia y verifica ambos. Retira únicamente sus archivos temporales al terminar. No imprime secretos.

## Pruebas automatizadas y comprobación HTTP

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app scripts config.py run.py
```

En Linux/macOS sustituye el ejecutable por `.venv/bin/python`. Las pruebas usan datos ficticios, claves de prueba y bases independientes bajo `.test-data/`. Incluyen AES, firmas, sesión/CSRF, autorización entre usuarios, CRUD cifrado, archivos manipulados, rutas, límites y validación. CSRF permanece habilitado también durante los tests.

Con el servidor iniciado en otra terminal:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_http.py
```

El script solo se conecta a `127.0.0.1` (opción `--port` si cambias el puerto), recorre los formularios con cookies y CSRF, comprueba SQLite y descarga el archivo. Elimina únicamente su propia nota de prueba y deja un comprobante ficticio firmado. Cada ejecución crea un comprobante nuevo. Consulta los comandos, resultados y limitaciones de validación por etapa en [docs/VERIFICACION.md](docs/VERIFICACION.md).

El host de automatización de navegador no estuvo disponible durante esta sesión. Se verificaron flujos HTTP reales y plantillas/recursos, pero **no se afirma inspección visual de escritorio o móvil**. Abre el sitio y reduce el ancho de la ventana para revisar la presentación responsive antes de la exposición.

## Estructura

```text
app/
  __init__.py           Factoría, dashboard, CSRF, headers y errores
  auth/routes.py        Sesiones y control de acceso
  crypto/               AES-GCM y firmas Ed25519, sin SQL
  database/             sqlite3 y esquema idempotente
  notes/routes.py       CRUD con cifrado y reserva de nonces
  documents/            Carga, almacenamiento y verificación
  local_files.py        Escritura exclusiva y permisos privados
  templates/            Plantillas Jinja2 en español
  static/               CSS propio y Bootstrap con licencia
scripts/                Preparación, claves, base y demostraciones
tests/                  Pruebas aisladas con pytest
instance/               Secretos y base locales, excluidos de Git
storage/                Documentos locales, excluidos de Git
docs/                   Plan y evidencia de verificación
```

## Ejecución y limitaciones

`run.py` escucha únicamente en `127.0.0.1:5000` con debug desactivado. Si el puerto está ocupado:

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app run --host 127.0.0.1 --port 5001
```

Solo durante desarrollo local, puede activarse el modo debug sin depurador interactivo ni recarga automática:

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app run --debug --no-debugger --no-reload --host 127.0.0.1
```

Esta es una **práctica académica local**, pendiente de revisión adicional antes de exponerse a Internet. No incluye MFA, bloqueo por intentos, auditoría, recuperación de contraseña, antivirus, gestión multiclave, rotación automática, backup ni un servidor de producción. Los documentos no están cifrados. La firma acredita la clave de la aplicación, no una identidad certificada ni una firma legal avanzada. Las fechas se muestran en UTC.

Conserva por separado copias protegidas de `.env`, ambas claves Ed25519, SQLite y los documentos. Perder `AES_KEY` impide recuperar las notas; cambiarla no migra el contenido antiguo. Cambiar claves Ed25519 rompe la verificación con el par nuevo; conserva la pública original para verificación externa. Cambiar `SECRET_KEY` invalida sesiones. No hay borrado seguro de soporte físico: eliminar una fila no garantiza retirar copias de backup o páginas libres de SQLite.

## Referencias técnicas

- [AESGCM y autenticación GCM — cryptography](https://cryptography.io/en/stable/hazmat/primitives/aead/)
- [Ed25519 — cryptography](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/)
- [CSRF global — Flask-WTF](https://flask-wtf.readthedocs.io/en/latest/csrf/)
- [Bootstrap 5.3 — distribución y licencia](https://getbootstrap.com/docs/5.3/getting-started/download/). Copia incluida en `app/static/vendor`, con su licencia MIT.
