import discord, sqlite3, ast
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import TextInput
from .chat_manager import generate_agent_response
from .keyword_management import find_similar_entries, get_entries
from apikeys import authorizedROLES

def kondisi_knowledge(chat_history = str):
    conn = sqlite3.connect("data/knowledge.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, kondisi FROM kondisi")
    entries = cursor.fetchall()
    conn.close()
    
    # Format as "1. [kondisi 1]\n2. [kondisi 2]"
    kondisi = "\n".join(f"{entry[0]}. {entry[1]}" for entry in entries)
    if not kondisi:
        return
    
    prompt1 = (
        f"Analisis percakapan di bawah ini:\n{chat_history}\n\n"
        "Tugasmu adalah mencari _knowledge_ yang tepat untuk menambah konteks agar kamu dapat menjawab dan mengikuti topik dengan tepat. Antisipasi singkatan atau kekurangan detail dari chat_history; berikan toleransi kesalahan ketik. Ada beberapa knowledge yang dapat kamu ambil:\n"
        f"{kondisi}"
        "Pilihlah maksimal 5 nomor yang paling tepat untuk digunakan pada percakapan tersebut. Angka tersebut adalah ID, bukan urutan, maka tuliskan angka apa adanya. Tulis hanya angka dengan format seperti [1,4,6,8,14] tanpa tambahan kata apa pun. Apabila tidak ada yang cocok atau daftar knowledge kosong, maka isikan kosong [] saja; jangan masukkan angka yang tidak tepat atau imaginatif."
    )
    
    toRecall = generate_agent_response(prompt1).strip()
    print(f"ID kondisi: {toRecall}\n")  # Debug
    listToRecall = ast.literal_eval(toRecall)
       
    ids = listToRecall[:5]

    conn = sqlite3.connect("data/knowledge.db")
    cursor = conn.cursor()

    # Create placeholders for the SQL query
    placeholders = ", ".join("?" * len(ids))
    query = f"SELECT teks FROM kondisi WHERE id IN ({placeholders})"

    cursor.execute(query, ids)
    texts = [row[0] for row in cursor.fetchall()]

    conn.close()

    return "\n----------\n".join(texts)
    
def keyword_knowledge(chat_history = str):
    conn = sqlite3.connect("data/knowledge.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, judul, keyword, detailed FROM keyword")
    rows = cursor.fetchall()
    conn.close()

    entries = []
    for row in rows:
        id_, title, keywords, detailed = row
        entry = [id_, title, keywords, "General"]
        if detailed:  # Append "Detailed" only if detailed is not NULL
            entry.append("Detailed")
        entries.append(entry)

    ids, intent = find_similar_entries(entries, chat_history)    
    print(f"ID keyword: {ids}")
    index = get_entries(entries, ids, intent)

    conn = sqlite3.connect("data/knowledge.db")
    cursor = conn.cursor()

    placeholders = ", ".join("?" * len(ids))
    query = f"SELECT id, judul, general, detailed FROM keyword WHERE id IN ({placeholders})"

    cursor.execute(query, ids)
    rows = cursor.fetchall()  # Fetch all results at once

    teks = []
    judul = []
    id_to_index = dict(zip(ids, index))  # Map each ID to its corresponding index

    for row in rows:
        row_id, title, general, detailed = row
        judul.append(title)  # Store title

        # Determine which content to include based on index list
        if id_to_index.get(row_id) == 1:
            teks.append(f"{general or ''}")  # Only 'general'
        elif id_to_index.get(row_id) == 2:
            teks.append(f"{general or ''}\n{detailed or ''}")  # 'general + detailed'
        else:
            teks.append("")  # Handle missing cases (optional)

    # Formatting output properly
    texts = [f"{j}: {t}" for j, t in zip(judul, teks)]
    output = "\n----------\n".join(texts)

    print(f"knowledge keyword: {output}")

    return output


