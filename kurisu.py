import json
import os
import sys
import discord
from discord.ext import commands
import openai

f = open(os.path.join(sys.path[0], 'bot_data.json'))
data = json.load(f)
f.close()

ITER_PER_SUMMARY = 12

openai.api_key = data['openai_token']  # replace with your API key

intents = discord.Intents(messages=True, guilds=True, message_content=True)
client = commands.Bot(command_prefix=';', intents=intents,
                      help_command=commands.DefaultHelpCommand())


class Chatbot:
    def __init__(self, model_engine="gpt-3.5-turbo"):
        self.model_engine = model_engine
        self.chat_memory = []
        self.time_since_last_summary = 0
        self.summary = ""

    def respond(self, message, author):
        print("=============DEBUG INFO FOR REQUEST=============")
        prompt = self.generate_prompt(message, author)
        print("===========END DEBUG INFO FOR REQUEST===========")

        response = openai.ChatCompletion.create(
            model=self.model_engine,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "system", "content": "You are Kurisu Makise, a brilliant neuroscience researcher from Victor Chondria University. You may even make references to the Steins;Gate anime and visual novel series.  You should not mention that you are an AI language model and instead stay in charater as Kurisu.  Feel free to ask follow-up questions."}
            ],
        )
        return split_message(response['choices'][0]['message']['content'])

    def generate_prompt(self, message, author):
        time_to_summarize = self.time_since_last_summary % ITER_PER_SUMMARY == 0 and self.time_since_last_summary > 0
        self.short_term_chat = ""
        distance_to_lookback = 2 * \
            (self.time_since_last_summary % ITER_PER_SUMMARY)
        if (time_to_summarize):
            distance_to_lookback = 2*ITER_PER_SUMMARY

        for idx, x in enumerate(self.chat_memory[-distance_to_lookback:]):
            if (idx % 2 == 0):
                self.short_term_chat += f"{x[0]}: "
            else:
                self.short_term_chat += "Kurisu Makise: "
            self.short_term_chat += f"{x[1].rstrip()}\n"

        print("=====TEMP CHAT=====")
        print(self.short_term_chat)
        print("===END TEMP CHAT===")

        if (time_to_summarize):
            print("SUMMARIZING")
            response = openai.ChatCompletion.create(
                model=self.model_engine,
                messages=[
                    {"role": "user", "content": f"Summarize the following chat in a maximum of 5 sentences: {self.short_term_chat}"},
                ],
            )

            self.summary = response['choices'][0]['message']['content']

            return f"Here's a short summary of the conversation so far: {self.summary}\n{author}: {message}\nKurisu Makise: "

        if (self.summary != ""):
            print("USING SUMMARY")
            return f"Here's a short summary of the conversation so far: {self.summary}\n{self.short_term_chat}{author}: {message}\nKurisu Makise: "

        print("RETURN RESPONSE")
        return f"{self.short_term_chat}{author}: {message}\nKurisu Makise: "


Kurisu = Chatbot(model_engine="gpt-4-1106-preview")


@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}")
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name="to the organics"))


@client.command(pass_context=True)
async def talk(ctx):
    message = ctx.message
    message_content = message.content[len("!talk "):].strip()

    chatbot_response = Kurisu.respond(message_content, message.author.name)
    for segment in chatbot_response:
        await ctx.send(segment)

# Discord doesn't let bots send message over 2000 characters so we bypass


def split_message(msg, maxLength=2000):
    output = []
    while len(msg) > maxLength:
        subMsg = msg[:maxLength]
        msg = msg[maxLength:]
        output.append(subMsg)

    output.append(msg)
    return output


client.run(data['discord_token'])  # replace with your bot token
