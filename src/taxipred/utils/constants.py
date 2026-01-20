from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PACKAGE_ROOT / "data"
MODELS_PATH = PACKAGE_ROOT / "model_development"

TAXI_CSV_PATH = DATA_PATH / "taxi_trip_pricing.csv"
TAXI_CLEANED_CSV = MODELS_PATH / "taxi_cleaned_training_data.csv"
MODEL_PATH = MODELS_PATH / "taxi_price_model.joblib"
