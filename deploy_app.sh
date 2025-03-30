#!/bin/bash
set -x
set -e

# Check if instance_id.txt exists
if [ ! -f instance_id.txt ]; then
    echo "Error: instance_id.txt not found. Please run create_instance.sh first."
    exit 1
fi

# Check if .secrets file exists
if [ ! -f .secrets ]; then
    echo "Error: .secrets file not found. Please create it with NGINX_USERNAME and NGINX_PASSWORD."
    exit 1
fi

# Source the secrets file
source .secrets

# Read the instance ID and IP from the files
INSTANCE_ID=$(cat instance_id.txt)
PUBLIC_IP=$(cat instance_ip.txt)
YAML_FILE="resources.yaml"
LOCAL_SSH_KEY_PATH=$(grep 'local_ssh_key_path' $YAML_FILE | awk '{print $2}')

# Function to run commands on the remote instance
run_remote() {
    ssh -o StrictHostKeyChecking=no -i $LOCAL_SSH_KEY_PATH ubuntu@$PUBLIC_IP "$1"
}

# Function to copy files to the remote instance
copy_to_remote() {
    local src=$1
    local dest=$2
    
    if [ -d "$src" ]; then
        # For directories, use rsync with .gitignore exclusions
        rsync -av --exclude-from=.gitignore -e "ssh -o StrictHostKeyChecking=no -i $LOCAL_SSH_KEY_PATH" "$src/" "ubuntu@$PUBLIC_IP:$dest/"
    else
        # For single files, use scp
        scp -o StrictHostKeyChecking=no -i $LOCAL_SSH_KEY_PATH "$src" "ubuntu@$PUBLIC_IP:$dest"
    fi
}

# Update system and install required packages
echo "Updating system and installing required packages..."
run_remote "sudo apt-get update && sudo apt-get install -y nginx python3-venv"

# Generate self-signed SSL certificate if it doesn't exist
echo "Generating SSL certificate..."
run_remote "sudo mkdir -p /etc/nginx/ssl && sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/private.key -out /etc/nginx/ssl/certificate.crt -subj '/CN=$PUBLIC_IP'"

# Create password file for basic auth
echo "Creating password file for basic authentication..."
run_remote "echo '$NGINX_USERNAME:$(openssl passwd -apr1 $NGINX_PASSWORD)' | sudo tee /etc/nginx/.htpasswd"

# Configure Nginx
echo "Configuring Nginx..."
run_remote "sudo tee /etc/nginx/sites-available/spreadsheet_project << 'EOF'
server {
    listen 443 ssl;
    server_name $PUBLIC_IP;

    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Add basic authentication
    auth_basic \"Restricted Access\";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /home/ubuntu/spreadsheet_project/static/;
    }

    location /media/ {
        alias /home/ubuntu/spreadsheet_project/media/;
    }
}
EOF"

# Enable the site
run_remote "sudo ln -sf /etc/nginx/sites-available/spreadsheet_project /etc/nginx/sites-enabled/ && sudo rm -f /etc/nginx/sites-enabled/default"

# Create deployment directory and clean up any existing files
run_remote "rm -rf ~/spreadsheet_project && mkdir -p ~/spreadsheet_project"

# Copy application files
echo "Copying application files..."
copy_to_remote "requirements.txt" "~/spreadsheet_project/"
copy_to_remote "manage.py" "~/spreadsheet_project/"

# Copy project files
run_remote "mkdir -p ~/spreadsheet_project/spreadsheet_project"
copy_to_remote "spreadsheet_project" "~/spreadsheet_project/spreadsheet_project"

# Copy processor app files
run_remote "mkdir -p ~/spreadsheet_project/spreadsheet_processor"
copy_to_remote "spreadsheet_processor" "~/spreadsheet_project/spreadsheet_processor"

# Copy static and media directories
copy_to_remote "static" "~/spreadsheet_project/static"
copy_to_remote "media" "~/spreadsheet_project/media"

# Set up Python environment and install dependencies
echo "Setting up Python environment..."
run_remote "cd ~/spreadsheet_project && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt gunicorn"

# Update Django settings
echo "Updating Django settings..."
run_remote "cat > ~/spreadsheet_project/spreadsheet_project/settings.py << 'EOF'
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-w8-zp@cp90d88pk)q63)4&ro-pj5-u9uar1*s+df-b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['$PUBLIC_IP']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'spreadsheet_processor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'spreadsheet_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'spreadsheet_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
EOF"

# Create systemd service file
echo "Creating systemd service..."
run_remote "sudo tee /etc/systemd/system/spreadsheet_project.service << 'EOF'
[Unit]
Description=Spreadsheet Project Django Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/spreadsheet_project
Environment=\"PATH=/home/ubuntu/spreadsheet_project/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
Environment=\"PYTHONPATH=/home/ubuntu/spreadsheet_project\"
ExecStart=/home/ubuntu/spreadsheet_project/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 spreadsheet_project.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"

# Run database migrations
echo "Running database migrations..."
run_remote "cd ~/spreadsheet_project && source venv/bin/activate && python manage.py migrate"

# Reload systemd and start the service
run_remote "sudo systemctl daemon-reload && sudo systemctl enable spreadsheet_project && sudo systemctl restart spreadsheet_project"

# Restart Nginx
run_remote "sudo systemctl restart nginx"

echo "Deployment completed successfully!"
echo "You can access the application at https://$PUBLIC_IP"
echo "Note: Since we're using a self-signed certificate, your browser will show a security warning. This is expected and you can proceed by accepting the security risk." 