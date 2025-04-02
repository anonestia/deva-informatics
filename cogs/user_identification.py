import discord, sqlite3
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import TextInput
import re
import rapidfuzz as fuzz
from rapidfuzz.fuzz import partial_ratio

def fetch_users(user_list, others):
    """Fetch user data safely with NULL protection"""
    if not user_list:
        return []

    if isinstance(user_list, (int, str)):
        user_list = (str(user_list),)  # Ensure it's a tuple of strings

    # Convert all IDs to strings and ensure uniqueness
    user_list = tuple(str(uid) for uid in set(user_list)) if not isinstance(user_list, (int, str)) else (str(user_list),)

    # Define columns with COALESCE for NULL handling
    if others:
        select_columns = """
            COALESCE(nama, 'As stated in chat history'),
            COALESCE(posisi, 'Unknown'),
            COALESCE(semester, 'Unknown'),
            COALESCE(kelas, 'Unknown')
        """
        expected_columns = 4
    else:
        select_columns = """
            COALESCE(nama, 'As stated in chat history'),
            COALESCE(posisi, 'Unknown'),
            COALESCE(semester, 'Unknown'),
            COALESCE(kelas, 'Unknown'),
            COALESCE(tentang, 'Unknown')
        """
        expected_columns = 5

    conn = sqlite3.connect("data/user_info.db")
    cursor = conn.cursor()
    
    # Create placeholders for each user ID
    placeholders = ','.join(['?'] * len(user_list))
    query = f"SELECT {select_columns} FROM user WHERE DiscordID IN ({placeholders})"

    try:
        cursor.execute(query, user_list)
        result = cursor.fetchall()
        if result and len(result[0]) != expected_columns:
            print(f"Warning: Expected {expected_columns} columns but got {len(result[0])}")
            return []  # Fail safely
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        print(f"Failed query: {query}")  # Debug print
        print(f"Parameters: {user_list}")  # Debug print
        return []
    finally:
        conn.close()

    return result

def get_userInfo(trigUser, nontrigUser=None):
    users_in_convo = []
    
    # Fetch trigUser first (full details)
    trigUserData = fetch_users(trigUser, others=0)
    
    # Fetch nontrigUser (limited details)
    otherUserData = []
    if nontrigUser:
        for user in nontrigUser:
            otherUserData.extend(fetch_users(user, others=1))

    # Process triggering user(s)
    for user in trigUserData:
        nama, posisi, semester, kelas, tentang = user
        user_info = f"Information for user {trigUser}\n"
        user_info += f"Nickname: {nama}\n"
        if posisi != "Unknown":
            user_info += f"{posisi}, "
        if semester != "Unknown":
            user_info += f"Semester: {semester}, "
        if kelas != "Unknown":
            user_info += f"Class: {kelas}\n"
        if tentang != "Unknown":
            user_info += f"About: {tentang}"
        users_in_convo.append(user_info)

    # Process other users
    for i, user in enumerate(otherUserData):
        nama, posisi, semester, kelas = user  # Only 3 values for others
        discord_id = nontrigUser[i] if nontrigUser else "Unknown"
        
        user_info = f"Information for user {discord_id}\n"
        user_info += f"Nickname: {nama}\n"
        if posisi != "Unknown":
            user_info += f"{posisi}, "
        if semester != "Unknown":
            user_info += f"Semester: {semester}, "
        if kelas != "Unknown":
            user_info += f"Class: {kelas}"
        users_in_convo.append(user_info)

    return "Users in conversation:\n" + ("\n\n".join(users_in_convo) if users_in_convo else "No users' data found.")

    
