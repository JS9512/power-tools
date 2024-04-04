import pdftotext
import sys

with open(sys.argv[1], "rb") as f:
    pdf = pdftotext.PDF(f)

print("\n\n".join(pdf))