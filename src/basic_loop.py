import os
import sys
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

openai = os.getenv("OPENAI_API")

client = OpenAI(
    api_key=openai
)

def start_chatbot():
    print("cli bot starting")

    messages = [
        {"role": "system", "content": "you are helpful cli assistant"}
    ]

    while True:
        try:
            user_input = input("You: ")

            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye")
                break

            # check if the stripped input is not empty 
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            reply = response.choices[0].message.content
            print(f"\nCliBot: {reply}")

            messages.append({"role":"assistant", "content": reply})
        except Exception as e:
            print(f"\nAn error occurred: {e}")

start_chatbot()
