# Upload

- Endpoints to upload the expenses in the CSV format
  - upload the csv
  - to view the history of file uploads 
  - list and filter the expenses

## Prerequisites

Before running the app, ensure you have the following installed:

- Python 3.8 or later
- pip (Python package manager)
- Virtual environment (optional but recommended)

## Installation

1. **Clone the repository**

   ```bash
    git clone git@github.com:venkatsgit/expense-guard.git
   cd upload
   ```

2. **Create a virtual environment (optional but recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configurations

set environment variables for below values:

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=expense_insights
```

## Running the Streamlit App

To start the Streamlit app, run:

```bash
python main.py
```


