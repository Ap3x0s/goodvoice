"""Test transcriber on CPU."""
import sys
sys.path.insert(0, r"C:\Users\Евгений\Desktop\Projects\goodvoice")
from transcriber import Transcriber
import numpy as np

print("Testing transcriber with CPU...")
t = Transcriber(model_size="tiny", device="cpu")
t.load_model()
print("Model loaded on CPU")

audio = np.random.randn(16000).astype(np.float32) * 0.01
print("Transcribing...")
text = t.transcribe(audio, language="en")
print(f"Result: '{text}'")
print("Transcriber test passed!")
