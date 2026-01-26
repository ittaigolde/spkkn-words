# The Word Registry - Backend

FastAPI backend for The Word Registry platform.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Initialize database:
```bash
python init_db.py
```

5. Import words:
```bash
python import_words.py
```

### Running the Server

```bash
uvicorn app.main:app --reload --port 8000
```

API will be available at http://localhost:8000

Interactive API docs: http://localhost:8000/docs

## Database Schema

### Words Table
- `id`: Primary key
- `text`: Word text (unique, indexed)
- `price`: Current price (starts at $1.00)
- `owner_name`: Current owner's name
- `owner_message`: Owner's custom message (max 140 chars)
- `lockout_ends_at`: Timestamp when lockout expires
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Transactions Table
- `id`: Primary key
- `word_id`: Foreign key to words table
- `buyer_name`: Buyer's name
- `price_paid`: Amount paid
- `timestamp`: Transaction timestamp
