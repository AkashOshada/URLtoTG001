import math, requests, os, time, datetime, aiohttp, asyncio, mimetypes, gdown, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.tgupload import upvideo, upaudio, upfile
from urllib.parse import quote_plus, unquote
from helpers.download_from_url import download_file, get_size
from helpers.file_handler import send_to_transfersh_async, progress
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from helpers.display_progress import progress_for_pyrogram, humanbytes
from helpers.tools import execute
from helpers.ffprobe import stream_creator
from helpers.thumbnail_video import thumb_creator
from helpers.youtube import ytdl

logger = logging.getLogger(__name__)
download_path = "Downloads/"

async def leecher2(bot , u):
    if not u.reply_to_message:
        await u.reply_text(text=f"Reply To Your Direct Link !", quote=True)
        return
    
    sw = "direct"
    m = u.reply_to_message
    
    if "|" in m.text:
        url , cfname = m.text.split("|", 1)
        url = url.strip()
        cfname = cfname.strip()
        cfname = cfname.replace('%40','@')
    else:
        url = m.text.strip()
        if os.path.splitext(url)[1]:
            cfname = unquote(os.path.basename(url))
        else:
            try:
                r = requests.get(url, allow_redirects=True, stream=True)
                if "Content-Disposition" in r.headers.keys():
                    cfname = r.headers.get("Content-Disposition")
                    cfname = cfname.split("filename=")[1]
                    if '\"' in cfname:
                        cfname = cfname.split("\"")[1]
                elif ("youtube.com" in url) or ("youtu.be" in url):
                    pass
                else:
                    await m.reply_text(text=f"I Could not Determine The FileType !\nPlease Use Custom Filename With Extension\n\nSee /help", quote=True)
                    return
            except RequestException as e:
                await m.reply_text(text=f"Error:\n\n{e}", quote=True)
                return
    
    msg = await m.reply_text(text=f"`Analyzing Your Link ...`", quote=True)
    
    if ("youtube.com" in url) or ("youtu.be" in url):
        await ytdl(bot, m, msg, url)
        return

    filename = os.path.join(download_path, cfname)
    filename = filename.replace('%25','_')
    filename = filename.replace(' ','_')
    filename = filename.replace('%40','@')
  
    start = time.time()
    try:
        file_path = await download_file(url, filename, msg, start, bot)
        print(f"file downloaded to {file_path} .")
    except Exception as e:
        if 'drive.google.com' in url:
            await msg.edit(f"Google Drive Link Detected !\n\n`Downloading ...`\n\n**Please Wait.**")
            sw = "gd"
        else:
            print(e)
            await msg.edit(f"Download Link is Invalid or not Accessible !\n\n**Error:** {e}")
            return
    
    if sw == "gd":
        file_path = os.path.join(download_path, cfname)
        if 'uc?id' in url:
            gdown.download(url, file_path, quiet=False)
        elif '/file/d/' in url:
            url2 = url.split("/file/d/", 1)[1]
            gid = url2.split("/", 1)[0]
            url = "https://drive.google.com/u/0/uc?id=" + str(gid) + "&export=download"
            gdown.download(url, file_path, quiet=False)
        else:
            await msg.edit(f"❌ Gdrive Link is Invalid ! \n\n **Error:** {e}")
            return
    await msg.edit(f"✅ **Successfully Downloaded**")
    filename = os.path.basename(file_path)
    filename = filename.replace('%40','@')
    filename = filename.replace('%25','_')
    filename = filename.replace(' ','_')
    size = os.path.getsize(file_path)
    size = get_size(size)
    audio_types = ['.aac', '.m4a', '.mp3', '.wma', '.mka', '.wav', '.oga', '.ogg', '.ra', '.flac', '.amr', '.opus', '.alac', '.aiff']
    mt = mimetypes.guess_type(str(cfname))[0]
    if mt and mt.startswith("video/"):
        uvstatus = await upvideo(bot, m, msg, file_path, cfname)
        if uvstatus:
            uvstatus = await upvideo(bot, m, msg, file_path, cfname)
            if uvstatus:
                fsw = "app"
            else:
                return
        else:
            return
    elif mt and mt.startswith("audio/"):
        uastatus = await upaudio(bot, m, msg, file_path, cfname)
        if uastatus:
            uastatus = await upaudio(bot, m, msg, file_path, cfname)
            if uastatus:
                fsw = "app"
            else:
                return
        else:
            return
    elif os.path.splitext(cfname)[1] in audio_types:
        uastatus = await upaudio(bot, m, msg, file_path, cfname)
        if uastatus:
            uastatus = await upaudio(bot, m, msg, file_path, cfname)
            if uastatus:
                fsw = "app"
            else:
                return
        else:
            return
    else:
        fsw = "app"
    
    if fsw == "app":
        await upfile(bot, m, msg, file_path, cfname)
        return
    
