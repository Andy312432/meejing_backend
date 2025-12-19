# 覓境 API Backend

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

Fill in the .env first.

```bash
cd meejing_api
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

- Base path: `/api/`
- See `/api/docs` For more information.

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


## Next Steps (Roadmap Ideas powered by chatGPT)

- Push notifications & async tasks for activity updates.  
- Recommendation engine for “Random Explore” and personalized feeds.  
- Enhanced analytics (footprint statistics, travel streaks) and achievement system.  
- GraphQL or gRPC façade for SwiftUI subscriptions / streaming map updates.

---
Happy exploring! Each footprint now has a home on the map.
