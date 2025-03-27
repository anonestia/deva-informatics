import discord, sqlite3
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import TextInput
import re
import rapidfuzz as fuzz

def contains_forbidden_words(self, text):
    """Checks if text contains forbidden words using fuzzy matching"""
    if not text:
        return False  # Ignore empty fields

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove symbols
    text = text.lower()

    for keyword in self.FORBIDDEN_KEYWORDS:
        if fuzz.partial_ratio(keyword, text) > 85:  # 85% similarity threshold
            return True
    return False
    
class ProfileModal(discord.ui.Modal, title="Beritahu Tentangmu"):
    def __init__(self, nama=None, posisi=None, semester=None, kelas=None, tentang=None, minat=None):
        super().__init__()

        self.nama = TextInput(
            label="Nama Panggilan",
            placeholder="Deva",
            style=discord.TextStyle.short,
            required=False,
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
            label="Tentangmu, kesukaanmu, kesulitanmu, dan lainnya",
            placeholder="Aku adalah mahasiswa semester 2 kelas A, pria, hobi eksplorasi digital...",
            style=discord.TextStyle.long,
            required=False,
            default=tentang
        )
        self.minat = TextInput(
            label="Minat",
            placeholder="Software Dev | Game Developer | Network | Data Science",
            style=discord.TextStyle.short,
            required=False,
            default=minat
        )

        self.add_item(self.nama)
        self.add_item(self.posisi)
        self.add_item(self.semester)
        self.add_item(self.kelas)
        self.add_item(self.tentang)
        self.add_item(self.minat)
        
    FORBIDDEN_KEYWORDS = [
        "system instruction", "system interrupt", "not deva", "guidelines",
        "bypass", "override", "administrator", "root access", "developer mode",
        "execute command", "debug mode", "privileged access", "jailbreak",
        "hacked", "cheat", "exploit", "superuser"
    ]

    async def on_submit(self, interaction: discord.Interaction):
        nama = self.nama.value if self.nama.value else None
        posisi = self.posisi.value if self.posisi.value else None
        semester = self.semester.value if self.semester.value else None
        kelas = self.kelas.value if self.kelas.value else None
        tentang = self.tentang.value if self.tentang.value else None
        minat = self.minat.value if self.minat.value else None

        # Check for forbidden words in user input
        inputs = [nama, posisi, semester, kelas, tentang, minat]
        for text in inputs:
            if self.contains_forbidden_words(text):
                await interaction.response.send_message(
                    "❌ Informasi yang kamu masukkan mengandung kata terlarang. Data tidak disimpan.", ephemeral=True
                )
                return

        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                DiscordID TEXT PRIMARY KEY,
                nama TEXT DEFAULT NULL,
                posisi TEXT DEFAULT NULL,
                semester TEXT DEFAULT NULL,
                kelas TEXT DEFAULT NULL,
                tentang TEXT DEFAULT NULL,
                minat TEXT DEFAULT NULL
            )
        ''')

        cursor.execute('''
            INSERT INTO user (DiscordID, nama, posisi, semester, kelas, tentang, minat)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(DiscordID) DO UPDATE SET 
                nama=excluded.nama,
                posisi=excluded.posisi,
                semester=excluded.semester,
                kelas=excluded.kelas,
                tentang=excluded.tentang,
                minat=excluded.minat
        ''', (interaction.user.id, nama, posisi, semester, kelas, tentang, minat))

        connection.commit()
        connection.close()

        await interaction.response.send_message(f"Datamu berhasil diperbaharui, {nama}.", ephemeral=True)


class Identification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="edit_profile", description="Beritahu Deva tentang dirimu")
    async def ubah_profil(self, interaction: discord.Interaction):
        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()

        # Fetch user data if exists
        cursor.execute("SELECT nama, posisi, semester, kelas, tentang, minat FROM user WHERE DiscordID = ?", (interaction.user.id,))
        data = cursor.fetchone()
        connection.close()

        # Pass existing data to modal if found, otherwise use None
        if data:
            modal = ProfileModal(*data)
        else:
            modal = ProfileModal()

        await interaction.response.send_modal(modal)
        
async def setup(bot):
    await bot.add_cog(Identification(bot))