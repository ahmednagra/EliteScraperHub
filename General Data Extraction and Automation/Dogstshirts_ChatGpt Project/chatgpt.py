from method import get_key_values_from_file
from openai import OpenAI


def get_openai_completion(api_key, system_prompt="", user_prompt=""):
    client = OpenAI(api_key=api_key)
    model = "gpt-3.5-turbo"
    # model = "text-davinci-003"
    a = client.chat.completions(
          model=model,
          messages=[ {"role": "user", "content": user_prompt}],
          max_tokens=100,
      )
    a=1
    completion = client.Chat.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return completion['choices'][0]['message']['content']


# Set your OpenAI API key
key = get_key_values_from_file().get('chatGPT')

# Example usage:
system_prompt = "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."
user_prompt = "Compose a poem that explains the concept of recursion in programming."
result = get_openai_completion(api_key=key, system_prompt=system_prompt, user_prompt=user_prompt)

print(result)

a = 1
