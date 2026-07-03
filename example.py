import openai
import unittest

# Set your OpenAI API key
openai.api_key = 'your-api-key-here'

# Making a request to the OpenAI API
class TestOpenAIAPI(unittest.TestCase):

    def test_chat_completion(self):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, World!"}
            ]
        )
        self.assertIn('content', response.choices[0].message)
        print("Response: ", response.choices[0].message['content'])

if __name__ == '__main__':
    unittest.main()