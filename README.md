# Menu familiar

Aplicacion Django para organizar el menu semanal y generar la lista del super.

## Publicar en Vercel

1. Subi este proyecto a un repositorio en GitHub.
2. En Vercel, importa el repo y deja el preset como `Django`.
3. Usa una base externa PostgreSQL, por ejemplo Neon o Supabase. No uses SQLite en Vercel para produccion porque el filesystem serverless no guarda cambios de forma persistente.
4. En Vercel, configura estas variables:

```env
DEBUG=False
SECRET_KEY=pon-aca-una-clave-larga-y-random
ALLOWED_HOSTS=.vercel.app
CSRF_TRUSTED_ORIGINS=https://tu-app.vercel.app
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

5. Despues del primer deploy, ejecuta las migraciones contra esa base:

```powershell
$env:DATABASE_URL="postgresql://user:password@host:5432/dbname"
$env:DEBUG="False"
python manage.py migrate
```

Vercel usa `vercel.json` para correr `collectstatic` durante el build.

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
