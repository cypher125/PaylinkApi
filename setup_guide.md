# PayLink Setup Guide

This guide provides step-by-step instructions for setting up the PayLink API for both local development and production deployment.

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Git
- pip (Python package manager)
- Virtual environment tool (venv, pipenv, or conda)

### Clone the Repository

```bash
# Clone the repository
git clone https://github.com/cypher125/PayLinkApi.git
cd PayLinkApi/backend
```

### Set Up a Virtual Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Set Up Environment Variables

Create a `.env` file in the backend directory by copying the example file:

```bash
cp .env.example .env
```

Edit the `.env` file and configure the following variables:

```
# Django settings
DEBUG=True
SECRET_KEY=your_secret_key_here

# Database settings
DB_URL=postgres://username:password@localhost:5432/paylink

# VTPass API settings
VTPASS_API_KEY=your_vtpass_api_key
VTPASS_PUBLIC_KEY=your_vtpass_public_key
VTPASS_SECRET_KEY=your_vtpass_secret_key
VTPASS_BASE_URL=https://sandbox.vtpass.com/api

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Set Up the Database

```bash
# Create a PostgreSQL database
createdb paylink

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser
```

### Run the Development Server

```bash
# Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

## Production Deployment

### Deploying to Render

#### Prerequisites

- A [Render](https://render.com) account
- A PostgreSQL database service on Render or elsewhere

#### Steps

1. **Create a PostgreSQL database on Render**

   - Go to the Render dashboard
   - Click on "New" and select "PostgreSQL"
   - Fill in the required fields:
     - Name: `paylink-db`
     - Database: `paylink`
     - User: Choose a username
     - Region: Choose a region close to your users
   - Note the database connection details (Internal Database URL)

2. **Create a Web Service for the API**

   - Go to the Render dashboard
   - Click on "New" and select "Web Service"
   - Connect your GitHub repository
   - Fill in the required fields:
     - Name: `paylinkapi`
     - Environment: Python
     - Build Command: `./build.sh`
     - Start Command: `gunicorn paylink.wsgi`
   - Add environment variables:
     ```
     DEBUG=False
     SECRET_KEY=your_secure_secret_key
     DB_URL=your_render_postgres_internal_url
     VTPASS_API_KEY=your_vtpass_api_key
     VTPASS_PUBLIC_KEY=your_vtpass_public_key
     VTPASS_SECRET_KEY=your_vtpass_secret_key
     VTPASS_BASE_URL=https://sandbox.vtpass.com/api
     CORS_ALLOWED_ORIGINS=https://yourfrontend.render.com,https://yourdomain.com
     ```

3. **Deploy the Service**

   - Click "Create Web Service"
   - Render will build and deploy your application
   - Once deployed, the API will be available at `https://paylinkapi.onrender.com`

### Deploying to Other Platforms

#### Heroku

1. **Create a Procfile**

   Create a file named `Procfile` in the backend directory:
   ```
   web: gunicorn paylink.wsgi
   ```

2. **Create an app on Heroku**

   ```bash
   heroku create paylinkapi
   ```

3. **Add a PostgreSQL database**

   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Configure environment variables**

   ```bash
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your_secure_secret_key
   heroku config:set VTPASS_API_KEY=your_vtpass_api_key
   heroku config:set VTPASS_PUBLIC_KEY=your_vtpass_public_key
   heroku config:set VTPASS_SECRET_KEY=your_vtpass_secret_key
   heroku config:set VTPASS_BASE_URL=https://sandbox.vtpass.com/api
   heroku config:set CORS_ALLOWED_ORIGINS=https://yourfrontend.herokuapp.com,https://yourdomain.com
   ```

5. **Deploy the application**

   ```bash
   git push heroku main
   ```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| DEBUG | Enable debug mode | `True` or `False` |
| SECRET_KEY | Django secret key | `django-insecure-your-secret-key` |
| DB_URL | Database connection URL | `postgres://user:pass@host:port/dbname` |
| VTPASS_API_KEY | VTPass API key | `your_vtpass_api_key` |
| VTPASS_PUBLIC_KEY | VTPass public key | `your_vtpass_public_key` |
| VTPASS_SECRET_KEY | VTPass secret key | `your_vtpass_secret_key` |
| VTPASS_BASE_URL | VTPass API base URL | `https://sandbox.vtpass.com/api` or `https://vtpass.com/api` |
| CORS_ALLOWED_ORIGINS | Comma-separated list of allowed origins | `http://localhost:3000,https://yourdomain.com` |

## Common Issues and Troubleshooting

### Database Connection Errors

- Ensure PostgreSQL is running
- Verify database credentials in the `.env` file
- Check that the database exists

### VTPass API Issues

- Verify API credentials
- Check if you're using the correct base URL (sandbox vs. production)
- Look for error responses in the logs

### CORS Errors

- Ensure your frontend origin is included in `CORS_ALLOWED_ORIGINS`
- Check for trailing slashes in the origin URLs

## Maintenance and Updates

### Update Dependencies

```bash
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt
```

### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collect Static Files (Production Only)

```bash
python manage.py collectstatic --no-input
``` 