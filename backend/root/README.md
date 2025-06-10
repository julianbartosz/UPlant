# UPlant Backend

UPlant is a plant management application that helps users track and care for their plants. This document provides information about the backend architecture, setup, and development processes.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Running Tests](#running-tests)
- [Common Development Tasks](#common-development-tasks)

## Architecture Overview

UPlant's backend is built using Django 4.2 with Django REST Framework. The application is organized into the following modules:

- **User Management**: Handles user authentication, registration, and profile management
- **Plants**: Manages plant data, species information, and care instructions
- **Gardens**: Allows users to organize their plants into different gardens or collections
- **Community**: Enables social features, sharing, and community interactions
- **Notifications**: Manages user notifications and reminders
- **Core**: Contains shared functionality used across the application

The system uses a MySQL database for data storage and supports authentication via email/password and Google OAuth. The backend exposes a RESTful API consumed by the React frontend.

### Technology Stack

- **Framework**: Django 4.2
- **API**: Django REST Framework 
- **Database**: MySQL
- **Authentication**: Django AllAuth, Token Authentication
- **Testing**: Pytest, Factory Boy
- **Deployment**: Docker

## Setup and Installation

### Prerequisites

- Python 3.10+
- MySQL Server
- Docker (optional)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd UPlant/backend/root
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file in the `djangoProject1` directory (see [Environment Variables](#environment-variables))

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Using Docker

You can also use Docker to set up the development environment:

```bash
# From the project root
docker-compose up -d
```

## Environment Variables

Create a `.env` file in the `djangoProject1` directory with the following variables:

```
# Django settings
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DATABASE_NAME=uplant_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
SSL_CERT=path/to/cert/DigiCertGlobalRootCA.crt.pem

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@uplant.com
```

## API Documentation

UPlant exposes a RESTful API for frontend interaction. The main API endpoints are organized by app:

### User Management API

- `POST /api/users/register/`: Register a new user
- `POST /api/users/login/`: Log in a user and receive an authentication token
- `GET /api/users/profile/`: Get current user profile
- `PUT /api/users/profile/`: Update user profile

### Plants API

- `GET /api/plants/`: List all plants in the system
- `GET /api/plants/{id}/`: Get details of a specific plant
- `POST /api/plants/`: Create a new plant
- `PUT /api/plants/{id}/`: Update a plant
- `DELETE /api/plants/{id}/`: Delete a plant

### Gardens API

- `GET /api/gardens/`: List user gardens
- `POST /api/gardens/`: Create a new garden
- `GET /api/gardens/{id}/`: Get garden details
- `PUT /api/gardens/{id}/`: Update garden
- `DELETE /api/gardens/{id}/`: Delete garden
- `POST /api/gardens/{id}/plants/`: Add a plant to a garden

### Community API

- `GET /api/community/posts/`: List community posts
- `POST /api/community/posts/`: Create a post
- `GET /api/community/posts/{id}/`: Get post details
- `POST /api/community/posts/{id}/comments/`: Add a comment to a post

### Notifications API

- `GET /api/notifications/`: List user notifications
- `PUT /api/notifications/{id}/read/`: Mark notification as read

For detailed API documentation with request/response formats, you can access the browsable API at:
- Development: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/ (when configured)

## Database Schema

The UPlant database consists of the following main models:

### User Management
- **User**: Extended Django user model with profile information
  - Fields: email, first_name, last_name, profile_picture, etc.

### Plants
- **Plant**: Represents a specific plant instance owned by a user
  - Fields: name, species, description, image, water_frequency, etc.
- **Species**: General plant species information
  - Fields: common_name, scientific_name, care_instructions, etc.

### Gardens
- **Garden**: A collection of plants
  - Fields: name, description, image, owner, etc.
- **GardenPlant**: Relationship between gardens and plants with garden-specific data
  - Fields: garden, plant, location_in_garden, date_added, etc.

### Community
- **Post**: User posts in the community
  - Fields: title, content, image, author, created_at, etc.
- **Comment**: Comments on posts
  - Fields: post, author, content, created_at, etc.

### Notifications
- **Notification**: System notifications for users
  - Fields: user, message, created_at, read, type, etc.

## Running Tests

UPlant uses pytest for testing. Tests are located in each app's `tests` directory.

### Running All Tests

```bash
# From the backend/root directory
pytest
```

### Running Tests for a Specific App

```bash
pytest gardens/
```

### Running Tests with Coverage

```bash
pytest --cov=.
```

### Generating Coverage Report

```bash
pytest --cov=. --cov-report=html
```

The coverage report will be available in the `htmlcov` directory.

## Common Development Tasks

### Creating a New App

```bash
python manage.py startapp new_app_name
```

After creating a new app:
1. Add it to `INSTALLED_APPS` in `djangoProject1/settings.py`
2. Create URLs and register them in the main `urls.py`

### Making Database Changes

1. Create or modify models in `models.py`
2. Create migrations:
   ```bash
   python manage.py makemigrations
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```

### Creating a Superuser

```bash
python manage.py createsuperuser
```

### Running Management Commands

List all commands:
```bash
python manage.py help
```

### Accessing the Django Shell

```bash
python manage.py shell
```

For enhanced shell with additional imports:
```bash
python manage.py shell_plus
```

### Running the Development Server

```bash
python manage.py runserver
```

### Common Issues and Solutions

1. **Database Connection Issues**:
   - Ensure MySQL server is running
   - Verify credentials in `.env` file
   - Check SSL certificate path

2. **Migration Errors**:
   - Try resetting migrations: `python manage.py migrate app_name zero`
   - Then remigrate: `python manage.py migrate app_name`

3. **Authentication Issues**:
   - Ensure `AUTHENTICATION_BACKENDS` are properly configured
   - Check token expiration settings