# 覓境 API Backend
## **Warning: Under development!! Some apis are untested!!**

Backend implementation for **覓境｜Map-based 日誌社群平台**, built with Django 5 + Django REST Framework.  
It delivers the MVP feature set for personal journals, social discovery, and geo-based exploration with a SwiftUI-friendly REST API surface.

## Key Features

- **Accounts**: JWT authentication (SimpleJWT) plus profile visibility controls (private / friends / public).  
- **Map Places**: CRUD endpoints for geo-tagged places with per-place permissions.  
- **Place Posts**: Lightweight stories tied to places with simple visibility rules.  
- **Map API**: Dedicated endpoints for listing public places, fetching posts per place or user, editing/deleting places and posts.  
- **Search**: Unified `/api/search/` endpoint returning places and posts.  
- **OpenAPI Schema**: Auto-generated via drf-spectacular (`api-schema.yaml`) with Swagger UI at `/api/docs/`.

## Tech Stack

- Python 3.13, Django 5.2, Django REST Framework 3.16  
- Simple JWT, django-filter, django-cors-headers, drf-spectacular  
- Pillow for future media handling

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # optional admin access
python manage.py runserver
```

### Useful Commands

| Task | Command |
| --- | --- |
| Run unit tests | `python manage.py test` |
| Generate OpenAPI schema | `python manage.py spectacular --file api-schema.yaml` |
| Browse interactive docs | visit `http://localhost:8000/api/docs/` |
| Admin console | `http://localhost:8000/admin/` |

## API Overview

Base path: `/api/`

### Auth & Profiles (`/api/auth/…`)
- `POST /register/` – create account  
- `POST /token/`, `/token/refresh/`, `/token/verify/` – JWT flow  
- `GET/PATCH /me/` – authenticated profile detail/update  
- `GET /users/` – public directory with search & filters  
- `GET /users/{id}/stats/` – quick metrics per user

### Map (`/api/map/…`)
- `places/` – CRUD for places; `GET /places/public/` lists all public locations  
- `places/{id}/` – edit or delete a place (owner only)  
- `posts/` – CRUD for posts tied to places (`place_id` payload key)  
  - `GET /posts/by-place/<place_uuid>/` – posts for a place  
  - `GET /posts/by-user/<user_uuid>/` – posts written by a user  
  - `DELETE /posts/{id}/` – remove a post (author only)

### Global Search
- `GET /api/search/?q=espresso` – returns places and posts matching the query (≥2 chars) with visibility filtering

## Data Model Highlights

- `accounts.User` (customized `AbstractUser`) stores display names, avatars, and visibility preferences.  
- `map.Place` encapsulates geo coordinates, metadata, creator ownership, and visibility.  
- `map.Post` links user-authored stories to places with matching visibility rules.  
- Visibility (`private`, `friends`, `public`) centralized in `core.models.VisibilityChoices` and enforced across queries/permissions.

## Tests

`manage.py test` currently exercises:

- User model basics  
- Map API workflows (places/posts CRUD, restricted actions, public listings)  
- Search endpoint coverage

## Deploying to Vercel

1. **Install the Vercel CLI** (optional for local previews): `npm i -g vercel`.
2. **Set required environment variables** in the Vercel dashboard (`Project Settings → Environment Variables`):
   - `DEBUG=False`
   - `SECRET_KEY=<strong-random-string>`
   - `ALLOWED_HOSTS=.vercel.app,<your-custom-domain>`
   - `DATABASE_URL=<external-postgres-connection-string>`
   - `CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>`
   - `CSRF_TRUSTED_ORIGINS=https://<your-frontend-domain>,https://*.vercel.app`
3. **Provision a managed database** (e.g. Neon) and point `DATABASE_URL` at it—Vercel's storage is ephemeral.
4. (Optional) **Configure media storage** (S3, Cloudflare R2, etc.) and update `MEDIA_URL`/`MEDIA_ROOT` or storage backends accordingly.
5. Deploy with `vercel --prod` or through the Vercel dashboard. The build command runs `collectstatic` so hashed assets are served from `/staticfiles`.
6. After the first deploy, run migrations via `vercel ssh` or a CI step: `python manage.py migrate`.

> Note: The `routes` section in `vercel.json` serves collected static assets. User-uploaded media should live on external storage in production.

## Next Steps (Roadmap Ideas)

- File storage integration for images/video/audio uploads (S3, Cloudflare R2, etc.).  
- Push notifications & async tasks for activity updates.  
- Recommendation engine for “Random Explore” and personalized feeds.  
- Enhanced analytics (footprint statistics, travel streaks) and achievement system.  
- GraphQL or gRPC façade for SwiftUI subscriptions / streaming map updates.

---
Happy exploring! Each footprint now has a home on the map.
