# Notibac

A Django web application.

## Requirements

- Python 3.x
- Node.js (for CSS build)
- PostgreSQL

## Setup

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Install Node dependencies

```bash
npm install
```

### Database

Configure your database connection via environment variables:

```bash
export DB_NAME=notibac
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432
```

Then run migrations:

```bash
python notibac/manage.py migrate
```

## Development

Start the development server:

```bash
./run.sh
```

This launches both the Tailwind CSS watcher and the Django server. Press `Ctrl+C` to stop both.

### CSS Build

The project uses Tailwind CSS v4 with daisyUI. The CSS source is at `notibac/website/styles/styles.css` and compiles to `notibac/website/static/dist/styles.css`.

**Note:** The compiled CSS in `website/static/dist/` is not tracked in git.

To run the CSS watcher independently:

```bash
npm run watch:css
```
