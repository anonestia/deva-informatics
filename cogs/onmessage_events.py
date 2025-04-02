from .chat_manager import load_history, save_history, format_history, clear_history_file, add_to_history, generate_ai_response, generate_agent_response, deepContext_generate
from .knowledge_management import knowledge_recall
from .keyword_management import find_similar_LTM
from .user_identification import get_userInfo, fetch_users
import discord, sqlite3
from discord import app_commands
from discord.ext import commands
import random, os, json, re

class OnMessageEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/activechan.json"
        self.always_reply_channels = self.load_channels()

    def load_channels(self):
        """Loads the always-reply channels from JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    return set(json.load(f))  # Load as a set
                except json.JSONDecodeError:
                    return set()  # If file is corrupted, reset
        return set()

    def save_channels(self):
        """Saves the always-reply channels to JSON file."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)  # Ensure 'data/' exists
        with open(self.file_path, "w") as f:
            json.dump(list(self.always_reply_channels), f, indent=4)
    
    def make_keyword(self, summary):
        prompt = f"Summary text:\n{summary}\nFrom this summary above, determine the keywords. Keywords are used to decide if it is relevant enough or not to be remembered. The more keywords matched, the more likely it gets recalled. Get up to 10 keywords, and less keywords are okay. Keywords are short. like jadwal, 2A, Senin, dosen, informatika. Do not add additional words and just say the keywords right away SEPARATED WITH COMMAS."
        return generate_agent_response(prompt)
    
    def do_longTermMemory(self, chat_history, ltmType, DiscordID):
        """
        From the chat_history, extract valuable points and save them as long-term memory in a database.
        """
        connection = sqlite3.connect('data/ltm.db')
        cursor = connection.cursor()

        # Generate summary
        prompt = (
            "Based on the conversation below, generate a summary of the valuable information worth remembering for the far future (long-term memory)."
            "Heavily reference the latest message. Keep notes concisely; names, events, objects, etc. Exclude irrelevant, non-time based, and generic information that can be found anywhere. Write the dates if necessary or it is a time-based event/memory, otherwise don't write at all."
            "Do not make generic information like 'user wants to learn something' or 'user asked deva to do this'. Do not be overly detailed. If by chance the chat_history only states generic information, then only return 'No update needed'."
            "Do not add any additional words; just return the summary.\n"
            f"The conversation:\n{chat_history}"
        )
        summary = generate_agent_response(prompt)

        if ltmType == "personal":
            # Check if DiscordID already exists
            cursor.execute(f"SELECT summary FROM {ltmType} WHERE DiscordID = ?", (DiscordID,))
            existing_entry = cursor.fetchone()

            if existing_entry:
                existing_summary = existing_entry[0]

                if existing_summary != summary:  # Only merge if summary has changed
                    prompt = (
                        "There are two summaries:\n"
                        f"Summary 1 (older):\n{existing_summary}\n"
                        f"Summary 2 (newer):\n{summary}\n"
                        "Merge these two summaries, keeping all valuable details. Remove excessive details and unnecessary informations. Remove assumably old summary that won't be used anymore or is a junk information."
                        "Prioritize the latest information and resolve contradictions. "
                        "More than two paragraphs is allowed. Totally adjust the old summary is tolerable. Do not add extra words; return only the merged summary."
                    )
                    summary = generate_agent_response(prompt)

                    keyword = self.make_keyword(summary)

                    # Try to update
                    cursor.execute(
                        f"UPDATE {ltmType} SET summary = ?, keyword = ? WHERE DiscordID = ?", 
                        (summary, keyword, DiscordID)
                    )

                    if cursor.rowcount == 0:  # If update didn't happen, insert instead
                        cursor.execute(
                            f"INSERT INTO {ltmType} (DiscordID, summary, keyword) VALUES (?, ?, ?)", 
                            (DiscordID, summary, keyword)
                        )
                else:
                    print("Summary hasn't changed, skipping update.")
            else:
                # Insert new entry if no previous data exists
                keyword = self.make_keyword(summary)
                cursor.execute(
                    f"INSERT INTO {ltmType} (DiscordID, summary, keyword) VALUES (?, ?, ?)", 
                    (DiscordID, summary, keyword)
                )

        elif ltmType == "general":
            keyword = self.make_keyword(summary)
            cursor.execute(
                f"INSERT INTO {ltmType} (DiscordID, summary, keyword) VALUES (?, ?, ?)", 
                (DiscordID, summary, keyword)
            )

        connection.commit()
        connection.close()
        print(f"Long-term memory updated successfully for {ltmType}.")

        
    def get_longTermMemory(self, chat_history, DiscordID):
        connection = sqlite3.connect('data/ltm.db')
        cursor = connection.cursor()
        
        cursor.execute("SELECT summary FROM personal WHERE DiscordID = ?", (DiscordID,))
        personalLTM = cursor.fetchone()
        connection.commit()
        
        cursor.execute("SELECT id, summary, keyword FROM general")
        generalLTM = cursor.fetchall()  # ✅ Add parentheses to execute fetch
        connection.commit()
        
        relevant_entries = find_similar_LTM(generalLTM, chat_history)
        
        if relevant_entries:
            placeholders = ','.join(['?'] * len(relevant_entries))
            cursor.execute(f"SELECT summary FROM general WHERE id IN ({placeholders})", relevant_entries)
            filtered_summaries = cursor.fetchall()
        else:
            filtered_summaries = []

        # Format the output string
        if filtered_summaries:
            result_text = "General long-term memories:\n" + "\n\n".join(summary[0] for summary in filtered_summaries)
        else:
            result_text = ""

        # Format personal LTM properly
        personal_text = f"Personal Long-Term Memory for ID {DiscordID}:\n{personalLTM[0]}" if personalLTM else ""

        # Ensure we don't return unnecessary newlines
        if personal_text and result_text:
            return f"{personal_text}\n\n{result_text}"
        elif personal_text:
            return personal_text
        elif result_text:
            return result_text
        else:
            return ""
        
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
        
    @app_commands.command(name="always_reply", description="Toggle selalu membalas di channel ini.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_always_reply(self, interaction: discord.Interaction):
        """Slash command to toggle always-reply for a channel."""
        channel_id = interaction.channel_id

        if channel_id in self.always_reply_channels:
            self.always_reply_channels.remove(channel_id)
            await interaction.response.send_message("❌ Berhasil dimatikan.\nDeva hanya akan membalas apabila mendapat mention **@Deva** atau di-reply.")
        else:
            self.always_reply_channels.add(channel_id)
            await interaction.response.send_message("✅ Berhasil dinyalakan.\nDeva akan selalu menjawab di channel ini tanpa mention dan reply.")

        self.save_channels()

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

        # Conditions for the bot to reply
        is_intentional = (
            isinstance(message.channel, discord.DMChannel) or
            message.channel.id in self.always_reply_channels or
            self.bot.user in message.mentions
        )
        is_initiative = random.randint(1, 100) <= 5

        if is_intentional or is_initiative:
            async with message.channel.typing():
                try:
                    if is_intentional:
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
                    
                    ltm_information = self.get_longTermMemory(chat_history, message.author.id)
                    
                    knowledge_prompt = (
                        f"Perhatikan informasi pengguna di bawah ini!\n{user_information}"
                        f"Perhatikan percakapan ini!\n{chat_history}\n"
                        "Kamu membalas sebagai Deva. Apakah ada pertanyaan berkaitan dengan jadwal, dosen, dan hal lain yang berkaitan dengan informasi kampus?"
                        "Pembahasan bisa jadi disebutkan secara tersirat. Apabila ditemukan kata-kata berkaitan pada hal spesifik, real-time, dan unik kampus yang bukanlah informasi yang biasa diakses publik serta dibutuhkan info terkini, maka itu membutuhkan konteks tambahan. Informasi tentang mahasiswa tertentu tidak ada di sini, jadi pertanyaan mentions seperti <@1234567890> tidak terhitung."
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
                            f"{ltm_information}"
                            f"This is a conversation history:\n{chat_history}.\n"
                            f"\nUser's latest message:\n{message.author.display_name}: {message.content}\nYou: "
                        )
                    else:
                        prompt = (
                            f"{instruction}"
                            f"{user_information}"
                            f"{ltm_information}"
                            f"This is a conversation history:\n{chat_history}.\n"
                            f"\nUser's latest message:\n{message.author.display_name}: {message.content}\nYou: "
                        )
                    
                    response = generate_ai_response(prompt, (
                        f"This is information about user in the conversation:\n{user_information}"
                        f"This is the chat history:\n{chat_history}"
                        f"User's latest message:\n{message.author.display_name}: {message.content}"
                    ))

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
                    return
            ltm_prompt = (
                f"Perhatikan informasi pengguna di bawah ini!\n{user_information}"
                f"Perhatikan percakapan ini!\n{chat_history}\n"
                "Kamu membalas sebagai Deva. Kamu mengambil keputusan untuk mengingat atau tidak sebagai tutor."
                "Keputusan mengingat bisa jadi atas keinginan Deva sendiri (inisiatif), diminta oleh pengguna (perintah), ataupun impact kepada Deva secara pengalaman. Jenis ingatan:"
                "general: Informasi umum yang terkait dengan kampus, pengetahuan umum di dunia yang merupakan hal terupdate dan real-time, dan hal serupa. HARUS ADA FAKTOR REAL-TIME UPDATE. Pertanyaan meliputi cara programming tidak termasuk di sini, kecuali secara eksplisit menyebutkan versi yang lebih baru."
                "personal: Apabila itu terkait hal khusus pengguna, seperti preferensi cara belajar, preferensi pada bahasa program atau metode tertentu, keinginan belajar tertentu, proyek pribadi pengguna, dan hal serupa. HARUS ADA FAKTOR PREFERENSI. Pertanyaan umum penjelasan program tidak termasuk di sini. Hanya catatan personal."
                "none: Apabila kedua hal di atas tidak terpenuhi, terlalu personal, terlalu generic, atau tidak penting untuk diingat sebagai tutor. Chitchat dan candaan termasuk pada none."
                "Balas hanya dengan salah satu jenis di atas tanpa kata tambahan. Titik beratkan pada chat paling terakhir; apabila chat berada di pertengahan atau atas, kemungkinan besar sudah diingat oleh Deva. Jangan anggap hal sepele harus disimpan."
            )
            ltm_decision = generate_agent_response(ltm_prompt)
            print(f"LTM Decision: {ltm_decision}\n====================")
                    
            if ltm_decision == "personal" or ltm_decision == "general":
                self.do_longTermMemory(chat_history, ltm_decision, message.author.id)


async def setup(bot):
    await bot.add_cog(OnMessageEvent(bot))