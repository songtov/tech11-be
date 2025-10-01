# Tech11 Backend API

A FastAPI-based backend server built with modern Python tooling and best practices.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 📦 **uv** - Ultra-fast Python package manager
- 🧪 **pytest** - Testing framework with coverage reporting
- 🎨 **Code Quality** - Black, isort, and Ruff for formatting and linting
- 🔄 **Hot Reload** - Development server with automatic reloading
- 📊 **API Documentation** - Automatic OpenAPI/Swagger documentation

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installing uv

```bash
# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd tech11-be
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Development Server

```bash
uv run poe run
```

The server will start at `http://localhost:8000` with hot reload enabled.

## Available Endpoints

### API Endpoints

- `GET /` - Welcome message
- `GET /items/{item_id}` - Get item by ID with optional query parameter

### Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Development

### Project Structure

```
tech11-be/
├── app/
│   └── main.py          # FastAPI application
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Locked dependency versions
└── README.md           # This file
```

### Available Commands

The project uses [poethepoet](https://poethepoet.natn.io/) for task management:

```bash
# Run the development server
uv run poe run

# Run tests with coverage
uv run poe test

# Run tests in watch mode
uv run poe watch-test

# Format and lint code
uv run poe lint
```

### Code Quality

The project includes several tools for maintaining code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **Ruff** - Fast Python linter
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting

### Running Tests

```bash
# Run all tests
uv run poe test

# Run tests in watch mode (reruns on file changes)
uv run poe watch-test

# Run tests manually
uv run pytest
```

### Code Formatting and Linting

```bash
# Format and lint all code
uv run poe lint

# Run individual tools
uv run black .
uv run isort .
uv run ruff check .
```

## Environment Variables

Create a `.env` file in the project root for environment-specific configuration:

```bash
# Example .env file
DEBUG=true
LOG_LEVEL=info
```

## Production Deployment

### Using uvicorn

```bash
# Install production dependencies
uv sync --no-dev

# Run production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`uv run poe test && uv run poe lint`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub or contact the development team.
