# ============================================================
#  app.py  -  The MAIN file of this Flask web application
#
#  Flask is a lightweight Python web framework.
#  This single file controls EVERYTHING the website does:
#    - Which URL shows which page  (called "routing")
#    - What data to load and calculate for each page
#    - Which HTML template to send back to the browser
#
#  HOW A FLASK APP WORKS (simple explanation):
#    1. User types a URL in the browser  e.g.  /search/
#    2. Flask looks for a matching @app.route() below
#    3. The matching Python function runs
#    4. The function collects data, then calls render_template()
#    5. render_template() fills in the HTML file and sends it back
#    6. The browser displays the finished page
# ============================================================


# ---- IMPORTS -----------------------------------------------
# "import" means we are borrowing tools that other people wrote
# so we don't have to write everything from scratch.

import os           # OS tools - builds file paths that work on
                    # Windows, Mac, AND Linux automatically.

import pandas as pd # pandas = Excel inside Python.
                    # Reads CSV files and lets us filter/group data.
                    # "as pd" is just a short nickname.

import numpy as np  # numpy adds extra math tools used by pandas.
                    # "as np" is just a short nickname.

import requests     # lets Python talk to external websites (APIs).
                    # We use it to fetch movie posters from TMDB.

# Flask imports - the specific tools we need from Flask:
#   Flask           = creates the web application itself
#   render_template = loads an HTML file and fills in our data
#   request         = lets us read form data or URL parameters
#   jsonify         = converts Python data to JSON (kept for future use)
from flask import Flask, render_template, request, jsonify


# ---- CREATE THE APP ----------------------------------------
# This one line creates the entire Flask application.
# __name__ tells Flask where to look for templates/ and static/ folders.
app = Flask(__name__)


# ---- FIND THE PROJECT FOLDER --------------------------------
# os.path.abspath(__file__)  gives the full path to THIS file (app.py)
# os.path.dirname(...)       removes the filename, leaving just the folder
# Result: BASE_DIR = the folder where app.py lives
# We need this so we can correctly build paths to our CSV data files.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---- HELPER FUNCTION: Build a path to a data file -----------
def get_data_path(filename):
    """
    Takes a short filename like 'movies.csv' and returns the
    full path to it inside the data/ folder.

    Example:
        get_data_path('movies.csv')
        -> '/home/user/flask_ott/data/movies.csv'

    os.path.join() safely combines folder parts using the correct
    slash character (/ on Mac/Linux, backslash on Windows).
    """
    return os.path.join(BASE_DIR, 'data', filename)


# ---- HELPER FUNCTION: Load the main dataset -----------------
def load_data():
    """
    Reads movies.csv and returns it as a pandas DataFrame.

    A DataFrame is like a table with rows and columns - similar
    to a spreadsheet. It lets us filter rows, group data, and
    calculate averages very easily.

    We call this at the start of every page function so every
    page has access to the full movies dataset.
    """
    movies_df = pd.read_csv(get_data_path('movies.csv'))
    return movies_df


