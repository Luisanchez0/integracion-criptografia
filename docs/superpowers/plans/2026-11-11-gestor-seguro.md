# Gestor Seguro — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar la aplicación académica local descrita en el prompt, con cifrado real de notas y firmas reales de documentos.

**Architecture:** Factoría Flask, blueprints de autenticación/notas/documentos, persistencia sqlite3 y módulos criptográficos independientes. Jinja2 y Bootstrap 5 local, sin servicios externos en ejecución. Los secretos y datos locales se excluyen de Git.

**Tech Stack:** Python >=3.11, Flask, sqlite3, cryptography, python-dotenv, Flask-WTF, Jinja2, HTML/CSS/Bootstrap 5, pytest.

**Spec:** `Prompt_Codex_Gestor_Seguro.md` (autoridad para requisitos y autorización de ejecución continua).

## Restricciones globales

- Interfaz y mensajes en español; sin registro público.
- AES de 32 bytes desde AES_KEY Base64; nonce nuevo de 12 bytes por cifrado; tag de 16 bytes junto al ciphertext.
- Ed25519 firma bytes exactos; verifica bytes actuales; prueba alterada nunca sobrescribe el original.
- SECRET_KEY desde entorno; CSRF global; SQL parametrizado; propietario en cada consulta privada.
- Solo .txt/.pdf, límite configurable y nombres internos aleatorios.
- Sin Node.js, React, Docker ni servicios externos.
- Sin regeneración de claves ni borrado automático de datos al arrancar.

## Decisiones de implementación

- El directorio inicial solo contiene el prompt, sin Git ni código que preservar; se trabaja aquí sin crear un repositorio ni hacer commits.
- Se ejecuta este plan directamente: el prompt pide continuar y preguntar solo si es imprescindible.
- Se prefiere una factoría con blueprints frente a un archivo monolítico para separar acceso, datos y criptografía.
- Notas: nonce y ciphertext+tag en columnas Base64; AAD vincula el cifrado al UUID de nota y usuario. Título y fechas quedan visibles; se explica esa limitación.
- Nonces aleatorios de 96 bits y registro UNIQUE histórico para impedir reutilizarlos dentro de esta base incluso tras editar/eliminar.
- Documentos: se firman al registrar; se permite reverificar y verificar un archivo candidato contra la misma firma, sin modificar el original.
- Clave privada PEM PKCS8, pública PEM SubjectPublicKeyInfo; permisos 0600 POSIX y ACL del usuario en Windows.
- Inicialización idempotente, usuario admin local y contraseña aleatoria generada, guardada solo en archivo local ignorado con permisos restrictivos.
- Bootstrap se incluye en static/vendor con su licencia; no depende de CDN en ejecución.

## Review Focus

1. Manipulación de identificadores/archivos de otro usuario: 404 y ausencia de exposición.
2. Token CSRF ausente, sesión expirada, redirección externa: rechazo controlado y navegación local.
3. AES/PEM inválidos o desparejados y archivo faltante: mensajes controlados sin secretos ni rutas en HTML.
4. Nombres peligrosos, archivos vacíos, extensión/tamaño inválidos: rechazo sin archivos huérfanos.
5. Repetir inicialización o generación de claves: no pierde datos ni reemplaza secretos.

## Etapa 1: inspección y planificación

- [x] Leer el prompt, inventariar directorio e instrucciones locales.
- [x] Presentar el plan y establecer límites e interfaces.
- [x] Preparar Python local y dependencias verificables.

## Etapa 2: base, persistencia y acceso

**Archivos:** `config.py`, `run.py`, `requirements.txt`, `.gitignore`, `.env.example`, `app/__init__.py`, `app/database/{db.py,schema.sql}`, `app/auth/routes.py`, plantillas base/login/dashboard/errores, `scripts/{setup_env.py,init_db.py}`, `tests/{conftest.py,test_auth.py,test_config.py}`.

**Interfaces:** `create_app(test_config=None, *, require_signing_keys=True) -> Flask`; `get_db() -> sqlite3.Connection`; `init_db() -> None`; `login_required(view)`; `g.user` para el usuario actual. Config permite rutas absolutas o relativas a la raíz.

