import discord, sqlite3
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import TextInput
from .chat_manager import generate_agent_response
from .keyword_management import find_similar_entries, get_entries
from apikeys import NoctisLexiconRole as NL    
    
class ProfileModal(discord.ui.Modal, title="Input Knowledge Kondisi"):
    nama = TextInput(
        label="Nama Panggilan",
        placeholder="Deva",
        style=TextStyle.short,
        required=False        
    )
    posisi = TextInput(
        label="Posisi",
        placeholder="Mahasiswa Informatika | Dosen Umum | ...",
        style=TextStyle.short,
        required=False
    )
    semester = TextInput(
        label="Semester",
        placeholder="2",
        style=TextStyle.short,
        required=False
    )
    kelas = TextInput(
        label="Kelas",
        placeholder="[Abjad] A",
        style=TextStyle.short,
        required=False
    )
    tentang = TextInput(
        label="Tentangmu, kesukaanmu, kesulitanmu, dan lainnya",
        placeholder="Aku adalah mahasiswa semester 2 kelas A, pria, hobi eksplorasi digital...",
        style=TextStyle.long,
        required=False
    )
    minat = TextInput(
        label="Minat",
        placeholder='Software Dev | Game Developer | Network | Data Science',
        style=TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        nama = self.nama.value if self.nama.value else None
        posisi = self.posisi.value if self.posisi.value else None
        semester = self.semester.value if self.semester.value else None
        kelas = self.kelas.value if self.kelas.value else None
        tentang = self.tentang.value if self.tentang.value else None
        minat = self.tentang.value if self.tentang.value else None
        
        connection = sqlite3.connect('data/user_info.db')
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                DiscordID TEXT DEFAULT NULL,
                nama TEXT DEFAULT NULL,
                posisi TEXT DEFAULT NULL,
                semester TEXT DEFAULT NULL,
                kelas TEXT DEFAULT NULL,
                tentang TEXT DEFAULT NULL,
                minat TEXT DEFAULT NULL,
            )
        ''')
        cursor.execute("INSERT INTO user_identification (DiscordID, IGN, tentang, preferensi, mainJob) VALUES (?, ?, ?, ?, ?, ?, ?)", (interaction.user.id, nama, posisi, semester, kelas, tentang, minat))

        connection.commit()
        connection.close()

        await interaction.response.send_message(f"Datamu berhasil diperbaharui, {nama}.", ephemeral=True)

class Identification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="edit_profile", description="Beritahu Deva tentang dirimu")
    async def ubah_profil(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProfileModal())
        
async def setup(bot):
    await bot.add_cog(Identification(bot))