# ============================================================
#  PAGE 1 - HOME DASHBOARD   (URL: /)
# ============================================================
# @app.route('/') is a "decorator".
# It tells Flask: "when someone visits the homepage (/),
# run the function directly below this line."
@app.route('/')
def home_dashboard():
    movies_df = load_data()   # Load the full CSV table

    # The 3 platforms we support in this app
    platforms = ['Netflix', 'Prime Video', 'Disney+ Hotstar']

    # Real 2026 Indian monthly subscription prices in Rupees
    current_prices = {
        'Netflix': 149,
        'Prime Video': 299,
        'Disney+ Hotstar': 299
    }

    # CHART 1 - Total Library Size
    # value_counts() counts how many rows have each platform name.
    # .to_dict() converts the result to a Python dictionary.
    # Example result: {'Netflix': 3000, 'Prime Video': 2500, ...}
    library_sizes = movies_df['platform'].value_counts().to_dict()

    # CHART 2 - Average IMDB Rating per Platform
    # groupby('platform') groups rows together by platform name.
    # ['imdb_rating'].mean() calculates the average rating per group.
    # .round(2) rounds to 2 decimal places.
    avg_quality = movies_df.groupby('platform')['imdb_rating'].mean().round(2).to_dict()

    # CHART 3 - Content Freshness
    # Filter to keep only movies released in 2020 or later
    fresh_movies = movies_df[movies_df['release_year'] >= 2020]
    freshness_counts = fresh_movies['platform'].value_counts().to_dict()

    # Build the summary cards - one dictionary per platform
    # Each dict holds all the numbers we show on that platform's card
    platform_stats = []
    for platform in platforms:
        total_movies = int(library_sizes.get(platform, 0))  # int() converts numpy int to plain Python int
        avg_rating   = float(avg_quality.get(platform, 0))  # float() converts numpy float to plain Python float
        price        = current_prices[platform]

        # Value Score = how many movies you get per Rupee spent
        # We guard against dividing by zero with "if price > 0"
        value_score = round(total_movies / price, 1) if price > 0 else 0

        platform_stats.append({
            'name':         platform,
            'total_movies': total_movies,
            'avg_rating':   avg_rating,
            'price':        price,
            'value_score':  value_score,
            'fresh_count':  int(freshness_counts.get(platform, 0))
        })

    # CHART 4 - Subscriber Growth (real-world data in millions)
    subscriber_years = ['2020', '2021', '2022', '2023', '2024', '2025']
    subscriber_data = {
        'Netflix':         [203.7, 221.8, 231.3, 260.3, 301.6, 315.0],
        'Prime Video':     [200.0, 220.0, 230.0, 240.0, 240.0, 252.0],
        'Disney+ Hotstar': [87.0,  129.8, 161.8, 149.6, 153.8, 132.0]
    }

    # render_template() opens templates/home.html and replaces
    # all {{ variable }} placeholders with the real values below.
    # Every keyword argument (platforms=...) becomes a variable in home.html.
    return render_template('home.html',
        platforms        = platforms,
        library_sizes    = [library_sizes.get(p, 0) for p in platforms],
        avg_quality      = [avg_quality.get(p, 0) for p in platforms],
        freshness        = [freshness_counts.get(p, 0) for p in platforms],
        value_scores     = [round(library_sizes.get(p, 0) / current_prices[p], 1) for p in platforms],
        platform_stats   = platform_stats,
        subscriber_years = subscriber_years,
        subscriber_data  = {p: subscriber_data[p] for p in platforms},
    )


