# Dash Amazon E-commerce Sales Dataset

Python Dash app for exploring Amazon e-commerce sales data.

## Dataset Source

This project uses the dataset from Kaggle:

- [E-Commerce Sales Dataset (Kaggle)](https://www.kaggle.com/datasets/sharmajicoder/e-commerce-sales-dataset?resource=download)

Current local dataset path:

- `dataset/amazon_sales_dataset.csv`

## App Stack

- Python 3.11
- Dash
- Pandas
- Plotly
- Docker

## Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   python app.py
   ```
3. Open:
   - `http://localhost:8080`

## Run with Docker

1. Build image:
   ```bash
   docker build -t dash-amazon-sales .
   ```
2. Run container:
   ```bash
   docker run --rm -p 8080:8080 dash-amazon-sales
   ```

## Deployment / Infrastructure Flow

This repository is intended to connect:

1. GitHub (source + CI trigger)
2. Spacelift (infrastructure orchestration)
3. Google Cloud Platform (target cloud)

High-level flow:

- Code changes are pushed to GitHub.
- GitHub integrates with Spacelift to trigger IaC workflows.
- Spacelift plans/applies infrastructure on GCP.
