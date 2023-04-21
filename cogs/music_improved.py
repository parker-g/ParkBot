import discord


class MusicController(discord.Cog):
    def __init__(self, bot, playlist):
        self.bot = bot
        self.playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {"format": "bestaudio","noplaylist": "True",}
    
    def playNextSong(self):
        if len(self.playlist.q) > 0:
            self.playing = True
            url_ext = self.playlist.q[0][1] 
            audio = discord.FFmpegPCMAudio(url_ext, )
            self.voice.play()