# Project Resume Description & Interview Preparation

This document serves as a reference for resume bullets and interview talking points for the **Movie Recommendation & Analysis System** project.

---

## 📝 Simplified Resume Description

**Movie Recommendation & Analysis System (Python, MySQL & Flask)**
- Built a movie recommendation system using Python and SQL to analyze user ratings and movie datasets.
- Designed an ETL pipeline using Pandas to clean and process data before storing it in a MySQL database.
- Performed SQL-based analysis to identify top-rated movies and genre trends.
- Implemented a recommendation engine using TF-IDF and cosine similarity to suggest movies based on genre similarity.
- Developed a Flask REST API to serve real-time recommendations and analytics in JSON format.

---

## 💬 Interview Preparation (First Person)

### 1-Minute Project Pitch
> "I built a **Movie Recommendation & Analysis System** using Python, MySQL, and Flask to explore database engineering and basic recommendation logic. 
> 
> First, I wrote an **ETL pipeline** that downloads the raw MovieLens dataset, cleans missing entries, parses the movie release years using regular expressions, and bulk-loads the data into a structured **MySQL database** table. 
> 
> To generate recommendations, I built a **genre matching engine** that vectorizes movie genres using TF-IDF and compares them using **Cosine Similarity**. To optimize latency, I precomputed this similarity matrix offline and cached it as a **Pickle file**. On startup, my Flask API loads this pickle into memory, allowing recommendation lookups to complete in **under 5 milliseconds**. Finally, I wrote SQL analytical queries to report top-performing genres and ratings."

### Common Interview Q&As

**Q1: What does Cosine Similarity do in your project, and how does it work?**
> **My Answer**: "Cosine similarity is a simple logic that measures how similar two movies are based on their genres. In my system, I first convert the movie genre text (like 'Action|Adventure') into numerical vectors using TF-IDF. Then, Cosine Similarity calculates the angle between these vectors. If two movies share similar genres, their vectors point in the same direction, resulting in a score close to 1.0. If they have no genres in common, the score is 0.0. It provides a simple, explainable way to recommend items without needing heavy calculations."

**Q2: How did you implement caching, and why is it important?**
> **My Answer**: "Running TF-IDF and calculating Cosine Similarity matrices over thousands of movies on-the-fly inside an API call is computationally slow and would cause a lag in user requests. To prevent this, I precompute the similarity matrix during an offline training step (`main.py --train`) and save the output using Python’s `pickle` library. When my Flask server starts, it loads this precomputed file into memory. Because the API only has to read indices from RAM rather than doing math on the fly, recommendations load in under 5 milliseconds."

**Q3: How does your ETL pipeline clean the raw data?**
> **My Answer**: "My ETL pipeline handles three main cleaning tasks using Pandas. First, it drops any records containing missing values in ratings or titles. Second, it resolves duplicate reviews by sorting by timestamp and keeping only the most recent review for any user-movie pair. Lastly, I wrote a regular expression (`\s*\((\d{4})\)\s*$`) to extract parenthetical release years from movie titles (like extracting 1995 from 'Toy Story (1995)'). This cleans up the titles for display and allows me to save a clean `release_year` integer column in SQL for sorting."

**Q4: Why did you migrate from SQLite to MySQL, and what changes were required?**
> **My Answer**: "I migrated to MySQL to represent a production-ready database environment where database records run on a dedicated server rather than a local file. The migration required updating the python connector package to `mysql-connector-python` and modifying standard SQL statement placeholders from SQLite's `?` to MySQL's `%s`. I also set up a custom B-tree indexing configuration check to query `INFORMATION_SCHEMA.STATISTICS` dynamically before running table edits."
