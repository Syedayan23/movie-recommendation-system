import os
import sys
import pickle
from flask import Flask, request, jsonify

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils import DATA_PROCESSED_DIR, setup_logger
from src.recommender import SimpleMovieRecommender
import src.database as db

logger = setup_logger("API")
app = Flask(__name__)

# Model pickle path
MODEL_PATH = os.path.join(DATA_PROCESSED_DIR, "genre_similarity_model.pkl")
recommender = None

def load_cached_model():
    global recommender
    recommender = SimpleMovieRecommender()
    try:
        if os.path.exists(MODEL_PATH):
            recommender.load_model(MODEL_PATH)
            logger.info("Genre recommendation model successfully loaded on startup.")
        else:
            logger.warning(
                f"Model file not found at {MODEL_PATH}. "
                "Recommendation endpoint will return 503 Service Unavailable. "
                "Please run 'python main.py --train' first."
            )
            recommender = None
    except Exception as e:
        logger.error(f"Error loading recommendation model: {e}")
        recommender = None

# Initialize model
load_cached_model()

# Helper standard response functions
def send_success(data, message="Operation successful"):
    return jsonify({
        "status": "success",
        "data": data,
        "message": message
    }), 200

def send_error(message, status_code=400):
    return jsonify({
        "status": "error",
        "message": message,
        "data": None
    }), status_code

@app.route('/recommend/movie/<movie_id>', methods=['GET'])
def recommend_movie(movie_id):
    """
    Returns movies that are highly similar in genres to the input movie.
    URL: /recommend/movie/<movie_id>?count=10
    """
    logger.info(f"API Request: /recommend/movie/{movie_id}")
    
    if recommender is None or not recommender.movie_ids:
        return send_error("Recommender model is not trained or loaded. Please run model training.", 503)

    # Validate integer ID
    try:
        movie_id_int = int(movie_id)
    except ValueError:
        return send_error("Invalid movie ID format. Movie ID must be an integer.", 400)

    if movie_id_int not in recommender.movie_id_to_idx:
        return send_error(f"Movie ID {movie_id_int} not found in dataset.", 404)

    # Validate count parameter
    count = request.args.get('count', 10)
    try:
        count_int = int(count)
        if count_int <= 0:
            raise ValueError()
    except ValueError:
        return send_error("Count parameter must be a positive integer.", 400)

    # Generate recommendations
    try:
        recommendations = recommender.get_recommendations(movie_id_int, top_n=count_int)
        return send_success(
            data=recommendations,
            message=f"Successfully fetched top {len(recommendations)} recommendations similar to movie {movie_id_int}"
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return send_error("Internal server error occurred.", 500)

@app.route('/analytics/top-movies', methods=['GET'])
def analytics_top_movies():
    """
    Queries SQL database for top-rated movies based on rating average and count.
    URL: /analytics/top-movies?limit=10&min_ratings=50
    """
    logger.info("API Request: /analytics/top-movies")
    
    limit = request.args.get('limit', 10)
    min_ratings = request.args.get('min_ratings', 50)
    
    try:
        limit_int = int(limit)
        min_ratings_int = int(min_ratings)
        if limit_int <= 0 or min_ratings_int < 0:
            raise ValueError()
    except ValueError:
        return send_error("Parameters 'limit' and 'min_ratings' must be positive integers.", 400)
        
    try:
        movies = db.get_top_rated_movies(limit=limit_int, min_ratings=min_ratings_int)
        return send_success(data=movies, message="Top-rated movies queried successfully.")
    except Exception as e:
        logger.error(f"Error querying top-rated movies: {e}")
        return send_error("Internal database error occurred.", 500)

@app.route('/analytics/genre-insights', methods=['GET'])
def analytics_genre_insights():
    """
    Computes average rating and rating volume count for all genres.
    URL: /analytics/genre-insights
    """
    logger.info("API Request: /analytics/genre-insights")
    
    try:
        raw_ratings = db.get_raw_movie_ratings()
        if not raw_ratings:
            return send_success(data=[], message="No ratings data available to analyze.")
            
        import pandas as pd
        df = pd.DataFrame(raw_ratings, columns=['genres', 'rating'])
        df_exploded = df.assign(genres=df['genres'].str.split('|')).explode('genres')
        
        genre_stats = df_exploded.groupby('genres').agg(
            rating_count=('rating', 'count'),
            avg_rating=('rating', 'mean')
        ).reset_index()
        
        genre_stats = genre_stats[genre_stats['genres'] != '(no genres listed)']
        genre_stats['avg_rating'] = genre_stats['avg_rating'].round(2)
        genre_stats = genre_stats.sort_values(by='rating_count', ascending=False)
        
        data = genre_stats.to_dict(orient='records')
        return send_success(data=data, message="Genre analytics loaded successfully.")
    except Exception as e:
        logger.error(f"Error computing genre insights: {e}")
        return send_error("Internal error occurred during computation.", 500)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check indicating database and recommender loading status.
    """
    db_ok = False
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchall()
        cursor.close()
        conn.close()
        db_ok = True
    except Exception:
        pass
        
    return jsonify({
        "status": "healthy" if db_ok else "unhealthy",
        "database_connected": db_ok,
        "recommender_loaded": recommender is not None
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
