import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.utils import DATA_PROCESSED_DIR, setup_logger

logger = setup_logger("Recommender")

class SimpleMovieRecommender:
    def __init__(self):
        """
        Initializes the Simple Recommender.
        """
        self.movie_ids: List[int] = []
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        
        # Mappings
        self.movie_titles: Dict[int, str] = {}
        self.movie_genres: Dict[int, str] = {}
        
        # Precomputed Cosine Similarity Matrix
        #
        # --- WHAT IS COSINE SIMILARITY? ---
        # Cosine similarity is a simple metric that measures how similar two movies are based on their genres.
        # It looks at the overlap of genre tags: if two movies share the exact same genres (e.g. Action and Adventure),
        # they get a score of 1.0 (highly similar). If they share no genres (e.g. Comedy vs Horror), they get a score of 0.0.
        #
        # We precompute this matrix and save it (cache it) using Pickle. This avoids recalculating the similarities
        # during live API requests, making recommendations load instantly.
        self.similarity_matrix: np.ndarray = np.array([])
        
    def fit(self, df_movies: pd.DataFrame):
        """
        Learns movie properties and computes similarity scores based on genre tags.
        """
        logger.info("Starting simple recommender training...")
        
        # Store titles and genres mappings
        self.movie_titles = dict(zip(df_movies['movieId'], df_movies['cleaned_title']))
        self.movie_genres = dict(zip(df_movies['movieId'], df_movies['genres']))
        
        # Align movie indices
        self.movie_ids = sorted(df_movies['movieId'].unique().tolist())
        self.movie_id_to_idx = {m_id: idx for idx, m_id in enumerate(self.movie_ids)}
        self.idx_to_movie_id = {idx: m_id for idx, m_id in enumerate(self.movie_ids)}
        num_movies = len(self.movie_ids)
        
        # Compute TF-IDF on genres (converts genre tags to numerical vectors)
        logger.info("Computing genre-based similarity...")
        tfidf = TfidfVectorizer(analyzer=lambda x: [g.strip().lower() for g in x.split('|')])
        ordered_genres = [self.movie_genres[m_id] for m_id in self.movie_ids]
        tfidf_matrix = tfidf.fit_transform(ordered_genres)
        
        # Calculate Cosine Similarity (compares how close the genre vectors are)
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        logger.info(f"Similarity matrix computed. Shape: {self.similarity_matrix.shape}")

    def save_model(self, filepath: str):
        """
        Saves the trained model state to a binary file using Pickle.
        """
        logger.info(f"Saving precomputed model state to {filepath}...")
        artifacts = {
            'movie_ids': self.movie_ids,
            'movie_id_to_idx': self.movie_id_to_idx,
            'idx_to_movie_id': self.idx_to_movie_id,
            'movie_titles': self.movie_titles,
            'movie_genres': self.movie_genres,
            'similarity_matrix': self.similarity_matrix
        }
        with open(filepath, 'wb') as f:
            pickle.dump(artifacts, f)
        logger.info("Model saved successfully.")

    def load_model(self, filepath: str):
        """
        Loads the precomputed model state from a Pickle file on startup.
        """
        logger.info(f"Loading precomputed model state from {filepath}...")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found at {filepath}")
            
        with open(filepath, 'rb') as f:
            artifacts = pickle.load(f)
            
        self.movie_ids = artifacts['movie_ids']
        self.movie_id_to_idx = artifacts['movie_id_to_idx']
        self.idx_to_movie_id = artifacts['idx_to_movie_id']
        self.movie_titles = artifacts['movie_titles']
        self.movie_genres = artifacts['movie_genres']
        self.similarity_matrix = artifacts['similarity_matrix']
        logger.info("Model loaded successfully.")

    def get_recommendations(self, movie_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Finds the top N movies with the highest genre similarity to the input movie.
        """
        if movie_id not in self.movie_id_to_idx:
            logger.warning(f"Movie ID {movie_id} not found in model vocabulary.")
            return []
            
        # Get the row index for this movie in the similarity matrix
        idx = self.movie_id_to_idx[movie_id]
        
        # Get pairwise similarity scores for this movie index
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        
        # Sort by similarity score descending
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Exclude the input movie itself and compile the top_n results
        recommendations = []
        for c_idx, score in sim_scores:
            c_movie_id = self.idx_to_movie_id[c_idx]
            if c_movie_id == movie_id:
                continue
            recommendations.append({
                'movie_id': c_movie_id,
                'title': self.movie_titles[c_movie_id],
                'genres': self.movie_genres[c_movie_id],
                'score': round(float(score), 4)
            })
            if len(recommendations) >= top_n:
                break
                
        return recommendations