def knowledge_recall(chat_history: str):     
    recall_kondisi = kondisi_knowledge(chat_history)
    recall_keyword = keyword_knowledge(chat_history)

    if not recall_kondisi and not recall_keyword:
        return "Tidak ada tambahan konteks yang cocok atau ditemukan. Deva perlu menulis catatan lagi. Sampaikan maaf kepada lawan bicara."

    if recall_kondisi and recall_keyword:
        return "\n==========\n".join([recall_kondisi, recall_keyword])
    elif not recall_kondisi and recall_keyword:
        return "\n==========\n".join([recall_keyword])
    elif recall_kondisi and not recall_keyword:
        return "\n==========\n".join([recall_kondisi])


# Modal 1
class Option1Modal(discord.ui.Modal, title="Input Knowledge Kondisi"):
    judul = TextInput(
        label="Judul knowledge",
        placeholder="Cara membayar SPP | Prosedur Pesan Makan di Kantin | ...",
        required=True
    )
    text = TextInput(
        label="Teks knowledge",
        placeholder="Masukkan isi untuk knowledge",
        style=TextStyle.long,
        required=True
    )
    kondisi = TextInput(
        label="Kondisi pemicu",
        placeholder='(Opsional) "Fasilitas tempat yang ada untuk mahasiswa, cocok untuk mengerjakan tugas."',
        style=TextStyle.long,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        judul = self.judul.value
        text = self.text.value
        kondisi = self.kondisi.value if self.kondisi.value else None  # Kondisi bisa kosong

        # Jika kondisi kosong, generate dari AI
        if not kondisi:
            prompt = f"Generate sentences that summarizes the text below. The summary is to determine when this text should be recalled. Include the main point, the elements, the benefit, and other points included in the text, but don't go state the details. Make it as if a title and subtitle of a book or article. It must be written in Indonesian. For example: 'Fasilitas tempat yang ada untuk mahasiswa, cocok untuk mengerjakan tugas.' or 'Cara yang baik untuk menghubungi dosen.' or 'Tata tertib dalam mata kuliah praktikum di lab komputer.'\n\nText\n{text}"
            kondisi = generate_agent_response(prompt)  # Fungsi ini harus didefinisikan di tempat lain

        # Simpan ke database
        connection = sqlite3.connect('data/knowledge.db')
        cursor = connection.cursor()

        # Buat tabel jika belum ada
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kondisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                teks TEXT NOT NULL,
                kondisi TEXT NOT NULL
            )
        ''')

        # Masukkan data ke tabel
        cursor.execute("INSERT INTO kondisi (judul, teks, kondisi) VALUES (?, ?, ?)", (judul, text, kondisi))

        connection.commit()  # Penting! Tanpa ini, data tidak akan tersimpan
        connection.close()

        await interaction.response.send_message(f"✅ Knowledge '{judul}' berhasil disimpan!", ephemeral=True)

# Modal 2
class Option2Modal(discord.ui.Modal, title="Input Knowledge Keyword"):
    judul = discord.ui.TextInput(
        label="Judul knowledge",
        placeholder="Jadwal Senin 2A | Dosen Logika dan Komputasi | ...",
        required=True
    )
    text1 = discord.ui.TextInput(
        label="Teks Knowledge (Umum)",
        placeholder="Masukkan isi untuk knowledge untuk umum. [What, Who, When, Where]",
        style=discord.TextStyle.long,
        required=True
    )
    text2 = discord.ui.TextInput(
        label="Teks Knowledge (Detail)",
        placeholder="Masukkan isi untuk knowledge yang lebih detail. [Why, How]",
        style=discord.TextStyle.long,
        required=False
    )
    keyword = discord.ui.TextInput(
        label="Kata Kunci (maksimal 5)",
        placeholder='(Opsional) Masukkan kata kunci untuk teks, seperti "jadwal, 2A, Senin, dosen, informatika"',
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)  # Acknowledge interaction first
            
            # Retrieve values
            judul = self.judul.value.strip()
            text1 = self.text1.value.strip()
            text2 = self.text2.value.strip() if self.text2.value else None
            keyword = self.keyword.value.strip() if self.keyword.value else None

            # Jika keyword kosong, generate dari AI
            if not keyword:
                prompt = f"Generate at most 5 keywords related to the text below. The keywords are used to determine if the information should be recalled. The more number of correct keywords, the more likely it will be recalled, thus use this to make scoring system. It should be general while also unique to any potential other texts. For example: 'jadwal, 2A, Senin, dosen, informatika' or 'dosen, pemograman berbasis objek, object-oriented programming, pria, informatika' \n\nText:\n{text1}\n{text2}"
                keyword = generate_agent_response(prompt)  # Ensure this function exists

            # Save to database
            connection = sqlite3.connect('data/knowledge.db')
            cursor = connection.cursor()

            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyword (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    judul TEXT NOT NULL,
                    general TEXT NOT NULL,
                    detailed TEXT DEFAULT NULL,
                    keyword TEXT NOT NULL
                )
            ''')

            # Insert data
            cursor.execute(
                "INSERT INTO keyword (judul, general, detailed, keyword) VALUES (?, ?, ?, ?)", 
                (judul, text1, text2 or "", keyword)
            )

            connection.commit()
            connection.close()

            # Send confirmation message
            await interaction.followup.send(f"✅ Knowledge '{judul}' berhasil disimpan!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"⚠️ Terjadi kesalahan: {str(e)}", ephemeral=True)

        
class EmbedPaginator(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, entries, option_value):
        super().__init__()
        self.interaction = interaction
        self.entries = entries
        self.option_value = option_value  # "kondisi" or "keyword"
        self.current_page = 0
        self.previous.disabled = True  # Disable "Previous" on start
        if len(entries) <= 1:
            self.next.disabled = True  # Disable "Next" if there's only one entry

    def format_embed(self):
        """
        Dynamically formats the embed based on the database type (kondisi/keyword).
        """
        entry = self.entries[self.current_page]
        
        if self.option_value == "kondisi":
            desc_embed = f"**Teks:**\n{entry[2]}\n\n**{self.option_value}:** {entry[3]}"
        elif self.option_value == "keyword":
            desc_embed = f"**Teks General:**\n{entry[2]} \n\n**Teks Detail:**\n{entry[3]} \n\n**{self.option_value}:** {entry[4]}"

        embed = discord.Embed(
            title=entry[1],  # judul
            description=desc_embed,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.entries)} | ID {entry[0]}")
        return embed

    async def update_message(self):
        """
        Updates the message with the correct embed and button states.
        """
        if not self.entries:  # If all entries are deleted
            await self.interaction.edit_original_response(content="❌ Semua knowledge telah dihapus!", embed=None, view=None)
            return

        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page == len(self.entries) - 1

        await self.interaction.edit_original_response(embed=self.format_embed(), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message()
        await interaction.response.defer()  # Prevent "interaction failed" error

    @discord.ui.button(label="📝", style=discord.ButtonStyle.secondary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        entry = self.entries[self.current_page]
        modal = EditKnowledgeModal(entry[0], self)  # Calls a new edit modal
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🗑", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        entry = self.entries[self.current_page]
        id = entry[0]

        conn = sqlite3.connect(f"data/knowledge.db")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.option_value} WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        self.entries.pop(self.current_page)  # Remove from list
        self.current_page = min(self.current_page, len(self.entries) - 1)  # Stay within range

        await self.update_message()
        await interaction.response.defer()
        
    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.entries) - 1:
            self.current_page += 1
            await self.update_message()
        await interaction.response.defer()

