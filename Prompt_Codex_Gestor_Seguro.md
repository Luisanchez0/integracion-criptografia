# Prompt para Codex: Gestor de notas y documentos seguros

## 1. Objetivo del proyecto

Desarrolla una aplicación web propia llamada **Gestor Seguro**,
destinada a almacenar notas privadas y documentos con mecanismos
criptográficos reales.

El proyecto se realiza como práctica académica. Debe demostrar, de forma
funcional y verificable, dos mecanismos distintos:

1.  **Cifrado simétrico:** proteger el contenido de las notas con
    AES-256-GCM.
2.  **Criptografía asimétrica:** firmar digitalmente documentos con
    Ed25519 y verificar sus firmas con la clave pública correspondiente.

La aplicación debe ser sencilla de instalar, ejecutar, probar y explicar
durante una demostración en vivo. No construyas solamente ejemplos
aislados: implementa una aplicación web funcional de principio a fin.

## 2. Tecnologías obligatorias

Utiliza exclusivamente esta pila, salvo que exista una razón técnica
importante para proponer un cambio:

-   Python 3.11 o superior.
-   Flask para el servidor web.
-   SQLite mediante el módulo estándar `sqlite3`.
-   `cryptography` para AES-256-GCM y Ed25519.
-   `python-dotenv` para cargar variables de entorno.
-   HTML, CSS y Bootstrap 5 para la interfaz.
-   Jinja2 mediante el motor de plantillas incluido en Flask.

No uses Node.js, React, Docker ni servicios externos. La aplicación debe
poder ejecutarse localmente.

## 3. Funcionalidades

### 3.1. Acceso a la aplicación

Implementa un acceso básico para la demostración académica:

-   Pantalla de inicio de sesión.
-   Un usuario administrador de demostración creado mediante un comando
    de inicialización o un proceso documentado.
-   Almacena las contraseñas utilizando
    `werkzeug.security.generate_password_hash` y `check_password_hash`.
    Nunca guardes contraseñas en texto claro.
-   Utiliza sesiones de Flask y protege las rutas privadas.
-   Incluye protección CSRF en formularios, preferentemente con
    Flask-WTF.
-   No permitas el registro público de usuarios en esta primera versión.

Los datos de demostración deben ser ficticios. Documenta claramente las
credenciales locales de prueba, sin utilizar credenciales reales.

### 3.2. Gestión de notas privadas: AES-256-GCM

Permite al usuario:

-   Crear una nota con título y contenido.
-   Consultar la lista de sus notas.
-   Abrir una nota y visualizar su contenido original.
-   Editar una nota.
-   Eliminar una nota con confirmación.

**Requisito criptográfico obligatorio:**

-   Cifra el contenido de cada nota antes de insertarlo o actualizarlo
    en SQLite.
-   Utiliza AES-256-GCM mediante la librería `cryptography`.
-   Genera un nonce aleatorio nuevo de 12 bytes para cada operación de
    cifrado.
-   Nunca reutilices un nonce con la misma llave.
-   Almacena en la base de datos el nonce, el ciphertext y el tag de
    autenticación, o almacena el resultado serializado de forma
    inequívoca. Es preferible guardar nonce y ciphertext juntos en
    Base64, documentando el formato.
-   Descifra el contenido únicamente en el servidor cuando un usuario
    autorizado consulta o edita su nota.
-   Si la llave es incorrecta o el contenido fue alterado, captura
    `InvalidTag` y muestra un error controlado. No muestres trazas
    internas al usuario.
-   No registres el contenido de las notas ni las llaves en logs.

**Demostración requerida:**

1.  Crear una nota con texto ficticio y reconocible.
2.  Consultar directamente SQLite y comprobar que el contenido
    almacenado no aparece en texto claro.
3.  Abrir la nota desde la aplicación y comprobar que se muestra el
    contenido original.
4.  Explicar el papel del nonce y la autenticación GCM.

No cifres solamente la respuesta HTML: el dato debe almacenarse cifrado
en la base de datos.

### 3.3. Gestión de documentos: firma digital Ed25519

