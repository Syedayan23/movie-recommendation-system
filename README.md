# Movie Recommendation & Analysis System

A clean, beginner-friendly movie analysis and recommendation system built with Python, MySQL, Pandas, Scikit-Learn, and Flask. 

This platform downloads the MovieLens dataset, executes an ETL pipeline, stores data in an optimized MySQL database, executes data visualizations, precomputes a genre-based similarity recommender, and serves suggestions via a Flask API.

---

## 📸 Architecture Diagram

```
                             [ User CLI / main.py ]
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      ▼
           [ --etl ]             [ --analyze ]           [ --train ]         [ --serve ]
             ├── Download Raw      ├── Query SQL statistics └── TF-IDF Cosine   └── Flask Server
             ├── Parse title/year  └── Save plots to disk       Similarity          (Loads Pickle)
             └── Load MySQL Tables
```

```
                   [ Raw MovieLens CSVs (movies, ratings) ]
                                    │
                                    ▼ (Extract/Transform)
                           [ src/etl.py ]
                                    │
                         ┌──────────┴──────────┐
                         ▼ (Load)              ▼ (Train Data)
               [ MySQL Database Server ]       [ src/recommender.py ]
                         │                     │ (Precompute & Caching)
                (SQL queries)                  ▼
             [ src/analysis.py ]        [ genre_similarity_model.pkl ]
                         │                     │
                         ▼ (Charts & Insights) ▼ (Memory Caching)
                  [ data/processed/ ] <────[ api/app.py (Flask API) ]
```

---

## ⚙️ MySQL Configuration (Environment Variables)

The database driver reads connection configurations from the environment. You can set these variables in your shell before running the scripts, or the application will fallback to the defaults below:

| Environment Variable | Description | Default Value |
| :--- | :--- | :--- |
| `DB_HOST` | Host address of the MySQL Server | `localhost` |
| `DB_PORT` | Port of the MySQL Server | `3306` |
| `DB_USER` | Username for database connection | `root` |
| `DB_PASSWORD` | Password for database user | `password` |
| `DB_NAME` | Name of the database schema | `movie_platform` |

To set them in PowerShell:
```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="yourpassword"
```

To set them in Linux/macOS:
```bash
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASSWORD="yourpassword"
```

---

## ⚡ Caching & Cosine Similarity Explanation

### 1. What is Cosine Similarity?
Cosine similarity is a simple logic that measures how similar two movies are based on their genres. For example, if two movies share the exact same categories (like "Action" and "Adventure"), they will have a high similarity score (close to 1.0). If they share no genres (like a Comedy and a Horror film), they will have a low similarity score (close to 0.0).

### 2. Caching Design
Computing movie similarity across thousands of films during a live API call creates a performance bottleneck. To solve this, I calculate all movie similarities beforehand in an **offline training step** (`python main.py --train`) and save the results into a file using **Pickle**. On startup, the Flask server loads this precomputed file into memory. API queries run in **under 5 milliseconds** because the server only has to read pre-calculated scores rather than computing them on the fly.

---

## 📂 Project Directory Structure

```
movie-recommendation-system/
│
├── api/
│   └── app.py               # Flask API serving genre recommendations and SQL analytics
│
├── data/
│   ├── raw/                 # Raw MovieLens source files
│   └── processed/           # Cleaned CSVs and saved Seaborn visual charts
│
├── notebooks/
│   └── eda.ipynb            # Jupyter Notebook for database querying and visualization (MySQL)
│
├── src/
│   ├── __init__.py
│   ├── etl.py               # ETL pipeline (Download, Extract, Clean, MySQL Load)
│   ├── database.py          # MySQL database schema, connections, and aggregations
│   ├── analysis.py          # Analytics and visualization script
│   ├── recommender.py       # Recommendation engine (TF-IDF Cosine Similarity)
│   └── utils.py             # Unified logging and download helper utilities
│
├── requirements.txt         # Package dependencies list
├── Dockerfile               # Docker container specification
└── main.py                  # CLI entry point orchestrator
```

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure and Run your MySQL Server
Ensure a MySQL server is running and accessible using the credentials defined in your environment variables.

### 3. Execute Orchestration Steps
- **Ingest Data**: Download, clean, and write records to MySQL:
  ```bash
  python main.py --etl
  ```
- **Precompute Similarities**: Fit TF-IDF genre models and cache them:
  ```bash
  python main.py --train
  ```
- **Generate Analytics Visualizations**: Export Seaborn plots to disk:
  ```bash
  python main.py --analyze
  ```
- **Start Flask API Server**: Launches local endpoints on port 5000:
  ```bash
  python main.py --serve
  ```

---

## 🐳 Containerization (Docker)
Build and run the API server using Docker:
```bash
# Build the Docker image
docker build -t movie-platform .

# Run the container (pass MySQL variables if connection is remote/local)
docker run -p 5000:5000 -e DB_HOST="host.docker.internal" -e DB_PASSWORD="yourpassword" movie-platform
```

---

## 🔌 API Endpoints

All responses return standard JSON format:

* **Get Movie Recommendations (`GET /recommend/movie/<movie_id>?count=2`)**:
  ```json
  {
    "status": "success",
    "data": [
      { "genres": "Adventure|Animation|Children|Comedy|Fantasy", "movie_id": 2294, "score": 1.0, "title": "Antz" },
      { "genres": "Adventure|Animation|Children|Comedy|Fantasy", "movie_id": 3114, "score": 1.0, "title": "Toy Story 2" }
    ],
    "message": "Successfully fetched top 2 recommendations similar to movie 1"
  }
  ```
* **Top-Rated SQL Analytics (`GET /analytics/top-movies?limit=2`)**:
  ```json
  {
    "status": "success",
    "data": [
      { "movie_id": 318, "title": "Shawshank Redemption, The", "avg_rating": 4.43, "rating_count": 317 }
    ],
    "message": "Top-rated movies queried successfully."
  }
  ```
* **Genre aggregations (`GET /analytics/genre-insights`)**:
  ```json
  {
    "status": "success",
    "data": [
      { "genres": "Drama", "avg_rating": 3.66, "rating_count": 41928 }
    ],
    "message": "Genre analytics loaded successfully."
  }
  ```


