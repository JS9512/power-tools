
import sys
from PIL import Image
from config import serverConfig

import google.generativeai as genai
genai.configure(api_key= serverConfig.gemini_key)
model =  genai.GenerativeModel('gemini-pro-vision')

prompt = "Give all text in the image"
response = model.generate_content([prompt, Image.open(sys.argv[1]).convert("RGB")])
response.resolve()
text =  response.text
print(text)