from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",  # the only change vs. normal OpenAI use
    api_key="gate-dev-key-123",           # your gateway key, not a Groq key
)

resp = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Explain what an API gateway is in one sentence."}],
)

print(resp.choices[0].message.content)
print("model:", resp.model)
print("tokens:", resp.usage.prompt_tokens, "+", resp.usage.completion_tokens)

# a wrong key should be rejected
bad = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="wrong-key")
try:
    bad.chat.completions.create(model="auto", messages=[{"role": "user", "content": "hi"}])
    print("ERROR: wrong key was accepted")
except Exception as e:
    print("wrong key rejected:", type(e).__name__)