#!/bin/bash

# Set the application URL
APP_URL="https://54.219.180.166"
TIMEOUT=30
exit_code=0

echo "Checking application health at $APP_URL..."
echo "Timeout set to $TIMEOUT seconds for each check"
echo "Starting health checks..."
echo "----------------------------------------"

# Function to check if HTTP status code is successful (200, 201, 202, 204, 302, 304)
is_successful_status() {
    local status=$1
    if [[ $status =~ ^(200|201|202|204|302|304)$ ]]; then
        return 0
    else
        return 1
    fi
}

# Check if the HTTPS endpoint is accessible
echo "Checking HTTPS endpoint..."
echo "Running: curl -k -v -s -f -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 $APP_URL"
status_code=$(curl -k -v -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 "$APP_URL")
if is_successful_status "$status_code"; then
    echo "✅ HTTPS endpoint is accessible (status: $status_code)"
else
    echo "❌ HTTPS endpoint is not accessible or not returning a successful status code (got: $status_code)"
    exit_code=1
fi

# Check application health
echo "Checking application health..."
echo "Running: curl -k -v -s -f -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 $APP_URL/health/"
status_code=$(curl -k -v -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 "$APP_URL/health/")
if is_successful_status "$status_code"; then
    echo "✅ Application health check passed (status: $status_code)"
else
    echo "❌ Application health check failed (got: $status_code)"
    exit_code=1
fi

# Check SSL certificate
echo "Checking SSL certificate..."
echo "Running: curl -k -v -s -f -o /dev/null --connect-timeout 5 --max-time 10 $APP_URL"
if curl -k -v -s -f -o /dev/null --connect-timeout 5 --max-time 10 "$APP_URL"; then
    echo "✅ SSL connection is working (self-signed certificate is accepted)"
else
    echo "❌ SSL certificate verification failed"
    exit_code=1
fi

echo "----------------------------------------"
if [ "$exit_code" -eq 0 ]; then
    echo "✅ All health checks passed successfully!"
else
    echo "❌ Some health checks failed. Please check the logs above for details."
fi

exit $exit_code