- [x] Escribir pruebas de arranque, hashes de contraseñas, rutas privadas, login/logout, CSRF e inicialización idempotente y ejecutarlas antes del código (fallo esperado: módulo ausente).
- [x] Implementar configuración validada y acceso; inicialización explícita sin borrar datos.
- [x] Ejecutar `python -m pytest tests/test_auth.py tests/test_config.py -q`; resultado esperado: todas pasan (15 aprobadas).
- [x] Arrancar servidor local y comprobar HTTP de login antes de avanzar.

## Etapa 3: notas AES-256-GCM

**Archivos:** `app/crypto/encryption.py`, `app/notes/routes.py`, `app/templates/notes/{list,form,detail,delete}.html`, `tests/{test_encryption,test_notes}.py`.

**Interfaces:** `encrypt_note(key: bytes, content: str, aad: bytes) -> tuple[str,str]` devuelve nonce/ciphertext Base64; `decrypt_note(key, nonce_b64, ciphertext_b64, aad) -> str`; `note_aad(note_id: str, user_id: int) -> bytes`.

- [x] Pruebas primero: ida/vuelta Unicode, nonces distintos, llave/ciphertext/AAD alterados, CRUD, propietario, confirmación y persistencia cifrada.
- [x] Implementar criptografía y CRUD; InvalidTag se convierte en respuesta controlada.
- [x] Ejecutar `python -m pytest tests/test_encryption.py tests/test_notes.py -q`; todas pasan.
- [x] Inspeccionar SQLite directamente: texto ficticio ausente del ciphertext y archivo de base de datos; recuperación exacta desde ruta autorizada.

## Etapa 4: documentos Ed25519

**Archivos:** `app/crypto/signatures.py`, `app/documents/routes.py`, `scripts/generate_keys.py`, plantillas documentos, `tests/{test_signatures,test_documents}.py`.

**Interfaces:** `generate_keypair(private_path: Path, public_path: Path) -> None` sin sobrescritura; `load_keypair(...) -> tuple[Ed25519PrivateKey,Ed25519PublicKey]`; `sign_document(private_key, data: bytes) -> str`; `verify_document(public_key, data: bytes, signature_b64: str) -> bool`.

- [x] Pruebas primero: firmas válidas/alteradas/clave ajena, PEM persistido/desparejado, archivos modificados, subida y descarga, candidatos y propiedad, extensiones/tamaño/nombre seguros.
- [x] Implementar generación explícita, permisos, firma y rutas; comprobar claves al arrancar.
- [x] Ejecutar `python -m pytest tests/test_signatures.py tests/test_documents.py -q`; todas pasan.
- [x] Probar que bytes alterados producen firma inválida y el original permanece intacto.

## Etapa 5: interfaz y navegador

**Archivos:** `app/static/css/app.css`, `app/static/vendor/*`, todas las plantillas, `tests/test_routes.py`.

- [x] Completar dashboard con conteos por usuario, accesos rápidos, tablas, estados vacíos, resultados válidos/inválidos, menús responsive y formularios con etiquetas.
- [x] Pruebas de rutas, escape HTML, headers y activos locales.
- [x] Verificar flujos completos contra el servidor HTTP real mediante smoke_http.py.
- [ ] Inspección visual de escritorio/móvil: pendiente por indisponibilidad del host de navegador; limitación documentada, sin afirmación de verificación visual.

## Etapa 6: documentación y revisión

**Archivos:** `README.md`, `docs/VERIFICACION.md`, `scripts/demo_crypto.py`, `.env.example`, `.gitignore` y pruebas de regresión que haga falta.

- [x] Documentar instalación Windows/Linux/macOS, variables, inicialización, generación, ejecución/debug y recuperación de claves.
- [x] Añadir demostración reproducible de SQLite y firma alterada con datos ficticios y originales intactos.
- [x] Ejecutar suite completa, compilación Python y demo; registrar comandos/resultados por etapa.
- [x] Revisión final separada de la implementación (autorrevisión, sin auditor externo); corregir saltos de línea iniciales con regresión RED→GREEN y suite completa aprobada.
- [x] Revisar exclusiones de secretos y datos; entregar comandos de uso y limitaciones académicas.
