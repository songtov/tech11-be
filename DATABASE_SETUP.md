# Database Setup for Research Model

This project uses SQLAlchemy with Alembic for database management and version control.

## Database Model

The `Research` model includes the following fields:
- `id`: Primary key (auto-incrementing integer)
- `title`: Research paper title (string, max 500 characters)
- `abstract`: Research paper abstract/summary (text)
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

## Database Configuration

- **Database URL**: Configured in `app/core/config.py` (defaults to SQLite: `sqlite:///./app.db`)
- **Database Engine**: SQLAlchemy with SQLite (can be changed to PostgreSQL, MySQL, etc.)

## Alembic Migrations

### Initial Setup
The database was initialized with the following command:
```bash
uv run alembic init alembic
```

### Creating Migrations
To create a new migration after model changes:
```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations
To apply pending migrations:
```bash
uv run alembic upgrade head
```

### Rolling Back Migrations
To rollback to a previous migration:
```bash
uv run alembic downgrade <revision_id>
```

## API Endpoints

The research model provides the following REST API endpoints:

- `POST /research` - Create a new research entry
- `GET /research` - Get all research entries (with pagination)
- `GET /research/{research_id}` - Get a specific research entry
- `PUT /research/{research_id}` - Update a research entry
- `DELETE /research/{research_id}` - Delete a research entry

## Example Usage

### Create a research entry:
```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"title": "Machine Learning in Healthcare", "abstract": "This paper explores..."}'
```

### Get all research entries:
```bash
curl -X GET "http://localhost:8000/research"
```

### Get a specific research entry:
```bash
curl -X GET "http://localhost:8000/research/1"
```

## File Structure

```
app/
├── core/
│   ├── config.py          # Configuration settings
│   └── database.py        # Database connection and session management
├── models/
│   └── research.py        # SQLAlchemy model definitions
├── schemas/
│   └── research.py        # Pydantic schemas for API validation
├── services/
│   └── research.py        # Business logic and CRUD operations
└── routes/
    └── research.py        # FastAPI route handlers

alembic/
├── versions/              # Migration files
└── env.py                 # Alembic environment configuration
```
