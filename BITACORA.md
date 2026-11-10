# Bitácora del proyecto

Crónica de cómo se construyó esta entrega, el 10 de noviembre de 2026.
No es documentación del proyecto —para eso están [README.md](README.md) y
[ENTREGA.md](ENTREGA.md)—, sino el registro de **qué se decidió, qué falló y
por qué**. Sirve para retomar el trabajo más adelante o para que alguien del
grupo se ponga al día sin tener que reconstruirlo.

---

## El punto de partida

La actividad pedía dos contenedores Docker comunicados entre sí. El
repositorio estaba vacío y había que partir de cero.

Lo primero que se comprobó fue el entorno, y ahí apareció el primer obstáculo:

| Comprobación | Resultado |
|---|---|
| Docker Desktop instalado | No |
| WSL con alguna distribución | No |
| Virtualización en BIOS | Sí, habilitada |
| La sesión de Windows es administrador | **No** |

Sin permisos de administrador no se podía instalar Docker ni habilitar WSL2,
así que **el proyecto no se podía ejecutar en este equipo**.

**Decisión:** usar **GitHub Codespaces**, un entorno de desarrollo que corre en
el navegador y trae Docker preinstalado. No requiere instalar nada ni permisos
locales, y el plan gratuito da 60 horas al mes.

Se añadió una carpeta `.devcontainer/` para que el Codespace llegue listo para
trabajar: instala Docker y genera el `.env` con una contraseña aleatoria.

---

## Decisiones de diseño

Tres que conviene recordar, porque no son obvias y son las que se defienden en
la sustentación:

**La base de datos no publica puertos.** El servicio `db` no tiene sección
`ports:` en `docker-compose.yml`. Se hizo a propósito: además de ser más
seguro, demuestra que la comunicación entre los dos contenedores pasa de verdad
por la red interna de Docker. Si la base estuviera abierta al exterior, se
podría dudar.

**La espera al arranque está resuelta dos veces.** Un `healthcheck` en `db` más
`depends_on: condition: service_healthy` en `api`, y además un reintento dentro
de `app.py`. Es redundante a conciencia: es el punto donde más falla este tipo
de montaje.

**El Dockerfile copia `requirements.txt` antes que `app.py`.** Para aprovechar
la caché de capas. Se midió: la primera construcción tardó 19,8 s y la segunda
0,5 s, con todos los pasos marcados como `CACHED`.

---

## Los problemas que aparecieron

### 1. El script de pruebas usaba Python, y el Codespace no lo tiene

Al ejecutar `./probar.sh` por primera vez, varias líneas devolvieron
`python3: command not found`.

**Causa:** el script usaba `python3 -m json.tool` para imprimir el JSON con
sangría, pero la imagen base del devcontainer (`ubuntu-24.04`) no incluye
Python. Sí incluye `jq`.

**Importante:** las pruebas en sí **funcionaban** —los mensajes llegaban a la
base de datos—; lo que fallaba era solo mostrar las respuestas. Es decir, el
error no se veía en los resultados, solo en la pantalla.

**Solución:** el script ahora elige la herramienta que exista (`jq`, si no
`python3`, y si no imprime sin formatear). Nunca pierde la respuesta.

**Lección:** el código estaba correctamente escrito y la sintaxis era válida.
El fallo solo apareció al ejecutarlo de verdad contra un Docker real. No se
puede dar por hecho qué trae instalado un entorno ajeno.

### 2. Se subió un PDF equivocado sin mirarlo

Al preparar la entrega apareció en la carpeta un archivo llamado
`Entrega-Semana3.pdf` que era una copia de una versión anterior del documento.
Se incluyó en un commit **sin comprobar qué era**.

**Solución:** se sacó del repositorio y después se renombró el archivo correcto
con ese nombre. Al renombrar hubo que acordarse de **quitar la línea
correspondiente del `.gitignore`**, donde se había añadido para excluir la copia
vieja; si no, el archivo bueno habría quedado invisible para Git.

**Lección:** no incluir en un commit un archivo que no se ha mirado.

### 3. Comprobar el PDF dando por buena una comprobación que no servía

Se verificó que el PDF contenía el texto nuevo buscando palabras dentro del
archivo con un método casero. Dijo que no estaban. **El método estaba mal**: el
texto de un PDF va codificado y no se puede buscar como en un archivo normal.

También se dio por verificado el documento tras mirar el HTML intermedio, que
no es lo mismo que mirar el PDF final.

**Solución:** se instaló `pypdf` y se comprueba el PDF final extrayendo su
texto de verdad.

**Lección:** verificar el resultado, no el paso anterior. Y desconfiar de un
resultado negativo antes de desconfiar del trabajo.

---

## El documento de entrega se escribió tres veces

Vale la pena anotarlo porque el contenido técnico nunca cambió; lo que cambió
fue cómo estaba escrito.

1. **Primera versión:** redactada como documentación técnica. Se señaló que
   tenía demasiados tecnicismos.
2. **Segunda versión:** reescrita en lenguaje llano, explicando cada término la
   primera vez que aparece y con comparaciones del día a día (la red wifi de
   casa, la agenda de contactos del teléfono). Se añadió un glosario.
   Pero estaba en **primera persona del singular**.
3. **Tercera versión:** pasada entera a **primera persona del plural**, que es
   lo que corresponde a un trabajo en grupo, y con los dos integrantes en la
   cabecera.

---

## Cómo se generó el PDF

Sin usar el diálogo de impresión del navegador, que no es automatizable:

1. `ENTREGA.md` → HTML con Node y la librería `marked`.
2. Una hoja de estilos pensada para papel: A4 con márgenes, tablas e imágenes
   que no se parten entre páginas. Los bloques de código **sí** pueden
   partirse: al principio no, y el bloque largo del `docker-compose.yml`
   saltaba entero dejando media hoja en blanco.
3. HTML → PDF con Chrome en modo *headless* (`--print-to-pdf`).

Chrome tarda unos segundos en cerrar el archivo: comprobar si existe justo
después da un falso negativo.

---

## Estado final

- Las dos cajas construidas, encendidas y comunicándose. Verificado en el
  Codespace con las nueve pruebas de `probar.sh`.
- Cuatro capturas de evidencia en `evidencias/`.
- `ENTREGA.md` y su PDF, en lenguaje llano y en plural.
- El `.env` nunca se subió. Se comprobó dos veces: con `git check-ignore` y
  buscando la contraseña dentro de todo lo que iba a subirse.

---

## Cómo retomarlo

```bash
git clone https://github.com/SebasVelasquez/docker-semana3.git
cd docker-semana3
cp .env.example .env     # y poner una contraseña propia
```

Para ejecutarlo hace falta Docker. Si se trabaja desde un equipo sin permisos
de administrador, abrir un **Codespace** desde el botón verde `<> Code` del
repositorio: el `.devcontainer/` lo deja todo listo, y después basta con

```bash
docker compose up --build -d
./probar.sh
```
