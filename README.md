
# Task Management API

A RESTful API built with FastAPI for managing tasks with user authentication, PostgreSQL database, and Redis caching.

## Features

- User authentication with JWT tokens
- CRUD operations for tasks
- PostgreSQL database with SQLAlchemy ORM
- Redis caching for improved performance
- Password hashing with bcrypt
- Token-based authentication
- Pagination support for task listing
- Docker support for easy deployment
- Command Line Interface (CLI) for easy interaction

## API Configuration

The API uses the following configuration settings:

- `API_V1_STR`: "/api/v1" (API version prefix)
- `PROJECT_NAME`: "Task Management API"
- `SECRET_KEY`: JWT secret key (set in .env)
- `ALGORITHM`: "HS256" (JWT encryption algorithm)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30 (JWT token expiration time)

## Service Configuration

### Database Configuration (PostgreSQL)
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name

### Cache Configuration (Redis)
- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `CACHE_EXPIRE_IN_SECONDS`: Cache TTL in seconds (default: 60)

## Requirements

### Local Development
- Python 3.12+
- FastAPI
- SQLAlchemy
- Python-Jose
- Passlib
- uvicorn
- Redis
- Other dependencies listed in requirements.txt

### Docker Deployment
- Docker
- Docker Compose

## Installation and Setup

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd task_api
```

2. Create a `.env` file in the project root with the following variables:
```
# API Settings
SECRET_KEY=your-secret-key-here

# PostgreSQL Settings
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=taskdb

# Redis Settings (optional - defaults will be used if not set)
REDIS_HOST=redis
REDIS_PORT=6379
CACHE_EXPIRE_IN_SECONDS=60
```

3. Build and start the containers:
```bash
# Clean up any existing containers and volumes
docker-compose down --volumes --remove-orphans

# Build and start services
docker-compose up -d --build
```

The API will be available at http://localhost:8000

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd task_api
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file as described above, but use:
```
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

5. Start the required services:
```bash
# Using Docker for PostgreSQL and Redis only
docker-compose up -d db redis
```

6. Start the server:
```bash
uvicorn app.main:app --reload
```

## Docker Compose Services

The application consists of three services:

- `api`: The FastAPI application
  - Builds from the Dockerfile
  - Exposes port 8000
  - Depends on database and cache services

- `db`: PostgreSQL database
  - Uses postgres:latest image
  - Persistent volume for data storage
  - Includes health checks

- `redis`: Redis cache
  - Uses redis:alpine image
  - Persistent volume for data
  - Includes health checks
  - Improves API performance through caching

## Development with Docker

### Useful Commands

Start services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

Clean restart:
```bash
docker-compose down --volumes --remove-orphans
docker-compose up -d --build
```

Access PostgreSQL CLI:
```bash
docker-compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

Access Redis CLI:
```bash
docker-compose exec redis redis-cli
```

## API Endpoints

### Authentication
- `POST /token` - Get access token
- `POST /users` - Create new user

### Tasks
- `GET /tasks` - List all tasks (paginated, cached)
- `GET /tasks/{task_id}` - Get specific task (cached)
- `POST /tasks` - Create new task
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task

## Usage Examples

### Create a New User
```bash
curl -X 'POST' \
  'http://localhost:8000/users' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "testuser",
  "password": "testpass"
}'
```

### Get Access Token
```bash
curl -X 'POST' \
  'http://localhost:8000/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=testuser&password=testpass'
```

### Create a Task
```bash
curl -X 'POST' \
  'http://localhost:8000/tasks' \
  -H 'Authorization: Bearer <your-token>' \
  -H 'Content-Type: application/json' \
  -d '{
  "title": "Test Task",
  "description": "Task description",
  "status": "pending"
}'
```

## Task Status

Tasks can have one of three states:
- `pending`: Task is waiting to be started
- `in_progress`: Task is currently being worked on
- `done`: Task is completed

Example of creating a task with status:
```bash
curl -X 'POST' \
  'http://localhost:8000/tasks' \
  -H 'Authorization: Bearer <your-token>' \
  -H 'Content-Type: application/json' \
  -d '{
  "title": "Test Task",
  "description": "Task description",
  "status": "pending"
}'
```

## Database Schema

### Users Table
- id (Integer, Primary Key)
- username (String, Unique)
- hashed_password (String)

### Tasks Table
- id (Integer, Primary Key)
- title (String)
- description (String)
- status (String, one of: "pending", "in_progress", "done")
- created_at (DateTime)
- updated_at (DateTime)
- owner_id (Integer, Foreign Key to users.id)

## Caching

The API uses Redis for caching with the following features:
- Task listing and individual task retrieval are cached
- Default cache TTL: 60 seconds
- Automatic cache invalidation on task updates/deletes
- Configurable cache settings via environment variables

## Security

- Passwords are hashed using bcrypt
- Authentication uses JWT tokens
- Token expiration set to 30 minutes
- Protected endpoints require valid JWT token
- CORS middleware configured for security

## Development

The project uses:
- FastAPI for the web framework
- SQLAlchemy for ORM
- Pydantic for data validation
- JWT for authentication
- Redis for caching
- Docker for containerization

## Command Line Interface (CLI)

The project includes a Go-based CLI tool for interacting with the API.

### Building the CLI

```bash
cd cli
go build -o task-cli
```

### CLI Commands

#### Authentication
- `login` - Authenticate with the API
  ```bash
  # Interactive (secure) mode - will prompt for password
  task-cli login -u username

  # Non-interactive mode
  task-cli login -u username -p password
  ```
- `logout` - Clear stored authentication
  ```bash
  task-cli logout
  ```

#### Tasks
- `create` - Create a new task
  ```bash
  task-cli create -t "Task Title" -d "Task Description" -s pending
  ```
- `list` - List all tasks
  ```bash
  task-cli list
  ```
- `get` - Get a specific task
  ```bash
  task-cli get -i task_id
  ```
- `update` - Update an existing task
  ```bash
  task-cli update -i task_id -t "New Title" -d "New Description" -s in_progress
  ```
- `delete` - Delete a task
  ```bash
  task-cli delete -i task_id
  ```

### CLI Configuration

The CLI stores its configuration in `~/.task-cli.json` with the following settings:
- `api_base_url`: API endpoint (default: "http://localhost:8000")
- `access_token`: JWT token for authentication (managed automatically by login/logout commands)

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
