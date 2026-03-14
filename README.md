# OTT Streaming Analytics — Flask Version

## Project Structure
```
flask_ott/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── data/
│   ├── movies.csv
│   ├── netflix_cleaned.csv
│   ├── prime_cleaned.csv
│   ├── disney_cleaned.csv
│   └── multi_cleaned.csv
├── static/
│   └── css/
│       └── styles.css
└── templates/
    ├── base.html
    ├── home.html
    ├── platform_detail.html
    ├── comparison.html
    ├── recommendation.html
    ├── insights.html
    └── search_results.html
```

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000/
```

## Pages / Routes
| Route | Description |
|-------|-------------|
| `/` | Home Dashboard |
| `/platform/<name>/` | Platform Detail (netflix, prime, hotstar) |
| `/compare/` | Head-to-Head Comparison |
| `/recommendation/` | Genre-based Recommendation |
| `/insights/` | Data Insights |
| `/search/?q=<query>` | Search Movies |

## Key Changes from Django → Flask
- `urls.py` removed → routes defined with `@app.route()` in `app.py`
- `{% url 'name' %}` → `{{ url_for('function_name') }}`
- `{% load static %}` + `{% static 'file' %}` → `{{ url_for('static', filename='file') }}`
- `{% csrf_token %}` removed (Flask handles POST without CSRF by default)
- `{{ var|safe }}` → `{{ var | tojson }}` for JavaScript data
- `request.POST` → `request.form`
- `request.GET` → `request.args`
- `settings.BASE_DIR` → `os.path.dirname(os.path.abspath(__file__))`
- Django's `render(request, template, context)` → Flask's `render_template(template, **context)`
- `{% for x in dict.items %}` → `{% for x in dict.items() %}`
- `{{ forloop.first }}` → `{{ loop.first }}`
- `{{ forloop.counter }}` → `{{ loop.index }}`
