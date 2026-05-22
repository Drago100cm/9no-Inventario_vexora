# Vexora

Proyecto Django llamado `Vexora` para la administración de usuarios, grupos, empresas y configuración del sitio.

## Estructura del proyecto

- `manage.py` - comando principal de Django.
- `config/` - configuración del proyecto Django.
- `vexora/` - aplicación principal con modelos, vistas, urls y formularios.
- `Templates/` - plantillas HTML para la interfaz.
- `static/` - archivos estáticos.
- `requerimientos.txt` - dependencias del proyecto.

## Requisitos

- Python 3.8+ (o versión compatible con Django usada en el proyecto)
- Virtualenv opcional pero recomendado

## Configuración local

1. Clona el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd vexora
```

2. Crea un entorno virtual:

```bash
python -m venv .venv
```

3. Activa el entorno virtual:

- Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

- Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

4. Instala las dependencias:

```bash
pip install -r requerimientos.txt
```

5. Aplica migraciones:

```bash
python manage.py migrate
```

6. Crea un superusuario (opcional):

```bash
python manage.py createsuperuser
```

7. Ejecuta el servidor:

```bash
python manage.py runserver
```

8. Abre el navegador en:

```text
http://127.0.0.1:8000/
```

## Notas

- No incluyas la carpeta del entorno virtual `.venv` ni archivos temporales en Git.
- Si usas variables de entorno, añade un archivo `.env` y agrégalo al `.gitignore`.
