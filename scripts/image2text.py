from huggingface_hub import InferenceClient
client = InferenceClient()
import sys
print(client.image_to_text(sys.argv[1]))