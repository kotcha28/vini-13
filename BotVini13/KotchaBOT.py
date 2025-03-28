import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

FFMPEG_PATH = "C:/ffmpeg/ffmpeg.exe"  # Ajuste para o caminho correto do ffmpeg

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="v!", intents=intents)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn'
}

ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
ytdl = YoutubeDL(ytdl_options)

# Variáveis globais
loop_enabled = False
current_url = None
queue = []  # Lista de músicas a serem tocadas


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")


async def play_next(ctx):
    """Toca a próxima música na fila, ou repete se o loop estiver ativado"""
    global current_url

    if loop_enabled and current_url:
        source = discord.FFmpegPCMAudio(current_url, executable=FFMPEG_PATH, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
    elif queue:
        next_song = queue.pop(0)
        current_url = next_song["url"]
        source = discord.FFmpegPCMAudio(current_url, executable=FFMPEG_PATH, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
        await ctx.send(f"🎵 Tocando agora: **{next_song['title']}**")
    else:
        current_url = None  # Se a fila estiver vazia, não há música tocando


@bot.command()
async def play(ctx, *, url):
    """Adiciona uma música à fila ou toca imediatamente se nenhuma estiver tocando"""
    global current_url

    if not ctx.voice_client:
        await ctx.invoke(join)

    try:
        with ytdl as ydl:
            info = ydl.extract_info(url, download=False)
            song_url = info.get('url')

            if not song_url:
                await ctx.send("❌ Erro ao obter o link do áudio.")
                return

            song = {"title": info['title'], "url": song_url}

            if ctx.voice_client.is_playing():
                queue.append(song)  # Adiciona à fila
                await ctx.send(f"📌 **{song['title']}** adicionada à fila!")
            else:
                current_url = song["url"]
                source = discord.FFmpegPCMAudio(current_url, executable=FFMPEG_PATH, **ffmpeg_options)
                ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
                await ctx.send(f"🎵 Tocando agora: **{song['title']}**")
    except Exception as e:
        await ctx.send(f"❌ Erro ao tentar reproduzir: {e}")
        print(f"Erro completo: {e}")


@bot.command()
async def skip(ctx):
    """Pula a música atual e toca a próxima da fila"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Pulando para a próxima música...")
    else:
        await ctx.send("❌ Não há música tocando no momento.")


@bot.command()
async def stop(ctx):
    """Para a música e limpa a fila"""
    global loop_enabled, current_url, queue

    if ctx.voice_client and ctx.voice_client.is_playing():
        loop_enabled = False
        current_url = None
        queue.clear()  # Limpa a fila
        ctx.voice_client.stop()
        await ctx.send("⏹ Música parada, loop desativado e fila limpa.")
    else:
        await ctx.send("❌ Não há música tocando no momento.")


@bot.command()
async def loop(ctx):
    """Ativa ou desativa o loop da música atual"""
    global loop_enabled
    loop_enabled = not loop_enabled
    status = "ativado" if loop_enabled else "desativado"
    await ctx.send(f"🔁 Loop {status}!")


@bot.command()
async def join(ctx):
    """Faz o bot entrar no canal de voz"""
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz para usar este comando.")
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)


@bot.command()
async def leave(ctx):
    """Desconecta o bot do canal de voz"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🔌 Bot desconectado do canal de voz.")
    else:
        await ctx.send("❌ Não estou em um canal de voz no momento.")


# Executar o bot
TOKEN = "aaaaa"  # Substitua pelo token do seu bot
bot.run(TOKEN)
