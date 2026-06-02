# download_all_models.py
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

print("="*50)
print("Downloading all required models...")
print("="*50)
print()

# Step 1: Download sentence transformer embeddings model
print("[1/2] Downloading sentence transformer model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model downloaded and cached!")
print()

# Step 2: Download TinyLlama model
print("[2/2] Downloading TinyLlama model (TinyLlama/TinyLlama-1.1B-Chat-v1.0)...")
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
print("✅ TinyLlama model downloaded and cached!")
print()

print("="*50)
print("All models downloaded successfully! The app should now work!")
print("="*50)
