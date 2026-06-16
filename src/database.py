import os
import mysql.connector
from typing import List, Tuple, Dict, Any
from src.utils import setup_logger

logger = setup_logger("Database")

# MySQL Connection Configurations (loaded from environment variables)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "syedayan23")
DB_NAME = os.getenv("DB_NAME", "movie_platform")

def get_connection(include_db: bool = True) -> mysql.connector.MySQLConnection:
    """
    Establishes a connection to the MySQL database server.
    """
    config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD
    }
    if include_db:
        config["database"] = DB_NAME
    return mysql.connector.connect(**config)

def create_index_safely(cursor, table: str, index_name: str, columns: str):
    """
    Checks if a MySQL index exists before attempting to create it.
    This prevents duplicate index errors on repeated runs.
    """
    query = """
        SELECT 1 
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s;
    """
    cursor.execute(query, (DB_NAME, table, index_name))
    if not cursor.fetchone():
        cursor.execute(f"CREATE INDEX {index_name} ON {table}({columns});")
        logger.info(f"Created index {index_name} on {table}({columns}).")

def create_tables():
    """
    Creates the MySQL database and the movies/ratings tables if they do not exist.
    """
    logger.info(f"Initializing MySQL database '{DB_NAME}' and tables...")
    
    # 1. Connect without DB name to create database if missing
    try:
        conn = get_connection(include_db=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to connect to MySQL database server or create schema: {e}")
        logger.error("Please verify that your MySQL server is running and connection details are correct.")
        raise e

    # 2. Connect with DB name to create tables and indexes
    conn = get_connection(include_db=True)
    cursor = conn.cursor()
    try:
        # Create movies table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            genres VARCHAR(255),
            release_year INT
        );
        """)

        # Create ratings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            rating FLOAT NOT NULL,
            timestamp INT NOT NULL,
            PRIMARY KEY (user_id, movie_id),
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
        );
        """)

        # Safely create indexes for search optimization
        create_index_safely(cursor, "movies", "idx_movies_title", "title")
        # Note: MySQL automatically indexes foreign key columns, so idx_ratings_movie_id is implicit,
        # but we can explicitly index user_id for user query performance.
        create_index_safely(cursor, "ratings", "idx_ratings_user_id", "user_id")

        conn.commit()
        logger.info("Database tables and indexes verified successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating database tables: {e}")
        raise e
    finally:
        conn.close()

def insert_movies(movies: List[Tuple[int, str, str, int]]):
    """
    Performs bulk insertion of movies using executemany.
    Uses MySQL REPLACE INTO syntax for duplicates.
    """
    logger.info(f"Inserting {len(movies)} movies into database...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany("""
        REPLACE INTO movies (movie_id, title, genres, release_year)
        VALUES (%s, %s, %s, %s);
        """, movies)
        conn.commit()
        logger.info("Movies bulk insert completed.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting movies: {e}")
        raise e
    finally:
        conn.close()

def insert_ratings(ratings: List[Tuple[int, int, float, int]]):
    """
    Performs bulk insertion of ratings.
    """
    logger.info(f"Inserting {len(ratings)} ratings into database...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany("""
        REPLACE INTO ratings (user_id, movie_id, rating, timestamp)
        VALUES (%s, %s, %s, %s);
        """, ratings)
        conn.commit()
        logger.info("Ratings bulk insert completed.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting ratings: {e}")
        raise e
    finally:
        conn.close()

# --- ANALYTICS SQL QUERIES ---

def get_top_rated_movies(limit: int = 10, min_ratings: int = 50) -> List[Dict[str, Any]]:
    """
    Returns the highest rated movies with a minimum number of ratings.
    """
    conn = get_connection()
    # mysql-connector returns dictionary representation of rows when dictionary=True
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT m.movie_id, m.title, m.genres, COUNT(r.rating) as rating_count, ROUND(AVG(r.rating), 2) as avg_rating
        FROM movies m
        JOIN ratings r ON m.movie_id = r.movie_id
        GROUP BY m.movie_id, m.title, m.genres
        HAVING rating_count >= %s
        ORDER BY avg_rating DESC, rating_count DESC
        LIMIT %s;
    """
    try:
        cursor.execute(query, (min_ratings, limit))
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error fetching top rated movies: {e}")
        return []
    finally:
        conn.close()

def get_most_active_users(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns users who have rated the most movies.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT user_id, COUNT(rating) as rating_count, ROUND(AVG(rating), 2) as avg_rating
        FROM ratings
        GROUP BY user_id
        ORDER BY rating_count DESC
        LIMIT %s;
    """
    try:
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error fetching active users: {e}")
        return []
    finally:
        conn.close()

def get_raw_movie_ratings() -> List[Tuple[str, float]]:
    """
    Helper query to fetch genre tags and raw ratings.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT m.genres, r.rating
        FROM movies m
        JOIN ratings r ON m.movie_id = r.movie_id;
    """
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching raw ratings: {e}")
        return []
    finally:
        conn.close()

def get_ratings_over_time() -> List[Tuple[int, float]]:
    """
    Returns rating timestamps and ratings.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT timestamp, rating FROM ratings;"
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching ratings over time: {e}")
        return []
    finally:
        conn.close()
