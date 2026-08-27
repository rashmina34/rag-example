from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client() 

chat = client.chats.create(model="gemini-3.5-flash")

r1 = chat.send_message("My name is Sam.")
# print(r1.text)

r2 = chat.send_message("What's my name?")
# r2 = chat.send_message("Write a 3-sentence, upbeat product description for a dog leash aimed at first-time dog owners.")
# print(r2.text)

for message in chat.get_history():
    print(message.role, ":", message.parts[0].text)