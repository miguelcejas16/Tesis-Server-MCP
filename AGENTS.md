# AGENTS.md

Guía para agentes que colaboran en este proyecto **MCP Server (Model Context Protocol)**.

## Contexto

Este repositorio implementa un **servidor MCP** (Model Context Protocol) en **Python 3.11+**, que maneja la comunicación entre modelos y clientes mediante un protocolo estructurado.
El objetivo es proporcionar una interfaz extensible, clara y segura para que los modelos de IA interactúen con recursos externos.


## Estilo de código

### 💛 Nombres de funciones y variables

* **Usar siempre `snake_case`** para nombres de funciones, variables y métodos.
  Ejemplo:

  ```python
  def handle_message_request():
      ...
  ```
* **Clases** deben usar `PascalCase`:

  ```python
  class MessageHandler:
      ...
  ```
* **Constantes** en mayúsculas con guiones bajos:

  ```python
  DEFAULT_TIMEOUT = 30
  ```

## Comentarios automáticos

Al escribir **cualquier función o bloque de código nuevo**, incluir **comentarios estructurados** con el formato ''' ... ''' antes de la definición.

Formato base:

```python
'''
 * Breve descripción de lo que hace la función
 * Parámetros:
 *   param_name (tipo) — descripción
 * Retorna:
 *   tipo — descripción del valor retornado
 * Notas:
 *   (opcional) información adicional
 */
def example_function(param: int) -> str:
    ...'''
```

**Ejemplo correcto**

```python
/***
 * Procesa un mensaje entrante del cliente MCP.
 * Parámetros:
 *   message (dict) — datos del mensaje JSON recibido.
 * Retorna:
 *   dict — respuesta con el resultado procesado.
 */
def process_client_message(message: dict) -> dict:
    # Lógica principal de procesamiento
    ...
```

**Evitar**:

* Comentarios tipo `# esta función hace...`
* Funciones sin docstring o con formato inconsistente.
* Usar `camelCase` o `PascalCase` en nombres de funciones.

## ⚡ Reglas para agentes

1. Comentar **todas las funciones** con el formato `/*** ... */`.
2. Usar **nombres en snake_case** para funciones y variables.
3. Mantener **tipado explícito** en parámetros y valores de retorno.
4. Formatear con `black` o respetar **PEP8**.
5. No modificar configuraciones del protocolo MCP sin aprobación.
6. Evitar código duplicado y preferir modularidad.
7. Cada nueva función debe tener su correspondiente prueba unitaria.
8. Para trabajar con las tablas de la BD tendrás el formato correspondiente en context/estructura_de_db.sql con las definiciones DLL correspondientes.

## Estructura del proyecto

```plaintext
Tesis-Server-MCP/
├── [AGENTS.md](http://_vscodecontentref_/2)
├── [pyproject.toml](http://_vscodecontentref_/3)
├── [README.md](http://_vscodecontentref_/4)
├── [uv.lock](http://_vscodecontentref_/5)
├── context/
│   └── estructura_de_db.sql
└── src/
    ├── __init__.py
    ├── bd/
    │   ├── __init__.py
    │   ├── baseModels.py
    │   └── __pycache__/
    │       ├── __init__.cpython-313.pyc
    │       └── baseModels.cpython-313.pyc
    └── server/
        ├── __init__.py
        ├── server.py
        ├── utils.py
        └── __pycache__/
            └── utils.cpython-313.pyc
```