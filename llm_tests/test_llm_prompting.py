import ollama

agent1 = {
  'name': 'agent1',
  'messages' : [],
}

prompt = '''Hi! Your name is agent1. You are in an escape room.
Here are the objects in the room and their associated functions:

door:
  def examine()
  def unlock(code: int)

paper:
  def examine()

Only respond with one function call.
'''

agent1['messages'].append({"role": "user", "content": prompt})
stream = ollama.chat(model="deepseek-r1:32b", messages=agent1['messages'], stream=True)

response = ""
for chunk in stream:
    part = chunk['message']['content']
    print(part, end='')
    response += part

agent1['messages'].append({"role": "assistant", "content": response})

agent1['messages'].append({"role": "assistant", "content": response})
