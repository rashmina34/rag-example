from google import genai

client = genai.Client()  # reads GEMINI_API_KEY automatically

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Explain what an API is in one sentence."
)

print(response.text)