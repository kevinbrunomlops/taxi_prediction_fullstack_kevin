from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data"
MODELS_PATH = PROJECT_ROOT / "model_development"

TAXI_CSV_PATH = DATA_PATH / "taxi_trip_pricing.csv"
MODEL_PATH = MODELS_PATH / "taxi_price_model.joblib"