#!/bin/bash

# Setup virtual environment if it doesn't exist
# and install requirements.txt if available

# Define venv directory name
VENV_DIR="venv"

export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix mysql-client)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix mysql-client)/include"
export PKG_CONFIG_PATH="$(brew --prefix openssl)/lib/pkgconfig:$(brew --prefix mysql-client)/lib/pkgconfig"

# Check if we're on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PYTHON_CMD="python"
    VENV_PYTHON_PATH="./$VENV_DIR/Scripts/python.exe"
    VENV_PIP_PATH="./$VENV_DIR/Scripts/pip"
    VENV_ACTIVATE="./$VENV_DIR/Scripts/activate"
else
    PYTHON_CMD="python3"
    VENV_PYTHON_PATH="./$VENV_DIR/bin/python"
    VENV_PIP_PATH="./$VENV_DIR/bin/pip"
    VENV_ACTIVATE="./$VENV_DIR/bin/activate"
fi

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR

    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_ACTIVATE

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    $VENV_PIP_PATH install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements."
        exit 1
    fi
    echo "Requirements installed successfully."
else
    echo "No requirements.txt file found."
fi

# Output the path to the Python executable
echo ""
echo "Python executable path for IDE configuration:"
echo "$(pwd)/$VENV_PYTHON_PATH"

# If on Windows, also provide the path with backslashes
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    WIN_PATH=$(echo "$(pwd)/$VENV_PYTHON_PATH" | sed 's/\//\\/g')
    echo "Windows path format: $WIN_PATH"
fi

echo ""
echo "Virtual environment is ready to use!"