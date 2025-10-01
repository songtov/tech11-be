# Alembic Setup Guide for New Team Members

This guide explains how to set up and use Alembic database migrations when cloning this repository.

## Initial Setup After Cloning

### 1. Install Dependencies
```bash
# Install project dependencies
uv sync
```

### 2. Check Alembic Status
```bash
# Check current migration status
uv run alembic current
```

### 3. Apply All Migrations
```bash
# Apply all pending migrations to create/update database
uv run alembic upgrade head
```

### 4. Verify Database
```bash
# Check that migrations were applied successfully
uv run alembic current
```

## Common Alembic Commands

### Check Migration Status
```bash
# See current migration version
uv run alembic current

# See migration history
uv run alembic history

# See pending migrations
uv run alembic show head
```

### Apply Migrations
```bash
# Apply all pending migrations
uv run alembic upgrade head

# Apply migrations up to a specific revision
uv run alembic upgrade <revision_id>

# Apply next migration only
uv run alembic upgrade +1
```

### Rollback Migrations
```bash
# Rollback to previous migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Rollback all migrations
uv run alembic downgrade base
```

### Create New Migrations
```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Create empty migration file
uv run alembic revision -m "Description of changes"
```

## Workflow for Database Changes

### When You Modify Models:
1. **Make changes** to your SQLAlchemy models in `app/models/`
2. **Generate migration**:
   ```bash
   uv run alembic revision --autogenerate -m "Add new field to research model"
   ```
3. **Review the migration** file in `alembic/versions/`
4. **Apply the migration**:
   ```bash
   uv run alembic upgrade head
   ```

### When You Pull Changes with New Migrations:
1. **Pull latest code** from repository
2. **Check for new migrations**:
   ```bash
   uv run alembic current
   uv run alembic show head
   ```
3. **Apply new migrations**:
   ```bash
   uv run alembic upgrade head
   ```

## Troubleshooting

### Database Out of Sync
If you get errors about database being out of sync:
```bash
# Check current status
uv run alembic current

# See what migrations are available
uv run alembic history

# Apply missing migrations
uv run alembic upgrade head
```

### Migration Conflicts
If there are migration conflicts:
```bash
# Check migration history
uv run alembic history --verbose

# You may need to resolve conflicts manually
# Contact the team lead for assistance
```

### Fresh Database Setup
If you need to start with a fresh database:
```bash
# Delete existing database file (SQLite)
rm app.db

# Apply all migrations from scratch
uv run alembic upgrade head
```

## Environment Configuration

The database URL is configured in `app/core/config.py` and can be overridden with environment variables:

```bash
# Set custom database URL
export DATABASE_URL="sqlite:///./my_custom.db"

# Or create a .env file
echo "DATABASE_URL=sqlite:///./my_custom.db" > .env
```

## Best Practices

1. **Always review** auto-generated migrations before applying
2. **Test migrations** on a copy of production data when possible
3. **Never edit** migration files that have been applied to production
4. **Use descriptive names** for migration messages
5. **Backup database** before major migrations
6. **Coordinate** with team when making schema changes

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv run alembic current` | Show current migration version |
| `uv run alembic history` | Show migration history |
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic downgrade -1` | Rollback one migration |
| `uv run alembic revision --autogenerate -m "message"` | Create new migration |
