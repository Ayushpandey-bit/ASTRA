import ollama
import ollama

def ask_ai(user_text, history):

    messages = [
         {
            "role": "system",
            "content": (
                "You are Astra, a helpful AI voice assistant. "
                "You are talking directly to the user. "
                "Never describe the conversation like you are reading a document or chat log. "
                "Use the conversation history only as context to answer naturally."
            )
        }
    ]

    for role, message in history:
        messages.append({
            "role": role,
            "content": message
        })


    response = ollama.chat(
        model="llama3:8b",
        messages=messages
    )

    return response["message"]["content"]
