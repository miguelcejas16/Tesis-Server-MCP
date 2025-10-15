# AGENTS.md

Guía para agentes que colaboran en este proyecto **MCP Server (Model Context Protocol)**.

## 🌟 Objetivo General

El objetivo de este proyecto es **programar de la forma MÁS SIMPLE POSIBLE** para una demostración universitaria.
Todo el código debe ser **EXTREMADAMENTE SIMPLE**, entendible, bien estructurado y probado inmediatamente después de su implementación.
**NO SE BUSCA COMPLEJIDAD BAJO NINGUNA CIRCUNSTANCIA**, sino **MÁXIMA SIMPLICIDAD, funcionalidad y orden**.

## 🗄️ Base de Datos PostgreSQL SIMPLE

**Archivo:** `/context/estructura_de_db.sql`  
[context/estructura_de_db.sql](context/estructura_de_db.sql)

## ⚙️ Reglas Generales

1. **SIMPLICIDAD ABSOLUTA - REGLA DE ORO.**
   **SIEMPRE elegir la implementación MÁS SIMPLE posible.**
   Si hay dos formas de hacer algo, elegir la más básica y directa.
   Evitar cualquier dependencia, patrón complejo o abstracción innecesaria.
   **En caso de duda, SIEMPRE optar por lo más simple.**

2. **Estructura modular SIMPLE.**
   Todo el código debe estar dividido en módulos pequeños y reutilizables.
   Cada módulo debe tener una única responsabilidad.
   **Los módulos deben ser tan simples que se entiendan de un vistazo.**

3. **Comentarios explicativos antes de cada función o bloque.**
   Siempre escribir un comentario con triple comilla (`''' ... '''`) antes de implementar código nuevo.
   **Los comentarios deben ser simples y directos.**
   **Ejemplo:**

   ```python
   '''
   Función que calcula el promedio de una lista de números
   '''
   def calcular_promedio(lista):
       return sum(lista) / len(lista)
   ```

4. **Base de datos existente.**
   Todos los DDL (estructura de las tablas de la base de datos) se encuentran en:

   ```
   /context/estructura_de_db.sql
   ```

   Cualquier interacción con la base de datos debe basarse estrictamente en esa estructura.
   **Usar SOLO las tablas y campos que ya existen. NO agregar complejidad.**


5. **Estilo del código - MÁXIMA SIMPLICIDAD.**

   * **Mantener el código lo MÁS SIMPLE posible.**
   * **Usar nombres claros y descriptivos en funciones, variables y archivos.**
   * **Evitar comentarios redundantes.**
   * **Usar el mismo formato de documentación en todo el proyecto.**
   * **Siempre que sea posible, incluir ejemplos simples dentro de los comentarios.**
   * **NO usar patrones complejos, decoradores avanzados o abstracciones innecesarias.**

6. **Ejecución paso a paso SIMPLE.**
   Antes de implementar algo, planear brevemente el flujo con pseudocódigo o comentarios simples.
   **Esto sirve como guía para mantener el código ordenado y SIMPLE.**

## 🧩 Comportamiento Esperado del Agente

* **SIEMPRE pensar: "¿Cuál es la forma MÁS SIMPLE de hacer esto?"**
* Antes de escribir código, **pensar en la estructura modular MÁS SIMPLE** que tendrá el componente.
* Si una tarea puede dividirse, **dividirla en funciones pequeñas y SIMPLES**.
* Siempre **documentar con `''' ... '''`** antes de cada bloque de código.
* En caso de modificar funciones existentes, actualizar sus tests si es necesario.
* El agente debe ser coherente con la estructura del proyecto y no alterar el orden de carpetas.
* **NUNCA implementar algo complejo cuando existe una alternativa simple.**

---

## 🧪 Buenas Prácticas

* **Pensar SIMPLE:** cada función debe tener una única tarea básica.
* **Probar SIMPLE:** cada nueva implementación debe ser acompañada de un test básico.
* **Comentar con propósito SIMPLE:** los comentarios deben explicar el "por qué" de manera directa.
* **Revisar antes de continuar:** antes de pasar a otro módulo, confirmar que los tests existentes pasan correctamente.
* **Mantener consistencia SIMPLE:** todos los archivos deben seguir el mismo estilo básico de nombrado, estructura y formato.
* **REGLA FINAL: Si algo parece complejo, buscar una alternativa más simple.**

---

## 🚀 Objetivo Final

El resultado final debe ser un proyecto **EXTREMADAMENTE SIMPLE, ordenado, modular y demostrable**, que refleje buenas prácticas básicas de programación universitaria.
Debe ser **tan simple que cualquier persona pueda entenderlo completamente** sin necesitar explicaciones adicionales.

## 🔴 RECORDATORIO IMPORTANTE

**ESTE ES UN PROYECTO DE DEMOSTRACIÓN UNIVERSITARIA**
**LA SIMPLICIDAD ES MÁS IMPORTANTE QUE LA SOFISTICACIÓN**
**EN CASO DE DUDA, SIEMPRE ELEGIR LO MÁS BÁSICO Y DIRECTO**
