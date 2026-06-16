import os
import re
import shutil
import pandas as pd
from src.utils import (
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    download_and_extract_zip,
    setup_logger
)
from src.database import create_tables, insert_movies, insert_ratings

logger = setup_logger("ETL")

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

def extract_year_and_clean_title(title: str) -> tuple:
    """
    Parses the release year from the movie title and returns a cleaned title
    along with the integer year. If no year matches, returns the original title
    and None.
    """
    if not isinstance(title, str):
        return str(title), None
    
    # Matches (YYYY) at the end of the title
    pattern = r"\s*\((\d{4})\)\s*$"
    match = re.search(pattern, title)
    if match:
        year = int(match.group(1))
        cleaned_title = re.sub(pattern, "", title).strip()
        return cleaned_title, year
    return title.strip(), None

def run_etl():
    """
    Executes the complete ETL Pipeline.
    1. Downloads & Extracts the MovieLens dataset.
    2. Transforms/Cleans the datasets (missing values, parsing, duplicates).
    3. Loads the datasets into MySQL.
    """
    logger.info("Starting ETL Pipeline...")
    
    # --- 1. EXTRACT ---
    extracted_folder_path = os.path.join(DATA_RAW_DIR, "ml-latest-small")
    
    # Download if not already present
    if not os.path.exists(extracted_folder_path):
        logger.info("MovieLens dataset not found. Downloading...")
        download_and_extract_zip(MOVIELENS_URL, DATA_RAW_DIR)
    else:
        logger.info("Dataset already exists in raw data directory. Skipping download.")

    movies_csv_path = os.path.join(extracted_folder_path, "movies.csv")
    ratings_csv_path = os.path.join(extracted_folder_path, "ratings.csv")

    if not os.path.exists(movies_csv_path) or not os.path.exists(ratings_csv_path):
        raise FileNotFoundError("Extracted MovieLens files are missing movies.csv or ratings.csv.")

    # --- 2. TRANSFORM ---
    logger.info("Transforming datasets...")
    
    # Process Movies
    df_movies = pd.read_csv(movies_csv_path)
    logger.info(f"Loaded {len(df_movies)} raw movies.")
    
    # Drop rows with null columns
    df_movies = df_movies.dropna(subset=['movieId', 'title'])
    
    # Clean titles and extract release years
    cleaned_titles_and_years = [extract_year_and_clean_title(t) for t in df_movies['title']]
    df_movies['cleaned_title'] = [item[0] for item in cleaned_titles_and_years]
    df_movies['release_year'] = [item[1] for item in cleaned_titles_and_years]
    
    # Standardize genres
    df_movies['genres'] = df_movies['genres'].fillna("(no genres listed)")
    
    # Process Ratings
    df_ratings = pd.read_csv(ratings_csv_path)
    logger.info(f"Loaded {len(df_ratings)} raw ratings.")
    
    # Drop rows with null columns
    df_ratings = df_ratings.dropna(subset=['userId', 'movieId', 'rating', 'timestamp'])
    
    # Keep only valid ratings range (0.5 to 5.0)
    df_ratings = df_ratings[(df_ratings['rating'] >= 0.5) & (df_ratings['rating'] <= 5.0)]
    
    # Resolve duplicate reviews - keep latest review based on timestamp
    df_ratings = df_ratings.sort_values(by='timestamp', ascending=False)
    df_ratings = df_ratings.drop_duplicates(subset=['userId', 'movieId'], keep='first')
    
    # Convert IDs and timestamps to appropriate integer/float types
    df_movies['movieId'] = df_movies['movieId'].astype(int)
    df_ratings['userId'] = df_ratings['userId'].astype(int)
    df_ratings['movieId'] = df_ratings['movieId'].astype(int)
    df_ratings['timestamp'] = df_ratings['timestamp'].astype(int)
    df_ratings['rating'] = df_ratings['rating'].astype(float)
    
    # Save transformed data to processed data directory
    processed_movies_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_movies.csv")
    processed_ratings_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_ratings.csv")
    
    df_movies.to_csv(processed_movies_path, index=False)
    df_ratings.to_csv(processed_ratings_path, index=False)
    logger.info(f"Transformed data saved to {processed_movies_path} and {processed_ratings_path}.")

    # --- 3. LOAD ---
    logger.info("Loading cleaned data into the MySQL database...")
    create_tables()

    # Prepare movie tuples for database insertion (handle NaN years by converting to None)
    movie_tuples = []
    for _, row in df_movies.iterrows():
        year = int(row['release_year']) if pd.notnull(row['release_year']) else None
        movie_tuples.append((
            int(row['movieId']),
            str(row['cleaned_title']),
            str(row['genres']),
            year
        ))

    # Prepare rating tuples
    rating_tuples = [
        (int(row['userId']), int(row['movieId']), float(row['rating']), int(row['timestamp']))
        for _, row in df_ratings.iterrows()
    ]

    # Insert into SQLite database
    insert_movies(movie_tuples)
    insert_ratings(rating_tuples)

    logger.info("ETL Pipeline executed successfully. Data is ready for analysis and model training.")

if __name__ == "__main__":
    run_etl()
