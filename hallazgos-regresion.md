# Mediciones para la pata de regresión

Fecha: **7 de septiembre de 2026**. Medido sobre el censo congelado
(N = 2036 issues cerrados, hasta el 30 de agosto de 2026).

Estas cifras no entran en el APF1, que se cierra en los intervalos de confianza.
Se midieron para contestar una sola pregunta antes de comprometer el tema del
ciclo: **¿el caso aguanta el análisis de regresión que exige el proyecto final?**
La respuesta es sí, pero no con las variables obvias.

---

## Advertencia previa: los campos que la regresión necesitará no están commiteados

`datos/censo.json` es la proyección a cinco campos, y es lo único que el
repositorio guarda. La respuesta cruda de la API —`datos/censo-crudo.json`,
11 MB— está **gitignorada y vive solo en la máquina donde se descargó**.

| Campo | ¿Commiteado? | ¿Lo necesita la regresión? |
|---|---|---|
| `number`, `created_at`, `closed_at` | sí | sí, definen la variable dependiente |
| `comments` | sí | sí, es el predictor con más recorrido |
| `state_reason` | sí | sí, como covariable de control |
| `reactions.total_count` | **no** | sí, es el predictor de mayor correlación |
| `labels` | **no** | sí |
| `author_association` | **no** | sí, para las comparaciones del APF2 |
| `body`, `title` | **no** | no, resultaron inútiles (ver abajo) |

Esto importa porque **el censo no se puede volver a bajar**: el repositorio sigue
vivo y el conteo del buscador, consultado hoy, ya devuelve 2042 en vez de 2036.
Si el archivo crudo se pierde, los N = 2036 registros con reacciones y etiquetas
no se recuperan nunca. Antes de tocar el APF2 hay que **ampliar la proyección
commiteada** a los campos de la tabla y volver a generar `censo.json` desde el
crudo, sin descargar nada.

---

## Correlaciones a nivel de issue

Coeficiente de Pearson entre cada predictor candidato y el tiempo de resolución,
sobre el censo completo. La columna log-log aplica logaritmo natural a las horas
y `log(1 + x)` a los predictores, que tienen ceros.

| Predictor | r crudo | r con log(horas) | r log-log |
|---|---|---|---|
| Reacciones (`reactions.total_count`) | +0,095 | +0,121 | **+0,351** |
| Comentarios (`comments`) | +0,143 | +0,223 | **+0,270** |
| N.º de etiquetas | +0,112 | +0,198 | +0,198 |
| Longitud del cuerpo | +0,005 | +0,012 | +0,045 |
| Longitud del título | +0,021 | +0,018 | +0,026 |
| N.º de asignados | −0,020 | −0,022 | −0,025 |

**Cómo se lee esto.** Con una muestra de n = 100 el valor crítico de r al 5 % de
significancia es ≈ 0,197. Las variables **en crudo no llegan**: una regresión de
horas contra comentarios sobre la muestra saldría no significativa. Solo en
escala logarítmica los dos primeros predictores superan el umbral con holgura, y
aun así explican poco: r = 0,351 es un R² de 0,12.

La transformación logarítmica no es un truco para forzar el resultado. Está
justificada por la asimetría de la variable, que el propio APF1 documenta: la
media es 1455,7 h y la mediana 135,0 h. Es una distribución de cola larga, y el
logaritmo es la transformación estándar para ese caso.

---

## Agregación mensual: la opción más sólida del censo actual

Agrupando los issues por mes de apertura y quedándose con los meses de al menos
5 registros (**49 meses**, de enero de 2019 a agosto de 2026):

| Relación | r |
|---|---|
| Volumen del mes vs. mediana de horas | −0,394 |
| Volumen del mes vs. log(mediana de horas) | −0,303 |
| **log(volumen) vs. log(mediana de horas)** | **−0,445** |

R² ≈ 0,20 y claramente significativa con n = 49. Además es interpretable sin
retorcer nada: **los meses de más actividad son los meses de triaje más rápido**,
que es exactamente la clase de afirmación que el informe necesita para hablar de
capacidad de respuesta del equipo.

El costo es que cambia la unidad de análisis, de issue a mes. Hay que decirlo en
la metodología, no deslizarlo.

---

## Lo que se probó y no funcionó

- **Carga de trabajo (backlog).** Issues abiertos y sin cerrar en el instante en
  que se creó cada uno, calculado por búsqueda binaria sobre las series de
  aperturas y cierres. Media 111,5 issues, máximo 220. Correlación con las horas:
  **+0,031**, y −0,012 en logaritmo. Nula. La intuición de que un backlog grande
  retrasa la resolución no aparece en estos datos.
- **Tendencia temporal.** Índice de mes contra log(horas): **−0,085**. El proceso
  no se acelera ni se frena de forma sostenida a lo largo de los siete años.
- **Longitud del texto.** Ni el cuerpo ni el título dicen nada (r ≈ 0). Se
  descartan como predictores.

---

## Variable pendiente de bajar: tiempo hasta la primera respuesta

Es el predictor que falta y el que, con casi total seguridad, sostiene la
regresión del proyecto final: cuánto tarda el equipo en contestar por primera
vez, frente a cuánto tarda en cerrar. No está en el censo.

Se obtiene del endpoint de comentarios, **una llamada por issue**. Para los 100
de la muestra son 100 llamadas, trivial dentro del límite autenticado de 5000 por
hora. Conviene bajarlo ahora y congelarlo junto al censo, no en noviembre.

---

## Definiciones operativas usadas en estas mediciones

- Tiempo de resolución: `closed_at − created_at`, en horas, sin redondeo.
- Logaritmo de las horas: natural, con las horas acotadas por abajo a 0,01 para
  el único caso de duración casi nula.
- Logaritmo de los predictores: `log(1 + x)`, porque todos admiten el cero.
- Mediana mensual: sobre las horas crudas, no sobre sus logaritmos.
- Correlación: Pearson. Sobre los 2036 registros del censo, no sobre la muestra.

---

## Descriptivos de referencia

| Medida | Valor |
|---|---|
| Media | 1455,7 h |
| Mediana | 135,0 h |
| Desviación estándar poblacional | 2951,3 h |
| Mínimo / máximo | 0,01 h / 23 856,8 h |
| Media de log(horas) | 4,744 |
| Desviación de log(horas) | 2,919 |

Reparto por `state_reason`: 1920 `completed`, 92 `not_planned`, 24 `duplicate`.

Reparto por `author_association`: 1541 `NONE`, 438 `CONTRIBUTOR`, 48 `MEMBER`,
9 `COLLABORATOR`. Este corte es el candidato natural para las comparaciones de
grupos del APF2.
