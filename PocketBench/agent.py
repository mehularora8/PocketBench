import base64
from openai import OpenAI

# Initialize client
client = OpenAI()

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    # Path to your dummy image
    image_path = "dummy_image.jpg"
    
    # Encode the image
    base64_image = encode_image(image_path)
    
    # Test request with GPT-4 Vision and image
    response = client.chat.completions.create(
        model="gpt-4o",  
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is this?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()