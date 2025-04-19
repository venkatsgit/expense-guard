FROM python:3.11

WORKDIR /app

COPY . /app

# Make sure start.sh is executable
RUN chmod +x start.sh

# Install system dependencies for odbc driver
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg2 \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's package repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install msodbcsql18 and mssql-tools18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql18 \
    mssql-tools18 \
    && rm -rf /var/lib/apt/lists/*

# Add SQL Server tools to the PATH environment variable
ENV PATH="$PATH:/opt/mssql-tools18/bin"


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8083

CMD ["./start.sh"]