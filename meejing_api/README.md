# 覓境 API Backend

Backend implementation for **覓境｜Map-based 日誌社群平台**, built with Django 5 + Django REST Framework.  
It delivers the MVP feature set for personal journals, social discovery, and geo-based exploration with a SwiftUI-friendly REST API surface.

## Key Features

- **Accounts**: JWT authentication (SimpleJWT), profile management, visibility controls (private / friends / public).  
- **Journal Entries**: Map-first content with locations, tags, media placeholders, privacy, and publishing workflow.  
- **Locations & Tags**: User-curated places with search/filter support; reusable thematic tags.  
- **Social Layer**: Follow system, likes, comments (with soft-delete), favorites/collections, and engagement counters.  
- **Search**: Unified `/api/search/` endpoint returning entries, locations, and tags.  
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

### Journals (`/api/journals/…`)
- `locations/` – CRUD for user-curated places  
- `tags/` – manage/list journal tags  
- `entries/` – journal CRUD with filters, search, pagination  
  - `entries/mine/` – include drafts and private content for owner  
  - `entries/map/` – lightweight payload for map plotting  
  - `entries/summary/` – feed-friendly summaries  
  - `entries/{id}/publish/` – publish draft

### Social (`/api/social/…`)
- `follows/` – list followings, `POST` follow, `DELETE` by follow ID or `/to/{user_id}/`  
- `likes/` – `POST` like, `DELETE` by entry ID, `GET` liked entries  
- `comments/` – threaded comments with soft-delete by author/entry owner  
- `collections/` – favorites & custom collections, nested `entries/` add/remove/list  
- `collections/favorites/` – ensure + fetch default “Favorites” collection

### Global Search
- `GET /api/search/?q=espresso` – returns entries, locations, tags matching the query (≥2 chars) respecting visibility rules

## Data Model Highlights

- `accounts.User` (customized `AbstractUser`) extends profile metadata and home base coordinates.  
- `journals.Location`, `JournalEntry`, `JournalTag`, `JournalMedia` cover geo stories with UUIDs & engagement counters.  
- `social.Follow`, `Like`, `Comment`, `Collection`, `CollectionEntry` layer social interactions with signal-driven stats refresh.  
- Visibility (`private`, `friends`, `public`) centralized in `core.models.VisibilityChoices` and enforced across queries/permissions.

## Tests

`manage.py test` currently exercises:

- User model basics  
- Journal API workflows (location creation, tag assignment, privacy filtering)  
- Social interactions (follow gating, likes, comments, collections)  
- Search endpoint coverage

## Next Steps (Roadmap Ideas)

- File storage integration for images/video/audio uploads (S3, Cloudflare R2, etc.).  
- Push notifications & async tasks for activity updates.  
- Recommendation engine for “Random Explore” and personalized feeds.  
- Enhanced analytics (footprint statistics, travel streaks) and achievement system.  
- GraphQL or gRPC façade for SwiftUI subscriptions / streaming map updates.

---
Happy exploring! Each footprint now has a home on the map.
