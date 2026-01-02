# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Start development server (Django + CSS watcher):**
```bash
./run.sh
```

**Run Django server only:**
```bash
python notibac/manage.py runserver
```

**Run CSS watcher only:**
```bash
npm run watch:css
```

**Run migrations:**
```bash
python notibac/manage.py migrate
```

**Make migrations:**
```bash
python notibac/manage.py makemigrations
```

## Architecture

This is a Django 6.0 project with a PostgreSQL database and Tailwind CSS v4 + daisyUI frontend.

### Project Structure

- `notibac/` - Django project root containing `manage.py`
  - `notibac/` - Django settings module (settings.py, urls.py, wsgi.py, asgi.py)
  - `website/` - Main Django app with views, models, and templates

### Frontend Build

- CSS source: `notibac/website/styles/styles.css`
- CSS output: `notibac/website/static/dist/styles.css` (gitignored)
- Uses Tailwind CSS v4 with daisyUI plugin
- Custom "jungle-green" theme defined in styles.css
- Custom font "Renogare" loaded from `/static/fonts/`

### Templates

- Base template: `notibac/website/templates/base.html`
- Page templates extend base.html and use `{% block content %}`
- Partials in `notibac/website/templates/partials/`

### Database

PostgreSQL configured via environment variables:
- `DB_NAME` (default: notibac)
- `DB_USER` (default: postgres)
- `DB_PASSWORD` (default: postgres)
- `DB_HOST` (default: localhost)
- `DB_PORT` (default: 5432)
