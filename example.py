import openai

# Set your OpenAI API key
openai.api_key = 'your-api-key-here'

# Making a request to the OpenAI API
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, World!"}
    ]
)

# Printing the response from API
print(response.choices[0].message['content'])
