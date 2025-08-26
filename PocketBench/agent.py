from openai import OpenAI

# Initialize client
client = OpenAI()

def main():
    # Simple test request with GPT-4
    response = client.chat.completions.create(
        model="gpt-4.1",  # 👈 using GPT-4 here
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
