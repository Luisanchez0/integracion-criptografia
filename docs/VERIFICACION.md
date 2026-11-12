# Registro de verificación

Plan: `docs/superpowers/plans/2026-11-11-gestor-seguro.md`.
Especificación: `Prompt_Codex_Gestor_Seguro.md`.

## Etapa 1

- Directorio inspeccionado: solo existe el prompt (16 023 bytes).
- No hay AGENTS.md local ni proyecto previo; `git status` confirma que no es repositorio.
- `python` y `py` no están en PATH. Se prepara un intérprete y entorno local sin modificar la instalación global.
- Autorización: el prompt exige escoger opciones seguras y continuar; no se solicita aprobación intermedia.
- Interfaces revisadas: autenticación provee `g.user` a notas/documentos; ambos usan `get_db`; rutas consumen módulos criptográficos sin SQL dentro de estos.

## Etapa 2

- Archivos: config/run, factoría Flask, auth, database, plantillas iniciales, scripts setup_env/init_db, tests y exclusiones.
- Python 3.12.14 local + entorno .venv; dependencias instaladas con uv.
- RED: `python -m pytest tests/test_auth.py tests/test_config.py -q --tb=short` falló por módulo app ausente.
- GREEN: mismo comando, **15 passed**.
- `python scripts/setup_env.py`: creó .env sin imprimir secretos; ACL restringida.
- `python scripts/init_db.py` dos veces: creó admin; segunda ejecución conservó datos y contraseña.
- `python run.py`: servidor en 127.0.0.1:5000, debug apagado. GET real /auth/login: **200**, formulario y CSRF presentes.
- Se detectó OutputEncoding ASCII del shell en el chequeo HTTP; se corrigió a UTF-8 sin cambiar la aplicación.
- Bootstrap 5.3.8 con licencia MIT incluido en static/vendor.
- Cómo probar: abrir /auth/login, usar instance/demo_credentials.txt, entrar y cerrar sesión.

## Etapa 3

- Archivos: crypto/encryption.py, notes/routes.py, plantillas de listado/formulario/detalle/confirmación y pruebas AES/notas.
- RED: pytest no pudo importar app.crypto, todavía ausente.
- GREEN: `python -m pytest tests/test_encryption.py tests/test_notes.py -q --tb=short`: **25 passed**.
- Comprobado: texto Unicode exacto, nonce aleatorio de 12 bytes, tag de 16 bytes, rechazo de llave/ciphertext/nonce/AAD alterados.
- CRUD autorizado, CSRF, validación, escape HTML y acceso ajeno rechazado. Editar genera nonce nuevo; borrar conserva historial de nonces. Una colisión simulada se reintenta.
- Consulta directa sqlite3 al archivo de la prueba: nonce **12 bytes**, ciphertext+tag **87 bytes**; marcador ficticio ausente tanto en la columna cifrada como en bytes de SQLite.
- Cómo probar: crear nota con texto ficticio, abrirla, editarla y eliminarla mediante confirmación. La inspección de SQLite se automatiza en las pruebas y en el script de demostración final.

## Etapa 4

- Archivos: crypto/signatures.py, documents/routes.py y storage.py, script generate_keys.py y plantillas de carga/listado/detalle/verificación.
- RED: faltaba app.crypto.signatures; GREEN: `python -m pytest tests/test_signatures.py tests/test_documents.py -q --tb=short`: **27 passed**.
- Firma válida de los bytes originales; firma, clave pública o documento alterados dan resultado inválido.
- Carga, firma, descarga, clave pública, nombres internos aleatorios, extensión/tamaño/contenido básico y autorización por propietario verificados.
- Una copia alterada falla sin cambiar el original ni guardar la copia. Alterar el archivo guardado también produce firma inválida.
- `python scripts/generate_keys.py` dos veces: creó el par y después lo conservó. La factoría arrancó con el par validado.
- ACL comprobada con icacls: clave privada restringida al usuario ejecutor. El ejecutor aislado difiere del dueño del proyecto; se dará acceso también al dueño real a los datos locales antes de entregar.
- Cómo probar: cargar un TXT ficticio, verificar, descargarlo, modificar una copia y enviarla en «Comprobar una copia».