# ============================================================
#  PAGE 2 - PLATFORM DETAIL   (URL: /platform/<platform_name>/)
# ============================================================
# <platform_name> is a URL variable - it captures whatever the
# user puts in the URL after /platform/
# e.g. visiting /platform/netflix/ sets platform_name = 'netflix'
# Flask automatically passes it as a parameter to the function below.
@app.route('/platform/<platform_name>/')
def platform_detail(platform_name):
    movies_df = load_data()

    # The URL uses short lowercase names like 'netflix',
    # but our CSV uses full names like 'Netflix'.
    # This dictionary translates between the two.
    platform_map = {
        'netflix':         'Netflix',
        'prime':           'Prime Video',
        'prime video':     'Prime Video',
        'hotstar':         'Disney+ Hotstar',
        'disney+ hotstar': 'Disney+ Hotstar'
    }

    # .lower() converts the URL input to lowercase before looking it up
    # .get(key, default) returns 'Netflix' if the key is not found
    actual_platform = platform_map.get(platform_name.lower(), 'Netflix')

    # Filter the DataFrame to only rows for this specific platform.
    # movies_df['platform'] == actual_platform  creates a True/False column.
    # Wrapping it in [] keeps only the rows where it is True.
    df = movies_df[movies_df['platform'] == actual_platform]

    # Genre Pie Chart data
    genre_counts = df['genre'].value_counts()
    genre_labels = genre_counts.index.tolist()   # ['Action', 'Drama', ...]
    genre_data   = genre_counts.tolist()          # [500, 300, ...]

    # Average IMDB rating grouped by genre (for the bar chart)
    genre_ratings = df.groupby('genre')['imdb_rating'].mean().round(1)

    # Top 10 highest rated movies on this platform
    # ascending=False means highest first, .head(10) takes only 10 rows
    top_movies      = df.sort_values(by='imdb_rating', ascending=False).head(10)
    top_movies_list = top_movies[['movie_name', 'genre', 'imdb_rating', 'release_year']].to_dict('records')

    # TMDB API - fetch live movie posters and plot summaries
    # TMDB (The Movie Database) is a free public movie API.
    # The Bearer Token below is like an API "password" that
    # identifies our application to the TMDB server.
    TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyZGM4N2FlNzk0ODRhNzllZWQwZmJkMjEzZWE2NmU4YiIsIm5iZiI6MTc3MzIyMTAwOS4wNiwic3ViIjoiNjliMTM0OTE3NDc5YmM4M2IxYWMyMTJjIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.rEzQuxJBVkGPeH6a2EazDmRxJnwYMgSgOUmMJ-ifo1E"

    # HTTP headers are extra info sent with every API request.
    # "Authorization" tells TMDB who we are.
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
    }

    # Loop through each of the top 10 movies and fetch its poster + plot
    for movie in top_movies_list:

        # Replace spaces with + to make a valid web search query
        # Example: "The Dark Knight" becomes "The+Dark+Knight"
        movie_query = movie['movie_name'].replace(' ', '+')

        # Build the TMDB search URL for this movie
        url = f"https://api.themoviedb.org/3/search/movie?query={movie_query}&include_adult=false&language=en-US&page=1"

        # Set fallback values in case the API call fails or the movie is not found
        movie['poster'] = 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60'
        movie['plot']   = f"An exciting critically-acclaimed {movie['genre']} movie released in {movie['release_year']}."

        # try/except - if any error happens (no internet, movie not found,
        # timeout, etc.) we silently skip it with "pass" so the page
        # still loads even if the API is down.
        try:
            # Send the web request to TMDB. timeout=1.5 means give up
            # after 1.5 seconds so the page doesn't hang forever.
            response = requests.get(url, headers=headers, timeout=1.5)

            # HTTP status 200 means "Success"
            if response.status_code == 200:
                data    = response.json()          # Parse the JSON text into a Python dictionary
                results = data.get('results', [])  # Get the list of matching movies (default empty list)

                if results:
                    first_match = results[0]  # Take the first (most relevant) result

                    # Get the poster image path e.g. '/abc123.jpg'
                    poster_path = first_match.get('poster_path')
                    if poster_path:
                        # Combine TMDB's image server address with the poster path
                        movie['poster'] = f"https://image.tmdb.org/t/p/w500{poster_path}"

                    # Get the plot summary text
                    overview = first_match.get('overview')
                    if overview:
                        movie['plot'] = overview

        except Exception:
            pass  # Something went wrong - keep the fallback values and move on

    # Movie Release Trend - count movies per year, sorted oldest to newest
    release_trend = df['release_year'].value_counts().sort_index()

    return render_template('platform_detail.html',
        platform_name  = actual_platform,
        platform_slug  = platform_name.lower(),
        genre_labels   = genre_labels,
        genre_data     = genre_data,
        rating_labels  = genre_ratings.index.tolist(),
        rating_data    = genre_ratings.tolist(),
        top_movies     = top_movies_list,
        trend_years    = release_trend.index.tolist(),
        trend_counts   = release_trend.tolist(),
    )


