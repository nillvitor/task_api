
# Task Management API

A RESTful API built with FastAPI for managing tasks with user authentication and SQLite database.

## Features

- User authentication with JWT tokens
- CRUD operations for tasks
- PostgreSQL database with SQLAlchemy ORM
- Password hashing with bcrypt
- Token-based authentication
- Pagination support for task listing

## API Configuration

The API uses the following configuration settings:

- `API_V1_STR`: "/api/v1" (API version prefix)
- `PROJECT_NAME`: "Task Management API"
- `SECRET_KEY`: JWT secret key (set in .env)
- `ALGORITHM`: "HS256" (JWT encryption algorithm)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30 (JWT token expiration time)

## Database Configuration

PostgreSQL connection settings (configured via .env):

- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port
- `POSTGRES_DB`: Database name

## Requirements

- Python 3.12+
- FastAPI
- SQLAlchemy
- Python-Jose
- Passlib
- uvicorn
- Other dependencies listed in requirements.txt

## Installation

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

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /token` - Get access token
- `POST /users` - Create new user

### Tasks
- `GET /tasks` - List all tasks (paginated)
- `GET /tasks/{task_id}` - Get specific task
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

## Database Schema

### Users Table
- id (Integer, Primary Key)
- username (String, Unique)
- hashed_password (String)

### Tasks Table
- id (Integer, Primary Key)
- title (String)
- description (String)
- status (String)
- created_at (DateTime)
- updated_at (DateTime)
- owner_id (Integer, Foreign Key to users.id)

## Security

- Passwords are hashed using bcrypt
- Authentication uses JWT tokens
- Token expiration set to 30 minutes
- Protected endpoints require valid JWT token

## Development

The project uses:
- FastAPI for the web framework
- SQLAlchemy for ORM
- Pydantic for data validation
- JWT for authentication

## License

Copyright 2024 [Your Name or Organization]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
# Task Management API

A RESTful API built with FastAPI for managing tasks with user authentication and SQLite database.

## Features

- User authentication with JWT tokens
- CRUD operations for tasks
- PostgreSQL database with SQLAlchemy ORM
- Password hashing with bcrypt
- Token-based authentication
- Pagination support for task listing

## API Configuration

The API uses the following configuration settings:

- `API_V1_STR`: "/api/v1" (API version prefix)
- `PROJECT_NAME`: "Task Management API"
- `SECRET_KEY`: JWT secret key (set in .env)
- `ALGORITHM`: "HS256" (JWT encryption algorithm)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30 (JWT token expiration time)

## Database Configuration

PostgreSQL connection settings (configured via .env):

- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port
- `POSTGRES_DB`: Database name

## Requirements

- Python 3.12+
- FastAPI
- SQLAlchemy
- Python-Jose
- Passlib
- uvicorn
- Other dependencies listed in requirements.txt

## Installation

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

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /token` - Get access token
- `POST /users` - Create new user

### Tasks
- `GET /tasks` - List all tasks (paginated)
- `GET /tasks/{task_id}` - Get specific task
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

## Database Schema

### Users Table
- id (Integer, Primary Key)
- username (String, Unique)
- hashed_password (String)

### Tasks Table
- id (Integer, Primary Key)
- title (String)
- description (String)
- status (String)
- created_at (DateTime)
- updated_at (DateTime)
- owner_id (Integer, Foreign Key to users.id)

## Security

- Passwords are hashed using bcrypt
- Authentication uses JWT tokens
- Token expiration set to 30 minutes
- Protected endpoints require valid JWT token

## Development

The project uses:
- FastAPI for the web framework
- SQLAlchemy for ORM
- Pydantic for data validation
- JWT for authentication

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