## Etapa 5

- Archivos: static/css/app.css, Bootstrap local, plantillas responsive y scripts/smoke_http.py.
- RED: el chequeo de activos detectó app.css ausente (404). GREEN: `python -m pytest tests/test_routes.py -q --tb=short`: **4 passed**.
- Menú, tarjetas, tablas, estados vacíos, confirmación, formularios con etiquetas, estados válidos/inválidos y CSS móvil implementados sin JavaScript ni CDN.
- `python scripts/smoke_http.py` contra el servidor real: **todos los flujos HTTP aprobados**, incluyendo login/CSRF, crear/consultar/editar/eliminar nota, SQLite cifrado, subir/firmar/verificar documento, copia alterada inválida, original intacto, descarga y logout.
- Se conserva un comprobante HTTP ficticio firmado; la nota temporal se eliminó mediante su confirmación normal.
- Limitación de verificación: tanto inventario CUA como createBrowserTab devolvieron «The browser access host is unavailable». No se afirma inspección visual de navegador ni de viewport móvil. La verificación disponible fue HTTP real y pruebas de HTML/rutas/activos.

## Etapa 6

- Archivos: README completo, requirements.lock.txt, demo_crypto.py, smoke_http.py, pruebas de configuración adicionales y regresión de saltos de línea iniciales.
- Suite completa inicial: **76 passed**. La autorrevisión posterior detectó que el parser HTML descarta un LF inmediatamente después de abrir textarea/pre.
- Regresión `test_edit_form_preserves_initial_newlines`: **falló primero**, se corrigieron las plantillas, y después **pasó**. El editor conserva ahora los saltos iniciales y el detalle usa un contenedor con white-space: pre-wrap.
- Suite completa final: `python -m pytest -q --tb=short`: **77 passed in 55.10s**, salida 0.
- `python scripts/demo_crypto.py`: SQLite sin texto claro, recuperación exacta, llave equivocada rechazada, firma original válida y copia alterada inválida; original intacto y temporales retirados. Salida 0.
- `python -m compileall -q app scripts config.py run.py`: salida 0.
- Servidor reiniciado después del ajuste de plantillas; `python scripts/smoke_http.py` repetido contra el servidor real: todos los flujos aprobados, salida 0. Quedaron dos comprobantes ficticios firmados y ninguna nota de esa prueba.
- Escaneo de **53 archivos** entregables: ninguna aparición de los valores locales de AES_KEY, SECRET_KEY o contraseña de demostración.
- `.gitignore` evaluado con **git check-ignore** en un repositorio temporal aislado: **11 rutas privadas excluidas**, y `.env.example`, README, código y lock incluidos. El directorio principal sigue sin repositorio Git.
- La primera invocación del evaluador de ignores encontró CRLF en stdin de Windows; se repitió correctamente con delimitadores NUL (-z). No fue un defecto de .gitignore.
- Permisos locales: se conservó acceso restringido del ejecutor y se concedió también acceso al dueño real del proyecto a .env, credenciales, claves y documentos ficticios, para que pueda ejecutar la aplicación fuera del entorno aislado.
- Revisión final realizada por el autor; no se afirma una auditoría de seguridad independiente. Limitación pendiente: inspección visual de navegador/escritorio/móvil, por host no disponible.
- Cómo probar: comandos de instalación/ejecución, pytest, demo aislada, recorrido HTTP y guion manual se encuentran en README.md. No se expusieron servicios fuera de localhost ni se publicó un repositorio.
- La revisión automática rechazó un comando de limpieza recursiva por requerir aprobación sandbox deshabilitada. No se intentó eludir el rechazo: los temporales ficticios de pytest permanecen en .test-data/, ignorados por Git, con acceso para el dueño del proyecto.
- Comprobación final de arranque/configuración: **1 usuario, 0 notas temporales y 2 documentos ficticios**, par Ed25519 válido y debug=False. Servidor de prueba detenido al terminar; usar el comando del README para iniciarlo.