Permite al usuario:

-   Cargar un documento de prueba (por ejemplo, `.txt` o `.pdf`) o crear
    un comprobante sencillo desde un formulario.
-   Guardar el documento en el almacenamiento local de la aplicación.
-   Firmar digitalmente los bytes exactos del archivo con Ed25519.
-   Guardar la firma digital asociada al documento.
-   Consultar los documentos registrados.
-   Verificar la firma de un documento.
-   Mostrar un resultado claro: **firma válida** o **firma inválida**.
-   Descargar el documento original.

**Requisito criptográfico obligatorio:**

-   Genera un par de claves Ed25519 mediante `cryptography`.
-   Firma con la clave privada y verifica con la clave pública.
-   Guarda la clave privada fuera del código fuente y del repositorio
    Git. Protege sus permisos de archivo.
-   La clave pública puede almacenarse en el proyecto y compartirse para
    la verificación.
-   Guarda la firma en Base64 en SQLite o en un archivo asociado, y
    conserva una referencia al documento firmado.
-   Verifica la firma contra los bytes actuales del archivo, no contra
    una copia del hash guardada como si eso bastara.
-   Si el documento cambia, la verificación debe fallar.
-   No afirmes que Ed25519 cifra documentos: en este proyecto se utiliza
    para firma digital y verificación de autenticidad e integridad.

**Demostración requerida:**

1.  Cargar o crear un documento ficticio.
2.  Firmarlo.
3.  Verificarlo y mostrar que la firma es válida.
4.  Modificar una copia del documento o alterar su contenido de prueba.
5.  Verificar la versión modificada y mostrar que la firma es inválida.

No sobrescribas silenciosamente el documento original durante la prueba
de manipulación.

### 3.4. Panel principal

Crea un dashboard sencillo y profesional que muestre:

-   Cantidad de notas registradas.
-   Cantidad de documentos registrados.
-   Accesos rápidos para crear una nota y cargar un documento.
-   Estado o acceso a la verificación de firmas.
-   Navegación clara entre Inicio, Notas, Documentos y Cerrar sesión.

La interfaz debe estar en español, ser adaptable a escritorio y móvil, y
mostrar mensajes de éxito y error comprensibles.

## 4. Diseño y estructura del proyecto

Organiza el proyecto de manera modular. Usa como referencia esta
estructura y ajústala si lo justificas:

