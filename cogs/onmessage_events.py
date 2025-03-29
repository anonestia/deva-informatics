from .chat_manager import load_history, save_history, format_history, clear_history_file, add_to_history, generate_ai_response, generate_agent_response, deepContext_generate
from .knowledge_management import knowledge_recall
from .user_identification import get_userInfo, fetch_users
import discord
from discord.ext import commands
import random, os, json, re
from collections import defaultdict

class OnMessageEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def get_instruction(self, type):
        # Path to the JSON file (adjusted for the 'cogs' folder structure)
        json_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'to_reply.json')

        # Read and extract data from the JSON file
        try:
            with open(json_path, 'r') as file:
                instructions = json.load(file)
            return instructions.get(type, 'Not provided')
        except FileNotFoundError:
            print("Error: instructions.json file not found.")
            return "Error: Could not generate response because the JSON file is missing."
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON.")
            return "Error: Could not generate response due to invalid JSON format."
        
    def get_history_path(self, channel_or_user):
        if isinstance(channel_or_user, discord.TextChannel):  # Server channel
            return f"chat_histories/{channel_or_user.id}.json"
        elif isinstance(channel_or_user, discord.User):  # Private chat
            return f"chat_histories/{channel_or_user.id}.json"

    def is_private_chat(self, message):
        return isinstance(message.channel, discord.DMChannel)
    
    async def send_message(self, channel, response):
        """Chunk response and send long messages, preserving code blocks and handling mixed content."""
        limit = 2000  # Discord message limit
        
        # Regex to identify code blocks
        codeblock_pattern = re.compile(r'(```(?:\w+)?\n.*?```)', re.DOTALL)
        
        chunks = codeblock_pattern.split(response)
        
        for chunk in chunks:
            if chunk.startswith('```') and chunk.endswith('```'):
                # Handle code block
                lines = chunk.splitlines(keepends=True)
                codeblock_lang = lines[0][3:].strip() if len(lines[0]) > 3 else ""
                content = ''.join(lines[1:-1])
                
                while len(content) > limit - len(f"```{codeblock_lang}\n\n```"):
                    part = content[:limit - len(f"```{codeblock_lang}\n\n```")]
                    split_index = part.rfind("\n")
                    if split_index == -1:
                        split_index = len(part)
                    
                    await channel.send(f"```{codeblock_lang}\n{part[:split_index]}\n```")
                    content = content[split_index:].lstrip()
                
                if content:
                    await channel.send(f"```{codeblock_lang}\n{content}\n```")
            else:
                # Handle plain text
                while len(chunk) > limit:
                    split_index = chunk[:limit].rfind(" ")
                    if split_index == -1:
                        split_index = limit
                    
                    await channel.send(chunk[:split_index])
                    chunk = chunk[split_index:].lstrip()
                
                if chunk:
                    await channel.send(chunk)
            
    @commands.command(name="reset", help="To reset the conversation history in the channel where this command is executed.")
    async def reset(self, ctx):
        is_bot_owner = await self.bot.is_owner(ctx.author)
        is_admin = ctx.author.guild_permissions.administrator if ctx.guild else False
        has_manage_messages = ctx.author.guild_permissions.manage_messages if ctx.guild else False

        if not (is_bot_owner or is_admin or has_manage_messages or isinstance(ctx.channel, discord.DMChannel)):
            await ctx.send("Maaf, gagal menghapus karena tidak memiliki izin.")
            return

        history_path = self.get_history_path(
            ctx.channel if isinstance(ctx.channel, discord.TextChannel) else ctx.author
        )
        
        clear_history_file(history_path)
        await ctx.send("Memori berhasil dihapus. Memulai percakapan dari awal.")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return  # Ignore bot's own messages
        
        if message.content in ["+reset", "+restart"]:
            return

        # Get history file path
        history_path = self.get_history_path(
            message.channel if isinstance(message.channel, discord.TextChannel) else message.author
        )
        history = load_history(history_path)

        # Add the received message to history
        history = add_to_history(
            history,
            user_id=message.author.id,
            user_display=message.author.display_name,
            user_message=message.content,
            ai_response= None,
            system_message= None
        )
        save_history(history_path, history)

        if isinstance(message.channel, discord.DMChannel) or self.bot.user in message.mentions or random.randint(1, 100) <= 5:
            async with message.channel.typing():  # Keep typing active
                try:
                    if self.bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
                        chat_history = format_history(history)
                        instruction = self.get_instruction('intentional_trigger')
                    else:
                        instruction = self.get_instruction('initiative_trigger')

                    messages = [msg async for msg in message.channel.history(limit=15)]
                    # Use a set to store unique user IDs
                    unique_user_ids = set()
                    for msg in messages:
                        if msg.author.id != message.author.id and msg.author.id != self.bot.user.id:
                            unique_user_ids.add(msg.author.id)
                    user_information = get_userInfo(str(message.author.id), [str(uid) for uid in unique_user_ids])
                    
                    if message.mentions:
                        mentioned_ids = [user.id for user in message.mentions]  # List comprehension
                        userMentioned = []
                        if mentioned_ids:
                            user_list = fetch_users(mentioned_ids, 0)
                            for i, user in enumerate(user_list):
                                nama, posisi, semester, kelas, tentang = user
                                
                                user_id = mentioned_ids[i]

                                # Full details for trigUser
                                user_info = f"Information for user ID {user_id}\n"
                                user_info += f"Nickname: {nama}\n"
                                if posisi != "":
                                    user_info += f"{posisi}, "
                                if semester != "":
                                    user_info += f"Semester: {semester}"
                                if kelas != "\n":
                                    user_info += f"{kelas}\n"
                                if tentang != "":
                                    user_info += f"About the mentioned user (not sender): {tentang}\n"

                                userMentioned.append(user_info)

                            # Return formatted user data
                            user_information += "\n\nUser(s) mentioned:\n" + ("\n\n".join(userMentioned) if userMentioned else "User mentioned none.")
                    print(user_information)
                    print(chat_history)
                    
                    knowledge_prompt = (
                        f"Perhatikan percakapan ini!\n{chat_history}\n"
                        "Kamu membalas sebagai Deva. Apakah ada pertanyaan berkaitan dengan jadwal, dosen, dan hal lain yang berkaitan dengan informasi kampus?"
                        "Pembahasan bisa jadi disebutkan secara tersirat. Apabila ditemukan kata-kata berkaitan pada hal spesifik dan unik kampus yang bukanlah informasi yang biasa diakses publik serta dibutuhkan info terkini, maka itu membutuhkan konteks tambahan. Informasi mahasiswa tidak ada di sini, jadi mentions seperti <@1234567890> tidak terhitung."
                        "Jawab hanya Y untuk ya, atau hanya N untuk tidak."
                    )
                    knowledge_decision = generate_agent_response(knowledge_prompt).strip()
                    print(f"Knowledge decision: {knowledge_decision}\n")
                    
                    if knowledge_decision == "Y":
                        knowledge = knowledge_recall(chat_history)
                    
                        prompt = (
                            f"{instruction}"
                            f"Below is your notes. Use the knowledge below as help to reply user's query. Do not alter information or imagine what's not given here.\n{knowledge}\n\n"
                            f"{user_information}"
                            f"This is a conversation history:\n{chat_history}.\n"
                            f"\nUser's latest message:\n{message.author.display_name}: {message.content}\nYou: "
                        )
                    else:
                        prompt = (
                            f"{instruction}"
                            f"{user_information}"
                            f"This is a conversation history:\n{chat_history}.\n"
                            f"\nUser's latest message:\n{message.author.display_name}: {message.content}\nYou: "
                        )
                    
                    deepContext_prompt = (
                        f"This is the chat history:\n{chat_history}"
                        f"User's latest message:\n{message.author.display_name}: {message.content}"
                    )
                    deep_context = deepContext_generate(deepContext_prompt).strip()
                    response = generate_ai_response(prompt, deep_context)

                    # Update history with bot's response
                    history = add_to_history(
                        history,
                        user_id=self.bot.user.id,
                        user_display=self.bot.user.name,
                        user_message= None,
                        ai_response=response,
                        system_message= None
                    )
                    save_history(history_path, history)

                    # Use the chunking function to send the response
                    await self.send_message(message.channel, response)
                except Exception as e:
                    await message.channel.send(f"Eh, maaf. Bisa ulangi?\n-# Error: {e}")    


async def setup(bot):
    await bot.add_cog(OnMessageEvent(bot))