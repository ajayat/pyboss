import asyncio

import discord
import youtube_dl
from discord.ext import commands

ytdl = youtube_dl.YoutubeDL()


class Video:
    def __init__(self, link):

        video = ytdl.extract_info(link, download=False)
        video_format = video["formats"][0]
        self.url = video["webpage_url"]
        self.stream_url = video_format["url"]


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.musics = {}

    @commands.command(name="play")
    async def play(self, ctx, url):
        """
        Joue une musique (lien requis)
        """
        voice_client = ctx.guild.voice_client

        if voice_client and voice_client.channel:
            video = Video(url)
            self.musics[ctx.guild].append(video)
        else:
            voice_channel = ctx.author.voice.channel
            video = Video(url)
            self.musics[ctx.guild] = []
            voice_client = await voice_channel.connect()
            self.play_song(voice_client, self.musics[ctx.guild], video)

    def play_song(self, voice_client, queue, song):
        """
        couroutine to play a song
        """
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                song.stream_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            )
        )

        def next(_):
            if len(queue) > 0:
                new_song = queue.pop(0)
                self.play_song(voice_client, queue, new_song)
            else:
                asyncio.run_coroutine_threadsafe(voice_client.disconnect, self.bot.loop)

        voice_client.play(source, after=next)

    @commands.command()
    async def skip(self, ctx):
        """
        Passer à la musique suivante, si disponible
        """
        voice_client = ctx.guild.voice_client
        try:
            voice_client.stop()
        except TypeError:
            pass
        else:
            embed = discord.Embed(
                title="",
                description=f"Morceau en cours: {self.musics[ctx.guild][0].url}",
                colour=0x54FA48,
            )
            embed.set_author(name=ctx.author.name)
            await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        voice_client = ctx.guild.voice_client
        if not voice_client.is_paused():
            voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()

    @commands.command()
    async def leave(self, ctx):
        """
        Arrêter la musique et la queue
        """
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
        self.musics[ctx.guild] = []


def setup(bot):
    bot.add_cog(Music(bot))
