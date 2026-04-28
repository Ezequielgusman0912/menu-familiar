# Menu familiar

Aplicacion Django para organizar el menu semanal y generar la lista del super.

## Publicar en Railway

1. Subi este proyecto a un repositorio en GitHub.
2. En Railway, crea un proyecto nuevo desde ese repo.
3. Agrega un servicio `PostgreSQL`.
4. En el servicio web, configura estas variables:

```env
DEBUG=False
SECRET_KEY=pon-aca-una-clave-larga-y-random
ALLOWED_HOSTS=tu-dominio.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-dominio.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

5. Genera el dominio publico desde Railway.
6. Railway va a usar `railway.json` y levantar la app con migraciones incluidas.

## Local

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
