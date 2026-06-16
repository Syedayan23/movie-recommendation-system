import os
import argparse
import sys
import pandas as pd

from src.utils import DATA_PROCESSED_DIR, setup_logger
from src.etl import run_etl
from src.analysis import run_analysis
from src.recommender import SimpleMovieRecommender

logger = setup_logger("Main")

def run_training():
    """
    Loads transformed movies dataset, trains the simple genre similarity recommender,
    and pickles the resulting similarity matrix.
    """
    logger.info("Initializing model training step...")
    
    processed_movies_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_movies.csv")
    
    if not os.path.exists(processed_movies_path):
        logger.error("Cleaned data CSV file not found in data/processed/. Please run ETL first (--etl).")
        sys.exit(1)
        
    df_movies = pd.read_csv(processed_movies_path)
    
    recommender = SimpleMovieRecommender()
    recommender.fit(df_movies)
    
    model_pickle_path = os.path.join(DATA_PROCESSED_DIR, "genre_similarity_model.pkl")
    recommender.save_model(model_pickle_path)
    logger.info(f"Model successfully trained and serialized at {model_pickle_path}")

def start_server():
    """
    Starts the Flask API server.
    """
    logger.info("Starting Flask API Server...")
    from api.app import app
    app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    parser = argparse.ArgumentParser(
        description="Movie Recommendation & Analysis System CLI Orchestration tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --etl
  python main.py --train
  python main.py --analyze
  python main.py --serve
  python main.py --etl --train --serve
        """
    )
    
    parser.add_argument('--etl', action='store_true', help='Download, clean, and load MovieLens data to MySQL.')
    parser.add_argument('--analyze', action='store_true', help='Execute Exploratory Data Analysis and save visualization plots.')
    parser.add_argument('--train', action='store_true', help='Precompute and cache genre similarity matrix.')
    parser.add_argument('--serve', action='store_true', help='Start the Flask REST API server.')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    if args.etl:
        logger.info("==== RUNNING ETL PIPELINE ====")
        run_etl()
        
    if args.analyze:
        logger.info("==== RUNNING DATA ANALYSIS ====")
        run_analysis()
        
    if args.train:
        logger.info("==== RUNNING MODEL TRAINING ====")
        run_training()
        
    if args.serve:
        logger.info("==== RUNNING API SERVER ====")
        start_server()

if __name__ == "__main__":
    main()