``` text
gestor-seguro/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   └── routes.py
│   ├── notes/
│   │   └── routes.py
│   ├── documents/
│   │   └── routes.py
│   ├── crypto/
│   │   ├── encryption.py
│   │   └── signatures.py
│   ├── database/
│   │   ├── db.py
│   │   └── schema.sql
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── notes/
│   │   └── documents/
│   └── static/
│       ├── css/
│       └── js/
├── instance/
│   └── .gitkeep
├── storage/
│   └── .gitkeep
├── scripts/
│   ├── init_db.py
│   └── generate_keys.py
├── tests/
│   ├── test_encryption.py
│   ├── test_signatures.py
│   └── test_routes.py
├── .env.example
├── .gitignore
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

Usa una factoría de aplicación de Flask si facilita la organización.
Mantén separadas las rutas, la persistencia y las operaciones
criptográficas.

## 5. Gestión de llaves y secretos

Este requisito es fundamental para la evaluación.

### Llave AES

-   Genera una llave AES de 32 bytes criptográficamente aleatorios.
-   No inventes una llave ni la escribas directamente en el código.
-   Cárgala desde una variable de entorno, por ejemplo `AES_KEY`.
-   Documenta cómo generarla y cómo representarla en Base64 o
    hexadecimal.
-   Valida al iniciar la aplicación que la llave tenga exactamente 32
    bytes.
-   No incluyas la llave real en `.env.example`, README, logs ni
    repositorio.

### Claves Ed25519

-   Genera el par de claves con un script dedicado.
-   Guarda la clave privada en una ubicación local excluida de Git, con
    permisos restrictivos cuando el sistema operativo lo permita.
-   Guarda la clave pública en una ubicación documentada.
-   Permite configurar las rutas mediante variables de entorno.
-   No regeneres las claves automáticamente en cada inicio: hacerlo
    impediría verificar documentos firmados anteriormente.
-   Si faltan las claves, muestra un mensaje claro con el comando que
    debe ejecutarse para generarlas.
-   No subas la clave privada a GitHub.

### Archivo de entorno

Incluye `.env.example` con nombres de variables y valores de ejemplo que
no sean secretos reales. Incluye `.env` en `.gitignore`.

## 6. Seguridad y validaciones

Implementa, como mínimo:

-   Validación de formularios en el servidor.
-   Protección CSRF.
-   Restricción de extensiones permitidas para documentos (`.txt` y
    `.pdf` en esta versión).
-   Límite configurable de tamaño de archivo.
-   Nombres de archivo seguros; utiliza `werkzeug.utils.secure_filename`
    y nombres internos aleatorios para evitar colisiones.
-   Evita rutas de archivo controladas directamente por el usuario.
-   Verifica que las rutas privadas requieran sesión.
-   Usa consultas SQL parametrizadas.
-   Maneja errores sin mostrar secretos, rutas internas ni trazas al
    usuario.
-   Configura `SECRET_KEY` de Flask mediante variable de entorno.
-   Desactiva el modo debug en configuración de producción. Para
    desarrollo local, explica cómo activarlo de forma controlada.
-   No guardes información sensible en logs.
-   No presentes la aplicación como lista para producción: es una
    práctica académica local y requiere una revisión adicional antes de
    exponerse a Internet.

## 7. Base de datos

Diseña tablas sencillas para:

-   Usuarios.
-   Notas.
-   Documentos.

Para las notas, almacena al menos:

-   Identificador.
-   Usuario propietario.
-   Título.
-   Contenido cifrado.
-   Nonce.
-   Fecha de creación.
-   Fecha de actualización.

Para los documentos, almacena al menos:

-   Identificador.
-   Usuario propietario.
-   Nombre original seguro.
-   Nombre interno de almacenamiento.
-   Ruta o referencia interna.
-   Firma Ed25519 codificada en Base64.
-   Fecha de creación.
-   Estado o metadatos necesarios para la interfaz.

La base de datos debe inicializarse con un script o comando documentado.
No borres los datos existentes automáticamente al iniciar la aplicación.

## 8. Pruebas automatizadas

Crea pruebas con `pytest` para comprobar:

### AES-256-GCM

-   Un texto se cifra y luego se descifra obteniendo exactamente el
    original.
-   Dos cifrados del mismo texto generan resultados distintos debido al
    nonce aleatorio.
-   Un ciphertext alterado no puede descifrarse correctamente.
-   Una llave incorrecta no permite descifrar el contenido.

### Ed25519

-   Una firma válida se verifica correctamente.
-   Una firma modificada falla.
-   Un documento modificado después de firmarse falla en la
    verificación.
-   La clave pública correspondiente verifica las firmas de la clave
    privada utilizada.

### Aplicación

-   Un usuario no autenticado no puede acceder a las rutas privadas.
-   Se puede crear y consultar una nota.
-   El contenido de la nota en SQLite no aparece en texto claro.
-   Se puede registrar un documento, firmarlo y verificarlo.

Las pruebas deben utilizar archivos y datos ficticios. No uses
documentos ni contraseñas reales.

## 9. Experiencia de usuario

Diseña una interfaz limpia, moderna y académica:

-   Idioma: español.
-   Menú lateral o superior.
-   Dashboard con tarjetas de resumen.
-   Formularios sencillos.
-   Tablas para notas y documentos.
-   Etiquetas visuales para firma válida e inválida.
-   Confirmación antes de eliminar.
-   Mensajes claros cuando no existan notas o documentos.
-   Diseño responsive.

Evita animaciones innecesarias y dependencias visuales pesadas.

## 10. README y documentación académica

El `README.md` debe explicar:

1.  Descripción y objetivo del proyecto.
2.  Funcionalidades.
3.  Tecnologías y librerías utilizadas.
4.  Explicación de AES-256-GCM.
5.  Explicación de Ed25519.
6.  Dónde se almacenan la llave AES y las claves Ed25519.
7.  Requisitos previos.
8.  Instalación paso a paso en Windows, Linux y macOS cuando sea
    posible.
9.  Configuración del archivo `.env`.
10. Inicialización de la base de datos.
11. Generación de claves.
12. Ejecución de la aplicación.
13. Ejecución de pruebas.
14. Procedimiento para demostrar el cifrado directamente en SQLite.
15. Procedimiento para demostrar una firma válida y una inválida.
16. Limitaciones y advertencias de seguridad.

Incluye datos de demostración inventados y credenciales locales de
prueba generadas durante la inicialización. No incluyas secretos reales.

## 11. Flujo de trabajo que debe seguir Codex

Trabaja por etapas y verifica cada etapa antes de avanzar:

**Etapa 1: Inspección y planificación** - Inspecciona el directorio
actual. - Si ya existe un proyecto, no sobrescribas archivos sin revisar
su contenido. - Presenta un plan breve y la estructura propuesta.

**Etapa 2: Base del proyecto** - Crea la estructura. - Configura
dependencias y Flask. - Implementa configuración, base de datos y
autenticación. - Comprueba que la aplicación arranca.

**Etapa 3: Cifrado simétrico** - Implementa el módulo AES-256-GCM. -
Añade pruebas unitarias. - Integra el cifrado con el CRUD de notas. -
Comprueba directamente en SQLite que el contenido se almacena cifrado.

**Etapa 4: Firma asimétrica** - Implementa generación y carga de claves
Ed25519. - Implementa firma y verificación. - Integra la funcionalidad
en la gestión de documentos. - Comprueba que modificar el archivo
provoca una verificación fallida.

**Etapa 5: Interfaz** - Completa el dashboard, notas y documentos. -
Asegura que todos los flujos se puedan ejecutar desde el navegador.

**Etapa 6: Pruebas y documentación** - Ejecuta todas las pruebas. -
Corrige los errores encontrados. - Completa el README y
`.env.example`. - Revisa `.gitignore` para evitar subir secretos, base
de datos local, documentos privados o claves privadas.

Al terminar cada etapa: - Resume los archivos creados o modificados. -
Indica los comandos ejecutados y sus resultados. - Explica cómo probar
la funcionalidad. - No afirmes que algo funciona si no lo has ejecutado
o verificado. - Si falta información, elige una opción segura y
sencilla, documenta la decisión y continúa. Pregunta solamente si es
imprescindible.

## 12. Criterios de aceptación

El proyecto se considera terminado cuando:

-   [ ] La aplicación Flask se ejecuta localmente.
-   [ ] El usuario puede iniciar y cerrar sesión.
-   [ ] Se pueden crear, consultar, editar y eliminar notas.
-   [ ] Las notas se almacenan cifradas con AES-256-GCM en SQLite.
-   [ ] Las notas se descifran correctamente al consultarlas.
-   [ ] La llave AES no está hardcodeada ni subida a GitHub.
-   [ ] Se pueden cargar o crear documentos ficticios.
-   [ ] Los documentos se firman con Ed25519.
-   [ ] Las firmas se verifican con la clave pública.
-   [ ] Una modificación del documento hace que la verificación falle.
-   [ ] La clave privada no está en el repositorio.
-   [ ] Las pruebas automatizadas pasan.
-   [ ] El README explica instalación, ejecución y demostración.
-   [ ] No hay secretos reales ni datos personales en el repositorio.

## 13. Instrucción inicial

Comienza inspeccionando el directorio de trabajo y presenta el plan de
implementación. Después desarrolla el proyecto por etapas, priorizando
que los dos mecanismos criptográficos sean correctos, comprobables y
fáciles de explicar en una exposición académica.

**No reduzcas los mecanismos criptográficos a simulaciones visuales. El
cifrado, descifrado, firma y verificación deben realizarse realmente
mediante la librería `cryptography`.**
