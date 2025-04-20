FROM python:3.11

WORKDIR /app

COPY . /app

# Make sure start.sh is executable
RUN chmod +x start.sh

# Install system dependencies for ODBC
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg2 \
    ca-certificates \
    unixodbc-dev

# Add Microsoft's GPG key and repo securely
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list

# Install msodbcsql18 and mssql-tools18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql18 \
    mssql-tools18 && \
    rm -rf /var/lib/apt/lists/*

# Add tools to PATH
ENV PATH="$PATH:/opt/mssql-tools18/bin"

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8083

CMD ["./start.sh"]