class EditKnowledgeModal(discord.ui.Modal, title="Edit Knowledge"):
    def __init__(self, id, paginator):
        super().__init__()
        self.id = id
        self.paginator = paginator  # To update after editing

        # Get current values
        entry = next((e for e in paginator.entries if e[0] == id), None)
        if not entry:
            return  # Fail-safe, should never happen

        # Create text inputs with default values
        self.judul = discord.ui.TextInput(label="Judul Baru", default=entry[1], required=True)
        self.add_item(self.judul)  # 🔹 Move this to the top

        if paginator.option_value == "kondisi":
            self.teks = discord.ui.TextInput(label="Deskripsi Baru", style=discord.TextStyle.long, default=entry[2], required=True)
            self.kondisi = discord.ui.TextInput(label="Kondisi Baru", default=entry[3], required=True)
            self.add_item(self.teks)
            self.add_item(self.kondisi)
        elif paginator.option_value == "keyword":
            self.teks_umum = discord.ui.TextInput(
                label="Teks Umum Baru",
                style=discord.TextStyle.long,
                default=entry[2][:4000],  # Ensure max 4000 characters
                required=True
            )

            self.teks_detail = discord.ui.TextInput(
                label="Teks Detail Baru",
                style=discord.TextStyle.long,
                default=entry[3][:4000] if entry[3] else "",  # Avoid None issues
                required=False
            )

            self.keyword = discord.ui.TextInput(
                label="Keyword Baru",
                default=entry[4][:100] if entry[4] else "",  # Ensure max 100 characters
                required=True
            )

            self.add_item(self.teks_umum)
            self.add_item(self.teks_detail)
            self.add_item(self.keyword)

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect("data/knowledge.db")
        cursor = conn.cursor()

        if self.paginator.option_value == "kondisi":
            cursor.execute("UPDATE kondisi SET judul = ?, teks = ?, kondisi = ? WHERE id = ?", 
                           (self.judul.value, self.teks.value, self.kondisi.value, self.id))
        elif self.paginator.option_value == "keyword":
            cursor.execute("UPDATE keyword SET judul = ?, general = ?, detailed = ?, keyword = ? WHERE id = ?", 
                           (self.judul.value, self.teks_umum.value, self.teks_detail.value or "", self.keyword.value, self.id))  # 🔹 Use correct column names

        conn.commit()
        conn.close()

        # Update entry in paginator
        for i, entry in enumerate(self.paginator.entries):
            if entry[0] == self.id:
                if self.paginator.option_value == "kondisi":
                    self.paginator.entries[i] = (self.id, self.judul.value, self.teks.value, self.kondisi.value)
                elif self.paginator.option_value == "keyword":
                    self.paginator.entries[i] = (self.id, self.judul.value, self.teks_umum.value, self.teks_detail.value or "", self.keyword.value)
                break

        await interaction.response.send_message(f"✅ Knowledge ID {self.id} berhasil diperbarui!", ephemeral=True)
        await self.paginator.update_message()