# ============================================================
#  PAGE 3 - RECOMMENDATION SYSTEM   (URL: /recommendation/)
# ============================================================
# methods=['GET', 'POST'] means this URL handles two situations:
#   GET  = user visits the page normally (show empty form)
#   POST = user clicked the submit button (calculate recommendation)
@app.route('/recommendation/', methods=['GET', 'POST'])
def recommendation_system():
    # Start with empty defaults - used when the page first loads (GET)
    recommended_platform = None  # None means "no recommendation yet"
    recommended_score    = 0
    reasons              = []    # empty list
    alternatives         = []

    movies_df  = load_data()

    # Get every unique genre from the dataset, sorted A to Z
    # .unique() removes duplicate genre names
    # sorted() arranges them alphabetically
    all_genres = sorted(movies_df['genre'].unique().tolist())

    # Only calculate a recommendation if the user submitted the form
    if request.method == 'POST':

        # request.form holds all the data the user submitted
        # .getlist() returns a list because multiple genres can be checked
        selected_genres = request.form.getlist('genres')

        # .get('min_rating', 0) reads the field, defaults to 0 if missing
        # float() converts the text "7.0" into the actual number 7.0
        min_rating = float(request.form.get('min_rating', 0))

        platforms = ['Netflix', 'Prime Video', 'Disney+ Hotstar']
        scores    = {}    # final score for each platform
        reasoning = {}    # explanation text for each platform

        for platform in platforms:
            df = movies_df[movies_df['platform'] == platform]

            # Step 1: Remove movies below the user's minimum rating threshold
            df_rated = df[df['imdb_rating'] >= min_rating]

            # Step 2: Keep only movies matching the user's selected genres
            # If no genres were selected, keep all rated movies
            if selected_genres:
                genre_movies = df_rated[df_rated['genre'].isin(selected_genres)]
            else:
                genre_movies = df_rated

            genre_count = len(genre_movies)   # total matching movies

            # Average rating of matching movies (0 if no matches to avoid crash)
            avg_rating = genre_movies['imdb_rating'].mean() if len(genre_movies) > 0 else 0

            # Find the 3 most recent years in the whole dataset
            # sorted()[-3:] = last 3 items after sorting = 3 most recent
            recent_years  = sorted(movies_df['release_year'].unique())[-3:]
            recent_movies = len(genre_movies[genre_movies['release_year'].isin(recent_years)])

            # THE SCORING FORMULA:
            #   (volume / 100)  rewards platforms with more matching movies
            #   avg_rating      rewards platforms with higher quality matches
            #   (recency / 50)  rewards platforms with more recent matches
            score = (genre_count / 100) + avg_rating + (recent_movies / 50)
            scores[platform] = round(score, 2)

            # Human-readable reasons to show the user why this score was given
            reasoning[platform] = [
                f"Matches {genre_count} movies in your selected genres",
                f"Average IMDB rating of matching movies is {round(avg_rating, 1)}",
                f"Added {recent_movies} matching movies in recent years"
            ]

        # Sort platforms by score, highest first
        # lambda x: x[1] means "sort by the second item in each tuple (the score)"
        sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # The winner is the first platform in the sorted list
        if sorted_platforms and sorted_platforms[0][1] > 0:
            recommended_platform = sorted_platforms[0][0]
            recommended_score    = sorted_platforms[0][1]
            reasons              = reasoning[recommended_platform]

            # The 2nd and 3rd platforms are shown as "alternatives"
            # [1:3] means take items at index 1 and 2 (skip index 0 = winner)
            for plat, score in sorted_platforms[1:3]:
                if score > 0:
                    alternatives.append({'name': plat, 'score': score, 'reasons': reasoning[plat]})

    # method=request.method lets the template distinguish between
    # "page not submitted yet" vs "submitted but no matches found"
    return render_template('recommendation.html',
        all_genres           = all_genres,
        recommended_platform = recommended_platform,
        recommended_score    = recommended_score,
        reasons              = reasons,
        alternatives         = alternatives,
        method               = request.method,
    )


# ============================================================
#  PAGE 4 - DATA INSIGHTS   (URL: /insights/)
# ============================================================
@app.route('/insights/')
def data_insights():
    movies_df = load_data()

    # Which platform has the highest average IMDB rating?
    # sort_values(ascending=False) puts the best platform first
    avg_imdb     = movies_df.groupby('platform')['imdb_rating'].mean().round(1).sort_values(ascending=False)
    highest_imdb = avg_imdb.to_dict()

    # Top 5 most popular genres across ALL platforms combined
    genre_counts = movies_df['genre'].value_counts()
    total_movies = len(movies_df)   # total number of rows = total movies

    # Calculate each genre's percentage share of the entire library
    # e.g. if Action has 500 movies out of 2000 total: 500/2000 * 100 = 25%
    popular_genres = {
        genre: f"{round((count / total_movies) * 100)}%"
        for genre, count in genre_counts.head(5).items()
    }

    # Total movie count per platform
    content_counts = movies_df['platform'].value_counts().to_dict()

    platforms = ['Netflix', 'Prime Video', 'Disney+ Hotstar']

    # Rating Distribution Chart
    # Instead of just showing averages, we sort movies into rating "buckets"
    # so we can see how spread out the quality is on each platform.
    bins   = [0, 5, 6, 7, 8, 9, 10]          # boundary values for each bucket
    labels = ['< 5', '5 - 6', '6 - 7', '7 - 8', '8 - 9', '> 9']  # bucket labels

    distribution = {p: [] for p in platforms}  # start with empty lists

    for platform in platforms:
        plat_df = movies_df[movies_df['platform'] == platform]

        # pd.cut() assigns each movie to a rating bucket based on its IMDB score
        # .value_counts() counts how many movies are in each bucket
        # .reindex(labels, fill_value=0) fills in 0 for any empty buckets
        #   so the chart always shows all 6 buckets even if some have no movies
        counts = (
            pd.cut(plat_df['imdb_rating'], bins=bins, labels=labels, right=False)
            .value_counts()
            .reindex(labels, fill_value=0)
        )
        distribution[platform] = counts.tolist()

    return render_template('insights.html',
        highest_imdb        = highest_imdb,
        popular_genres      = popular_genres,
        content_counts      = content_counts,
        rating_labels       = labels,
        rating_distribution = distribution,
    )


