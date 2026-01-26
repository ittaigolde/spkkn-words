"""
Warmup script for ML models.
Run this once after installing detoxify to download the model (~400MB).
"""
from detoxify import Detoxify
from better_profanity import profanity

print("Warming up ML models...")
print("\n1. Loading detoxify model (this will download ~400MB on first run)...")

try:
    model = Detoxify('original')
    # Test prediction to ensure model is loaded
    result = model.predict("test")
    print("   ✓ Detoxify model loaded successfully!")
    print(f"   Sample prediction: {result}")
except Exception as e:
    print(f"   ✗ Error loading detoxify: {e}")

print("\n2. Loading better-profanity...")
try:
    # Load the profanity filter
    profanity.load_censor_words()
    test_result = profanity.contains_profanity("test word")
    print(f"   ✓ Better-profanity loaded successfully!")
    print(f"   Sample check: {test_result}")
except Exception as e:
    print(f"   ✗ Error loading better-profanity: {e}")

print("\n✓ All ML models warmed up and ready!")
print("You can now start the server with: uvicorn app.main:app --reload")
