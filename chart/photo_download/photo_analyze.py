import base64
import os
import logging
from openai import OpenAI
from credentials import openai_api_key

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load OpenAI API key
openai_api_key = openai_api_key

if not openai_api_key:
    raise ValueError("Please set your OpenAI API key in the environment variable 'OPENAI_API_KEY'.")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Folder where images are saved
output_folder = 'images'

def get_latest_image(folder):
    """Get the latest image from the specified folder."""
    files = [f for f in os.listdir(folder) if f.endswith('.png')]
    if not files:
        logger.error("No .png files found in the images folder.")
        return None
    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(folder, f)))
    return os.path.join(folder, latest_file)

def encode_image(image_path):
    """Encode image to Base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image(image_path):
    """Send the image description to OpenAI GPT and get analysis."""
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that responds in Markdown. Help me with my technical analysis!"},
            {"role": "user", "content": [
                {"type": "text", "text": "Please analyze this chart and provide major and minor support and resistance levels."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content

def main():
    latest_image = get_latest_image(output_folder)
    if not latest_image:
        logger.error("No latest image to analyze.")
        return

    logger.info(f"Analyzing image: {latest_image}")
    analysis = analyze_image(latest_image)
    print("Technical Analysis:")
    print(analysis)

if __name__ == "__main__":
    main()