# ============================================================
#  PAGE 5 - GLOBAL SEARCH   (URL: /search/?q=your+query)
# ============================================================
@app.route('/search/')
def search_results():
    # The search term comes from the URL: /search/?q=batman
    # request.args holds all URL query parameters (?key=value pairs)
    # .get('q', '') returns '' (empty string) if no search term was given
    # .strip() removes extra spaces the user may have accidentally typed
    query     = request.args.get('q', '').strip()
    movies_df = load_data()

    results = []  # Start with empty results

    if query:  # Only search if user actually typed something
        # .str.contains() scans the movie_name column for the search term
        # case=False makes it case-insensitive ("batman" finds "Batman")
        # na=False handles blank cells without crashing
        matches = movies_df[movies_df['movie_name'].str.contains(query, case=False, na=False)]

        # Sort so highest-rated matches appear first
        matches = matches.sort_values(by='imdb_rating', ascending=False)

        # Convert matching rows to a list of dicts for the template
        # We only keep the 5 most relevant columns
        results = matches[['movie_name', 'platform', 'genre', 'imdb_rating', 'release_year']].to_dict('records')

    return render_template('search_results.html',
        query       = query,
        results     = results,
        total_found = len(results),  # len() counts items in the list
    )


# ============================================================
#  PAGE 6 - COMPARE PLATFORMS   (URL: /compare/)
# ============================================================
@app.route('/compare/')
def compare_platforms():
    movies_df     = load_data()
    all_platforms = ['Netflix', 'Prime Video', 'Disney+ Hotstar']

    # Read the two platforms the user chose from the dropdown menus.
    # They arrive as URL parameters: /compare/?p1=Netflix&p2=Prime+Video
    # Default to Netflix vs Prime Video if nothing was chosen yet.
    p1 = request.args.get('p1', 'Netflix')
    p2 = request.args.get('p2', 'Prime Video')

    # Safety check - if someone types an invalid platform name in the URL,
    # reset to the defaults instead of crashing
    if p1 not in all_platforms: p1 = 'Netflix'
    if p2 not in all_platforms: p2 = 'Prime Video'

    current_prices = {
        'Netflix': 149,
        'Prime Video': 299,
        'Disney+ Hotstar': 299
    }

    # Calculate comparison stats for each of the two selected platforms
    stats = {}

    for p in [p1, p2]:
        df = movies_df[movies_df['platform'] == p]

        library_size = len(df)  # total movies on this platform

        # Average IMDB (skip if no movies to avoid divide-by-zero)
        avg_quality = round(df['imdb_rating'].mean(), 2) if library_size > 0 else 0

        # Count movies from 2020 onwards (measures how current the library is)
        freshness = len(df[df['release_year'] >= 2020])

        price       = current_prices[p]
        value_score = round(library_size / price, 1) if price > 0 else 0

        # Find the 3 genres with the most movies on this platform
        # .head(3) keeps only the top 3
        # .index.tolist() gets just the genre names as a list
        top_genres = df['genre'].value_counts().head(3).index.tolist()

        stats[p] = {
            'library_size': library_size,
            'avg_quality':  avg_quality,
            'freshness':    freshness,
            'price':        price,
            'value_score':  value_score,
            'top_genres':   ", ".join(top_genres)  # Join list: ["Action","Drama"] -> "Action, Drama"
        }

    return render_template('comparison.html',
        all_platforms = all_platforms,  # used to populate the dropdown menus
        p1            = p1,
        p2            = p2,
        stats_p1      = stats[p1],
        stats_p2      = stats[p2],
    )


# ============================================================
#  START THE SERVER
# ============================================================
# This block only runs when you execute this file directly:
#     python app.py
#
# "if __name__ == '__main__'" prevents this from running if
# another file imports app.py (important for testing/deployment).
#
# debug=True gives you:
#   - Detailed error messages in the browser when something breaks
#   - Auto-restart whenever you save changes to the code
#   (Always set debug=False before deploying to the internet!)
if __name__ == '__main__':
    app.run(debug=True)