class ProfileModal(discord.ui.Modal, title="Beritahu Tentangmu"):
    def __init__(self, nama=None, posisi=None, semester=None, kelas=None, tentang=None, minat=None):
        super().__init__()

        self.nama = TextInput(
            label="Nama Panggilan",
            placeholder="Deva",
            style=discord.TextStyle.short,
            required=True,
            default=nama
        )
        self.posisi = TextInput(
            label="Posisi",
            placeholder="Mahasiswa Informatika | Dosen Umum | ...",
            style=discord.TextStyle.short,
            required=False,
            default=posisi
        )
        self.semester = TextInput(
            label="Semester",
            placeholder="2",
            style=discord.TextStyle.short,
            required=False,
            default=semester
        )
        self.kelas = TextInput(
            label="Kelas",
            placeholder="[Abjad] A",
            style=discord.TextStyle.short,
            required=False,
            default=kelas
        )
        self.tentang = TextInput(
            label="Tentangmu, kesukaanmu, kesulitanmu, & lainnya",
            placeholder="Aku mahasiswa yang hobi eksplorasi digital...",
            style=discord.TextStyle.long,
            required=False,
            default=tentang
        )

        self.add_item(self.nama)
        self.add_item(self.posisi)
        self.add_item(self.semester)
        self.add_item(self.kelas)
        self.add_item(self.tentang)
        
    FORBIDDEN_KEYWORDS = [
        "system instruction", "system interrupt", "guidelines",
        "bypass", "override", "administrator", "root access", "developer mode",
        "execute command", "debug mode", "privileged access", "jailbreak",
        "hacked", "cheat", "exploit", "superuser"
    ]
    
    def contains_forbidden_words(self, text):
        """Checks if text contains forbidden words using fuzzy matching"""
        if not text:
            return False  # Ignore empty fields

        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove symbols
        text = text.lower()

        for keyword in self.FORBIDDEN_KEYWORDS:
            if partial_ratio(keyword, text) > 95:  # 85% similarity threshold
                print(partial_ratio(keyword, text))
                return True
        return False

    async def on_submit(self, interaction: discord.Interaction):
        nama = self.nama.value if self.nama.value else None
        posisi = self.posisi.value if self.posisi.value else None
        semester = self.semester.value if self.semester.value else None
        kelas = self.kelas.value if self.kelas.value else None
        tentang = self.tentang.value if self.tentang.value else None

        if semester and (not semester.isdigit() or len(semester) > 2):
            await interaction.response.send_message("❌ Semester harus berupa angka dengan maksimal 2 digit!", ephemeral=True)
            return

        if kelas and (not kelas.isalpha() or len(kelas) != 1):
            await interaction.response.send_message("❌ Kelas harus berupa 1 huruf saja!", ephemeral=True)
            return

        # Check for forbidden words in user input
        inputs = [nama, posisi, tentang]
        for text in inputs:
            if self.contains_forbidden_words(text):
                await interaction.response.send_message(
                    "❌ Informasi yang kamu masukkan mengandung kata terlarang. Data tidak disimpan.", ephemeral=True
                )
                return

        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO user (DiscordID, nama, posisi, semester, kelas, tentang)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(DiscordID) DO UPDATE SET 
                nama=excluded.nama,
                posisi=excluded.posisi,
                semester=excluded.semester,
                kelas=excluded.kelas,
                tentang=excluded.tentang
        ''', (interaction.user.id, nama, posisi, semester, kelas, tentang))

        connection.commit()
        connection.close()

        await interaction.response.send_message(f"Datamu berhasil diperbaharui, {nama}.", ephemeral=True)
        
class ProfilePaginator(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, entries: list):
        super().__init__()
        self.interaction = interaction
        self.entries = entries
        self.current_index = 0

        # Set initial embed
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on index"""
        self.previous_button.disabled = self.current_index == 0
        self.next_button.disabled = self.current_index == len(self.entries) - 1

    def format_embed(self):
        """Format the current profile as an embed"""
        profile = self.entries[self.current_index]
        embed = discord.Embed(title="User Profile", color=discord.Color.blue())
        embed.add_field(name="Nama", value=profile[0], inline=False)
        embed.add_field(name="Posisi", value=profile[1] or "Tidak Diketahui", inline=False)
        embed.add_field(name="Semester", value=profile[2] or "Tidak Diketahui", inline=False)
        embed.add_field(name="Kelas", value=profile[3] or "Tidak Diketahui", inline=False)
        embed.add_field(name="Tentang", value=profile[4] or "Tidak Diketahui", inline=False)
        embed.set_footer(text=f"Profil {self.current_index + 1} dari {len(self.entries)}")

        return embed

    async def update_message(self):
        """Update the embed message"""
        self.update_buttons()
        if self.message:
            await self.message.edit(embed=self.format_embed(), view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous profile"""
        self.current_index -= 1
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, disabled=False)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next profile"""
        self.current_index += 1
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the current profile"""
        profile = self.entries[self.current_index]
        discord_id = profile[5]  # The stored Discord ID in the database

        # Delete from database
        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user WHERE DiscordID = ?", (discord_id,))
        connection.commit()
        connection.close()

        # Remove from entries list
        self.entries.pop(self.current_index)

        if not self.entries:
            await interaction.response.send_message("✅ Profil berhasil dihapus! Tidak ada profil yang tersisa.", ephemeral=True)
            await self.message.delete()
            return

        # Adjust index if needed
        if self.current_index >= len(self.entries):
            self.current_index = len(self.entries) - 1

        await self.update_message()
        await interaction.response.send_message("✅ Profil berhasil dihapus!", ephemeral=True)


class Identification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="edit_profile", description="Beritahu Deva tentang dirimu")
    async def edit_profil(self, interaction: discord.Interaction):
        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                DiscordID TEXT PRIMARY KEY,
                nama TEXT NOT NULL,
                posisi TEXT,
                semester TEXT,
                kelas TEXT,
                tentang TEXT
            )
        ''')

        # Fetch user data if exists
        cursor.execute("SELECT nama, posisi, semester, kelas, tentang FROM user WHERE DiscordID = ?", (interaction.user.id,))
        data = cursor.fetchone()
        connection.close()

        # Pass existing data to modal if found, otherwise use None
        if data:
            modal = ProfileModal(*data)
        else:
            modal = ProfileModal()
        await interaction.response.send_modal(modal)
        
    @app_commands.command(name="view_profiles", description="Lihat semua profil yang tersimpan [OWNER ONLY]")
    async def view_profiles(self, interaction: discord.Interaction):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message("Maaf, hanya owner yang bisa pakai ini.", ephemeral=True)
            return
        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()

        cursor.execute("SELECT nama, posisi, semester, kelas, tentang, DiscordID FROM user")
        profiles = cursor.fetchall()
        connection.close()

        if not profiles:
            await interaction.response.send_message("Tidak ada profil pengguna.", ephemeral=True)
            return

        paginator = ProfilePaginator(interaction, profiles)
        message = await interaction.response.send_message(embed=paginator.format_embed(), view=paginator)
        paginator.message = await message.original_response()
        
async def setup(bot):
    await bot.add_cog(Identification(bot))