import ollama
from game.world_model import print_world

class LLMGame:
    def __init__(self, model="deepseek-r1:32b"):
        self.agent_name = "llm"
        self.messages = []
        self.model = model

    def reset(self):
        self.messages = []

    
    def build_prompt(self):
        prompt = f"You are {self.agent_name}, inside an escape room. The current known world state is:\n"
        prompt += print_world()
        prompt += "\nReply with a single Python function call to act."
        return prompt

    def get_action(self, state=None):
        prompt = self.build_prompt()
        self.messages.append({"role": "user", "content": prompt})

        stream = ollama.chat(model=self.model, messages=self.messages, stream=True)
        response = ""
        for chunk in stream:
            part = chunk['message']['content']
            response += part

        self.messages.append({"role": "assistant", "content": response})
        return response.strip()