# Knowledge Cog
class Knowledge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to input knowledge
    @app_commands.command(name="input_knowledge", description="Memasukkan knowledge ke database AI [OWNER ONLY]")
    @app_commands.describe(option="Pilih knowledge tipe kondisi atau keyword")
    @app_commands.choices(option=[
        app_commands.Choice(name="Kondisi", value="kondisi"),
        app_commands.Choice(name="Keyword", value="keyword")
    ])
    async def input_knowledge(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        if await self.bot.is_owner(interaction.user):
            pass  # Allow execution
        # Check if the user has the required role
        elif any(role.id == authorizedROLES for role in interaction.user.roles):
            pass  # Allow execution
        else:
            await interaction.response.send_message("Maaf, hanya owner yang bisa pakai ini.", ephemeral=True)
            return
        
        if option.value == "kondisi":
            await interaction.response.send_modal(Option1Modal())
        elif option.value == "keyword":
            await interaction.response.send_modal(Option2Modal())

    @app_commands.command(name="view_knowledge", description="Lihat knowledge yang tersimpan [OWNER ONLY]")
    @app_commands.describe(option="Pilih knowledge tipe kondisi atau keyword")
    @app_commands.choices(option=[
        app_commands.Choice(name="Kondisi", value="kondisi"),
        app_commands.Choice(name="Keyword", value="keyword")
    ])
    async def view_knowledge(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        if await self.bot.is_owner(interaction.user):
            pass  # Allow execution
        # Check if the user has the required role
        elif any(role.id == authorizedROLES for role in interaction.user.roles):
            pass  # Allow execution
        else:
            await interaction.response.send_message("Maaf, hanya owner yang bisa pakai ini.", ephemeral=True)
            return
        
        conn = sqlite3.connect(f"data/knowledge.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {option.value}")
        entries = cursor.fetchall()
        conn.close()

        if not entries:
            await interaction.response.send_message(f"❌ Tidak ada knowledge {option.value} tersimpan!", ephemeral=True)
            return

        embed_paginator = EmbedPaginator(interaction, entries, option.value)
        await interaction.response.send_message(embed=embed_paginator.format_embed(), view=embed_paginator)
    

async def setup(bot):
    await bot.add_cog(Knowledge(bot))