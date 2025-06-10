# UPlant Project Onboarding Guide

Welcome to the UPlant project! This guide will help you set up your development environment and understand the project structure.

## Project Overview

UPlant is a plant management application that helps users track and care for their plants. The application consists of:

- **Frontend**: React-based UI built with Vite
- **Backend**: Django REST API
- **Database**: MySQL

## New Developer Setup Checklist

- [ ] Clone the repository
- [ ] Install backend dependencies
- [ ] Configure environment variables
- [ ] Set up the database
- [ ] Run database migrations
- [ ] Create a superuser
- [ ] Install frontend dependencies
- [ ] Run the development servers
- [ ] Access the application

## Development Environment Requirements

### General Requirements

- Git
- Docker and Docker Compose (optional, for containerized setup)
- Code editor (VS Code recommended)

### Backend Requirements

- Python 3.10+
- MySQL Server
- SSL Certificate (included in repo)

### Frontend Requirements

- Node.js (v16.x or higher)
- npm (v8.x or higher)

## Step-by-Step Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd UPlant
```

### 2. Backend Setup

#### Option A: Manual Setup

1. Create and activate a virtual environment:

```bash
cd backend/root
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the `djangoProject1` directory with the following variables:

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

4. Set up the database:

```bash
# Create the MySQL database
mysql -u root -p
CREATE DATABASE uplant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON uplant_db.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

5. Run database migrations:

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

#### Option B: Docker Setup

If you prefer using Docker, you can set up the backend using Docker Compose:

```bash
# From the project root
docker-compose up -d
```

### 3. Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:5173](http://localhost:5173) by default.

## Accessing the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/
- **Admin Interface**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/ (when configured)

## Project Structure

### Backend Structure

```
backend/
    root/
        community/         # Community forum functionality
        core/              # Core functionality and shared utilities
        djangoProject1/    # Main Django project settings
        gardens/           # Garden management functionality
        notifications/     # User notifications system
        plants/            # Plant data and management
        services/          # Shared services
        static/            # Static files
        templates/         # HTML templates
        user_management/   # User auth and profile management
```

### Frontend Structure

```
frontend/
    src/
        assets/            # Static assets like images and global styles
        components/        # Reusable UI components
        constants/         # Application constants and configuration
        context/           # React context providers
        hooks/             # Custom React hooks
        pages/             # Page components that correspond to routes
        styles/            # Global and component-specific styles
        App.jsx            # Main application component
        index.jsx          # Application entry point
```

## Common Issues and Solutions

### Backend Issues

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

### Frontend Issues

1. **Node Module Issues**:
   - Try clearing node modules and reinstalling: 
     ```
     rm -rf node_modules
     npm install
     ```

2. **Build Errors**:
   - Check for ESLint errors: `npm run lint`
   - Update dependencies if needed

3. **API Connection Issues**:
   - Ensure backend server is running
   - Check CORS settings in Django
   - Verify API endpoint URLs in frontend constants

## Testing

### Backend Testing

Run backend tests using pytest:

```bash
cd backend/root
pytest
```

For test coverage report:

```bash
pytest --cov=. --cov-report=html
```

The coverage report will be available in the `htmlcov` directory.

### Frontend Testing

Run frontend tests:

```bash
cd frontend
npm test
```

## Team Contacts and Resources

### Core Team Members

- **Julian** - Fullstack Developer
- **Jason** - Backend Developer
- **Cainan** - Backend Developer
- **Beckett** - React Developer
- **Laura** - Database Manager
- **Alex** - Digital Artist

### Documentation Resources

- Backend Documentation: `/backend/root/README.md`
- Frontend Documentation: `/frontend/README.md`
- API Documentation: Available at http://localhost:8000/api/docs/ when running locally

### External Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- React Documentation: https://react.dev/
- Vite Documentation: https://vitejs.dev/

## Workflow and Conventions

1. **Git Workflow**
   - Create feature branches from `main`
   - Use descriptive branch names (e.g., `feature/user-notifications`)
   - Submit pull requests for review

2. **Code Style**
   - Backend: Follow PEP 8 guidelines
   - Frontend: Use ESLint and Prettier with project config

3. **Commit Messages**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable

## Deployment

The deployment process will be handled separately, but for local development, the setup described above should be sufficient.

---

If you encounter any issues not covered in this guide, please reach out to the team members listed above.