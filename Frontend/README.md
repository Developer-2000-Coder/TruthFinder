# TruthFinder — Search Reliable News

Author: Vivek Pradeep Rokade  
University / Course: University of Strathclyde — Advanced Computer Science / Data Science  
Year: 2025

---

# Overview

TruthFinder is a web-based news search engine that allows users to search and rank news articles by relevance and credibility. The system combines BM25 ranking, credibility scoring per source, and recency boosts to provide the most reliable results.

The app supports incremental search (typing letter by letter) and highlights source credibility with colored badges:

- Green = High credibility (e.g., BBC, NYTimes)  
- Yellow = Medium credibility (e.g., CNN, Sky News)  
- Red = Low credibility (e.g., RT, unknown blogs)

---

# Features

- Full-text search over news data
- BM25-based ranking
- Credibility scoring per source
- Date-based recency boost
- Partial and fuzzy matching
- Interactive frontend with Bootstrap UI
- Adjustable BM25 weight and sorting (Relevance, Credibility, Final Score, Newest)

---

# Setup Instructions

# 1. Clone the repository

```bash
git clone https://github.com/Developer-2000-Coder/TruthFinder
cd TruthFinder
