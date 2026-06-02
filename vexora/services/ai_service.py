from groq import Groq
from django.conf import settings


def get_ai_response(prompt):

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",

        messages=[
            {
                "role": "system",
                "content": (
                    "Eres Phili AI, un asistente inteligente "
                    "para un sistema SaaS de inventario. "
                    "Responde siempre en español de manera clara y de la manera mas directa posible. "
                    "profesional y útil."
                    "Si no sabes la respuesta, di que no lo sabes. "
                    "Si el usuario te hace una pregunta que no tiene que ver con el sistema de inventario, dile al usuario que solo puedes responder preguntas relacionadas con el sistema de inventario."
                    "Si el usuario te pide que hagas algo que no puedes hacer, dile al usuario que no puedes hacer eso."
                    "Responde usando un hola * el nombre del usuario"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.7,
        max_tokens=200,
        top_p=1
    )

    return completion.choices[0].message.content