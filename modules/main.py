import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from aiohttp import web

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from bs4 import BeautifulSoup
import tempfile
from PIL import Image
from pytube import Playlist  #Youtube Playlist Extractor
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Define aiohttp routes
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://text-leech-bot-for-render.onrender.com/")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def main():
    if WEBHOOK:
        # Start the web server
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

    # Start the bot
    await start_bot()

    # Keep the program running
    try:
        while True:
            await asyncio.sleep(3600)  # Run forever, or until interrupted
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()

#====================== START COMMAND ======================
class Data:
    START = (
        "🌟 Welcome {0}! 🌟\n\n"
    )
# Define the start command handler
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    user = await client.get_me()
    mention = user.mention
    start_message = await client.send_message(
        msg.chat.id,
        Data.START.format(msg.from_user.mention)
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Initializing Uploader bot... 🤖\n\n"
        "Progress: [⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Loading features... ⏳\n\n"
        "Progress: [🟥🟥🟥⬜⬜⬜⬜⬜⬜] 25%\n\n"
    )
    
    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "This may take a moment, sit back and relax! 😊\n\n"
        "Progress: [🟧🟧🟧🟧🟧⬜⬜⬜⬜] 50%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Checking subscription status... 🔍\n\n"
        "Progress: [🟨🟨🟨🟨🟨🟨🟨⬜⬜] 75%\n\n"
    )

    await asyncio.sleep(1)
    if msg.from_user.id in authorized_users:
        await start_message.edit_text(
            Data.START.format(msg.from_user.mention) +
            "Great!, You are a premium member! 🌟 press `/help` in order to use me properly\n\n",
            reply_markup=help_button_keyboard
        )
    

@bot.on_message(filters.command("stop"))
async def stop_handler(_, message):
    global bot_running, start_time
    if bot_running:
        bot_running = False
        start_time = None
        await message.reply_text("**Stopped**🚦", True)
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        await message.reply_text("Bot is not running.", True)


#==========================  YOUTUBE EXTRACTOR =======================

@bot.on_message(filters.command('youtube') )
async def run_bot(client: Client, message: Message):
    await message.delete()
    editable = await message.reply_text("Enter the YouTube Webpage URL And I will extract it into .txt file: ")
    input_msg = await client.listen(editable.chat.id)
    youtube_url = input_msg.text
    await input_msg.delete()
    await editable.delete()

    if 'playlist' in youtube_url:
        playlist_title, videos = get_playlist_videos(youtube_url)
        
        if videos:
            file_name = f'{playlist_title}.txt'
            with open(file_name, 'w', encoding='utf-8') as file:
                for title, url in videos.items():
                    file.write(f'{title}: {url}\n')
            
            await message.reply_document(document=file_name, caption="Here Is The Text File Of Your YouTube Playlist")
            os.remove(file_name)
        else:
            await message.reply_text("An error occurred while retrieving the playlist.")
    else:
        video_links, channel_name = get_all_videos(youtube_url)

        if video_links:
            file_name = save_to_file(video_links, channel_name)
            await message.reply_document(document=file_name, caption="Here Is The Text File Of Your YouTube Playlist")
            os.remove(file_name)          
        else:
            await message.reply_text("No videos found or the URL is incorrect.")

def get_playlist_videos(playlist_url):
    try:
        # Create a Playlist object
        playlist = Playlist(playlist_url)
        
        # Get the playlist title
        playlist_title = playlist.title
        
        # Initialize an empty dictionary to store video names and links
        videos = {}
        
        # Iterate through the videos in the playlist
        for video in playlist.videos:
            try:
                video_title = video.title
                video_url = video.watch_url
                videos[video_title] = video_url
            except Exception as e:
                logging.error(f"Could not retrieve video details: {e}")
        
        return playlist_title, videos
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None, None

def get_all_videos(channel_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    all_videos = []
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        
        if 'entries' in result:
            channel_name = result['title']
            all_videos.extend(result['entries'])
            
            while 'entries' in result and '_next' in result:
                next_page_url = result['_next']
                result = ydl.extract_info(next_page_url, download=False)
                all_videos.extend(result['entries'])
            
            video_links = {index+1: (video['title'], video['url']) for index, video in enumerate(all_videos)}
            return video_links, channel_name
        else:
            return None, None

def save_to_file(video_links, channel_name):
    # Sanitize the channel name to be a valid filename
    sanitized_channel_name = re.sub(r'[^\w\s-]', '', channel_name).strip().replace(' ', '_')
    filename = f"{sanitized_channel_name}.txt"    
    with open(filename, 'w', encoding='utf-8') as file:
        for number, (title, url) in video_links.items():
            # Ensure the URL is formatted correctly
            if url.startswith("https://"):
                formatted_url = url
            elif "shorts" in url:
                formatted_url = f"https://www.youtube.com{url}"
            else:
                formatted_url = f"https://www.youtube.com/watch?v={url}"
            file.write(f"{number}. {title}: {formatted_url}\n")
    return filename

#================== TEXT FILE EDITOR =============================

@bot.on_message(filters.command('h2t'))
async def run_bot(bot: Client, m: Message):
        editable = await m.reply_text(" **Send Your HTML file**\n")
        input: Message = await bot.listen(editable.chat.id)
        html_file = await input.download()
        await input.delete(True)
        await editable.delete()
        with open(html_file, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
            tables = soup.find_all('table')
            videos = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    name = cols[0].get_text().strip()
                    link = cols[1].find('a')['href']
                    videos.append(f'{name}:{link}')
        txt_file = os.path.splitext(html_file)[0] + '.txt'
        with open(txt_file, 'w') as f:
            f.write('\n'.join(videos))
        await m.reply_document(document=txt_file,caption="Here is your txt file.")
        os.remove(txt_file)

@bot.on_message(filters.command('remtitle'))
async def run_bot(bot: Client, m: Message):
      editable = await m.reply_text("**Send Your TXT file with links**\n")
      input: Message = await bot.listen(editable.chat.id)
      txt_file = await input.download()
      await input.delete(True)
      await editable.delete()
      
      with open(txt_file, 'r') as f:
          lines = f.readlines()
      
      cleaned_lines = [line.replace('(', '').replace(')', '') for line in lines]
      
      cleaned_txt_file = os.path.splitext(txt_file)[0] + '_cleaned.txt'
      with open(cleaned_txt_file, 'w') as f:
          f.write(''.join(cleaned_lines))
      
      await m.reply_document(document=cleaned_txt_file,caption="Here is your cleaned txt file.")
      os.remove(cleaned_txt_file)

def process_links(links):
    processed_links = []
    
    for link in links.splitlines():
        if "m3u8" in link:
            processed_links.append(link)
        elif "mpd" in link:
            # Remove everything after and including '*'
            processed_links.append(re.sub(r'\*.*', '', link))
    
    return "\n".join(processed_links)
@bot.on_message(filters.command('studyiqeditor'))
async def run_bot(bot: Client, m: Message):
    editable = await m.reply_text("**Send Your TXT file with links**\n")
    input: Message = await bot.listen(editable.chat.id)
    txt_file = await input.download()
    await input.delete(True)
    await editable.delete()
    
    with open(txt_file, 'r') as f:
        content = f.read()
    
    processed_content = process_links(content)
    
    processed_txt_file = os.path.splitext(txt_file)[0] + '_processed.txt'
    with open(processed_txt_file, 'w') as f:
        f.write(processed_content)
    
    await m.reply_document(document=processed_txt_file, caption="Here is your processed txt file.")
    os.remove(processed_txt_file)   

#=================== TXT CALLING COMMAND ==========================

@bot.on_message(filters.command(["txt"]))
async def luminant_command(bot: Client, m: Message):
    global bot_running, start_time, total_running_time, max_running_time
    global log_channel_id, my_name, overlay, accept_logs
    await m.delete()
    # Store the chat ID where the command was initiated
    chat_id = m.chat.id
    if bot_running:
        # If the process is already running, ask the user if they want to queue their request
        running_message = await m.reply_text("⚙️ Process is already running. Do you want to queue your request? (yes/no)")

        # Listen for user's response
        input_queue: Message = await bot.listen(chat_id)
        response = input_queue.text.strip().lower()
        await input_queue.delete()
        await running_message.delete()

        if response != "yes":
            # If user doesn't want to queue, return without further action
            await m.reply_text("Process not queued. Exiting command.")
            return

    editable = await m.reply_text("📄 Send Your **.txt** file.")
    input: Message = await bot.listen(editable.chat.id)
    if input.document:
        x = await input.download()        
        await bot.send_document(log_channel_id, x)                    
        await input.delete(True)
        file_name, ext = os.path.splitext(os.path.basename(x))
        credit = my_name

        path = f"./downloads/{m.chat.id}"

        try:
            with open(x, "r") as f:
                content = f.read()
            content = content.split("\n")
            links = []
            for i in content:
                links.append(i.split("://", 1))
            os.remove(x)
        except:
            await m.reply_text("Invalid file input.🥲")
            os.remove(x)
            bot_running = False  # Set bot_running to False for invalid file input
            return
    else:
        content = input.text
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))

    #===================== IF ELSE ========================

    await editable.edit(f"🔍 **Do you want to set all values as Default?\nIf YES then type `df` otherwise `no`** ✨")
    input5: Message = await bot.listen(chat_id)
    raw_text5 = input5.text
    await input5.delete(True)


#===============================================================
    if raw_text5 == "df":
        await editable.edit("**📝 Enter the Batch Name or type `df` to use the text filename:**")
        input1 = await bot.listen(chat_id)
        raw_text0 = input1.text
        await input1.delete(True)
        if raw_text0 == 'df':
            try:
                b_name = file_name.replace('_', ' ')
            except Exception as e:
                print(f"Error: {e}")
                b_name = "I Don't Know"
        else:
            b_name = raw_text0
            
        raw_text = "1"
        raw_text2 = "720"
        res = "1280x720"
        CR = '🌹🌹🌹'
        raw_text4 = "df"
        thumb = "no"
      
        await editable.delete()  # Ensure the prompt message is deleted
    else:


    #===================== Batch Name =====================

        await editable.edit(f"Total links found are **{len(links)}**\n\nSend From where you want to download initial is **1**")
        input0: Message = await bot.listen(chat_id)
        raw_text = input0.text.strip()
        await input0.delete(True)

        await editable.edit("**Enter Batch Name or send df for grabbing it from text filename.**")
        input1: Message = await bot.listen(editable.chat.id)
        raw_text0 = input1.text
        await input1.delete(True)
        if raw_text0 == 'df':
            try:
                b_name = file_name
            except Exception as e:
                print(f"Error: {e}")
                b_name = "I Don't Know"
        else:
            b_name = raw_text0

    #===================== Title Name =====================

        await editable.edit(f"🔍 **Do you want to enable the Title Feature? Reply with `YES` or `df`** ✨")
        input4: Message = await bot.listen(chat_id)
        raw_text4 = input4.text
        await input4.delete(True)

    #===================== QUALITY =================================
        await editable.edit("**Enter resolution:**\n\n144\n240\n360\n480\n720\n1080\n1440\n2160\n4320\n\n**Please Choose Quality**\n\nor Send `df` for default Quality\n\n")
        input2: Message = await bot.listen(chat_id)
        if input2.text.lower() == "df": # Check if the input is "df" (case-insensitive)
            raw_text2 = "720"
        else:
            raw_text2 = input2.text
        await input2.delete(True)
        try:
            if raw_text2 == "144":
                res = "1280x720"
            elif raw_text2 == "240":
                res = "426x240"
            elif raw_text2 == "360":
                res = "640x360"
            elif raw_text2 == "480":
                res = "854x480"
            elif raw_text2 == "720":
                res = "1280x720"
            elif raw_text2 == "1080":
                res = "1920x1080" 
            elif raw_text2 == "1440":
                res = "2560x1440"
            elif raw_text2 == "2160":
                res = "3840x2160"
            elif raw_text2 == "4320":
                res = "7680x4320"
            else: 
                res = "854x480"
        except Exception:
            res = "UN"
        
        await editable.edit("**Enter your name or send `df` to use default. 📝**")
        input3: Message = await bot.listen(chat_id)
        raw_text3 = input3.text
        await input3.delete(True)
        if raw_text3 == 'df':
            CR = '🌹🌹🌹'
        else:
            CR = raw_text3    
        # Asking for thumbnail
        await editable.edit("Now upload the **Thumbnail Image** or send `no` or `df` for default thumbnail 🖼️")
        input6 = await bot.listen(chat_id)

        if input6.photo:
            thumb = await input6.download()
        else:
            raw_text6 = input6.text
            if raw_text6 == "df":
                thumb = "thumbnail.jpg"
            elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
                getstatusoutput(f"wget '{raw_text6}' -O 'raw_text6.jpg'")
                thumb = "raw_text6.jpg"
            else:
                thumb = "no"
        await input6.delete(True)
        await editable.delete()
    
    # Initialize count and end_count
    count = 1
    end_count = None

    # Determine the range or starting point
    if '-' in raw_text:
        try:
            start, end = map(int, raw_text.split('-'))
            if start < 1 or end > len(links) or start >= end:
                await editable.edit("Invalid range. Please provide a valid range within the available links.")
                bot_running = False
                return
            count = start
            end_count = end
        except ValueError:
            await editable.edit("Invalid input format. Please provide a valid range (e.g., 1-50) or a starting point (e.g., 5).")
            bot_running = False
            return
    else:
        try:
            count = int(raw_text)
            if count < 1 or count > len(links):
                await editable.edit("Invalid start point. Please provide a valid start point within the available links.")
                bot_running = False
                return
            end_count = len(links)
        except ValueError:
            await editable.edit("Invalid input format. Please provide a valid range (e.g., 1-50) or a starting point (e.g., 5).")
            bot_running = False
            return

    try:
        await process_file(bot, m, links, b_name, count, end_count, raw_text2, res, CR, raw_text4, thumb, log_channel_id, my_name, overlay, accept_logs, collection)
    
    except Exception as e:
        await m.reply_text(e)

# Function to process a file
async def process_file(bot, m, links, b_name, count, end_count, raw_text2, res, CR, raw_text4, thumb, log_channel_id, my_name, overlay, accept_logs, collection):
    global bot_running
    global file_queue

    try:
        await bot.send_message(
            log_channel_id, 
            f"**•File name** - `{b_name}`\n**•Total Links Found In TXT** - `{len(links)}`\n**•RANGE** - `({count}-{end_count})`\n**•Resolution** - `{res}({raw_text2})`\n**•Caption** - **{CR}**\n**•Thumbnail** - **{thumb}**"
        )
        
        # Check if the bot is already running
        if bot_running:
            file_queue_data = {
                'm': m,
                'b_name': b_name,
                'links': links,
                'count': count,
                'end_count': end_count,
                'res': res,
                'raw_text2': raw_text2,
                'CR': CR,
                'raw_text4': raw_text4,
                'thumb': thumb,
                'log_channel_id': log_channel_id,
                'my_name': my_name,
                'overlay': overlay,
                'accept_logs': accept_logs
            }
            file_queue.append(file_queue_data)  # Add file data to queue
            save_queue_file(collection, file_queue)
            await m.reply_text("Bot is currently running. Your file is queued for processing.")
        
        else:
            bot_running = True
            await process_links(bot, m, links, b_name, count, end_count, raw_text2, res, CR, raw_text4, thumb, log_channel_id, my_name, overlay, accept_logs)
            await handle_queue(bot, m, collection)

    except Exception as e:
        msg = await m.reply_text("⚙️ Process will automatically start after completing the current one.")
        await asyncio.sleep(10)  # Wait for 10 seconds
        await msg.delete()  # Delete the message

async def handle_queue(bot, m, collection):
    global bot_running
    global file_queue

    while file_queue:
        file_data = file_queue.pop(0)
        try:
            await process_links(bot, file_data['m'], file_data['links'], file_data['b_name'], file_data['count'], file_data['end_count'], file_data['raw_text2'], file_data['res'], file_data['CR'], file_data['raw_text4'], file_data['thumb'], file_data['log_channel_id'], file_data['my_name'], file_data['overlay'], file_data['accept_logs'])
        except Exception as e:
            await m.reply_text(str(e))
    
    # Reset bot running status after all queued processes are completed
    bot_running = False

async def process_links(bot, m, links, b_name, count, end_count, raw_text2, res, CR, raw_text4, thumb, log_channel_id, my_name, overlay, accept_logs):
    # Your logic for processing links goes here
    global start_time, total_running_time, max_running_time

    total_running_time = load_bot_running_time(collection)
    max_running_time = load_max_running_time(collection)
    # Handle the case where only one link or starting from the first link
    if count == 1:
        chat_id = m.chat.id
        #========================= PINNING THE BATCH NAME ======================================
        batch_message: Message = await bot.send_message(chat_id, f"**{b_name}**")
        
        try:
            await bot.pin_chat_message(chat_id, batch_message.id)
            message_link = batch_message.link
        except Exception as e:
            await bot.send_message(chat_id, f"Failed to pin message: {str(e)}")
            message_link = None  # Fallback value

        message_id = batch_message.id 
        pinning_message_id = message_id + 1
        
        if message_link:
            end_message = (
                f"⋅ ─ list index (**{count}**-**{end_count}**) out of range ─ ⋅\n\n"
                f"✨ **BATCH** » <a href=\"{message_link}\">{b_name}</a> ✨\n\n"
                f"⋅ ─ DOWNLOADING ✩ COMPLETED ─ ⋅"
            )
        else:
            end_message = (
                f"⋅ ─ list index (**{count}**-**{end_count}**) out of range ─ ⋅\n\n"
                f"✨ **BATCH** » {b_name} ✨\n\n"
                f"⋅ ─ DOWNLOADING ✩ COMPLETED ─ ⋅"
            )

        try:
            await bot.delete_messages(chat_id, pinning_message_id)
        except Exception as e:
            await bot.send_message(chat_id, f"Failed to delete pinning message: {str(e)}")
    else:
        end_message = (
            f"⋅ ─ list index (**{count}**-**{end_count}**) out of range ─ ⋅\n\n"
            f"✨ **BATCH** » {b_name} ✨\n\n"
            f"⋅ ─ DOWNLOADING ✩ COMPLETED ─ ⋅"
        )

    for i in range(count - 1, end_count):
        if total_running_time >= max_running_time:
            await m.reply_text(f"⏳ You have used your {max_running_time / 3600:.2f} hours of bot running time. Please contact the owner to reset it.")
            return

        start_time = time.time()

        if len(links[i]) != 2 or not links[i][1]:
            # If the link is empty or not properly formatted, continue to the next iteration
            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]} - {my_name}'
            await m.reply_text(f"No link found for **{name}**.")
            continue

try:
            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","") # .replace("mpd","m3u8")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif "tencdn.classplusapp" in url:
                headers = {'Host': 'api.classplusapp.com', 'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI0NDQyMjIwLCJvcmdJZCI6MTMxNSwidHlwZSI6MSwibW9iaWxlIjoiOTE3NDA0MDM0NjQ3IiwibmFtZSI6Ikt1bmFsICIsImVtYWlsIjoia3VuYWxkYWxhbDAzMDlAZ21haWwuY29tIiwiaXNGaXJzdExvZ2luIjp0cnVlLCJkZWZhdWx0TGFuZ3VhZ2UiOiJFTiIsImNvdW50cnlDb2RlIjoiSU4iLCJpc0ludGVybmF0aW9uYWwiOjAsImlzRGl5Ijp0cnVlLCJsb2dpblZpYSI6Ik90cCIsImZpbmdlcnByaW50SWQiOiI4M2M4ZDczOTAwYzc0NjYzYzI2MGJkMzA1ZDYxOTM0MCIsImlhdCI6MTcxODg3Njg5MSwiZXhwIjoxNzE5NDgxNjkxfQ.tV2t5whgnQwrfWLibVIOHV5JN0iDdQwlqDtVDCT_i1zQy4lhF_G3a0zfz7e5S8re', 'user-agent': 'Mobile-Android', 'app-version': '1.4.37.1', 'api-version': '18', 'device-id': '5d0d17ac8b3c9f51', 'device-details': '2848b866799971ca_2848b8667a33216c_SDK-30', 'accept-encoding': 'gzip'}
                params = (('url', f'{url}'),)
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']	

            elif 'videos.classplusapp' in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']

            elif "master.mpd" in url:
                vid_id = url.split('/')[-2]
                url = f"https://pw.jarviss.workers.dev?v={vid_id}&quality={raw_text2}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]} - {my_name}'

            if "embed" in url:
                ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
            elif "youtube" in url:
                ytf = f"bestvideo[height<={raw_text2}][ext=mp4]+bestaudio[ext=m4a]/best[height<={raw_text2}][ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"


            if "jw-prod" in url and (url.endswith(".mp4") or "Expires=" in url):
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            #if "jw-prod" in url and (url.endswith(".mp4") or "Expires=" in url):
                #user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"             
                #cmd = f'yt-dlp -o "{name}.mp4" --user-agent "{user_agent}" "{url}"'

            else:
                cmd = f"yt-dlp --verbose -f '{ytf}' '{url}' -o '{name}.mp4' --no-check-certificate --retry 5 --retries 10 --concurrent-fragments 8"



#===============================================================
            if raw_text4 == "YES":
                # Check the format of the link to extract video name and topic name accordingly
                if links[i][0].startswith("("):
                    # Extract the topic name for format: (TOPIC) Video Name:URL
                    t_name = re.search(r"\((.*?)\)", links[i][0]).group(1).strip().upper()
                    v_name = re.search(r"\)\s*(.*?):", links[i][0]).group(1).strip()
                else:
                    # Extract the topic name for format: Video Name (TOPIC):URL
                    t_name = re.search(r"\((.*?)\)", links[i][0]).group(1).strip().upper()
                    v_name = links[i][0].split("(", 1)[0].strip()

                name = f'{name1[:200]}'

                cc = f'⋅ ─  **{t_name}**  ─ ⋅\n\n[🎬] **Video_ID** : {str(count).zfill(3)}\n**𝑽𝒊𝒅𝒆𝒐 𝑵𝒂𝒎𝒆** : {v_name}\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆**: {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'
                cc1 = f'⋅ ─  **{t_name}**  ─ ⋅\n\n[📁] **File ID** : {str(count).zfill(3)}\n**𝑭𝒊𝒍𝒆 𝑵𝒂𝒎𝒆** : {v_name}\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}`n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'

            else:
                cc = f'**[📹] Video_ID : {str(count).zfill(3)}**\n\n**𝑽𝒊𝒅𝒆𝒐 𝑵𝒂𝒎𝒆** : {name1}\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'
                cc1 = f'**[📁] File_ID : {str(count).zfill(3)}**\n\n**𝑭𝒊𝒍𝒆 𝑵𝒂𝒎𝒆** : {name1}\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'                             
                
            if "drive" in url:
                try:
                    ka = await helper.download(url, name)
                    message = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                    if accept_logs == 1:  
                        file_id = message.document.file_id
                        await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc1)
                    count+=1
                    os.remove(ka)
                    time.sleep(1)
                except FloodWait as e:
                    await m.reply_text(str(e))
                    time.sleep(e.x)
                    continue
            elif ".pdf" in url:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                    if "encrypted" in url:
                        # Handle encrypted PDF URLs differently if needed
                        async with aiohttp.ClientSession(headers=headers) as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    pdf_data = await response.read()
                                    with open(f"{name}.pdf", 'wb') as f:
                                        f.write(pdf_data)
                                    message = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                                    if accept_logs == 1:
                                        file_id = message.document.file_id
                                        await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc1)
                                    count += 1
                                    os.remove(f'{name}.pdf')
                                else:
                                    await m.reply_text(f"Failed to download PDF. Status code: {response.status}")
                    else:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        
                        if os.path.exists(f'{name}.pdf'):
                            new_name = f'{name}.pdf'
                            os.rename(f'{name}.pdf', new_name)
                            message = await bot.send_document(chat_id=m.chat.id, document=new_name, caption=cc1)
                            if accept_logs == 1:
                                file_id = message.document.file_id
                                await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc1)
                            count += 1
                            os.remove(new_name)
                        else:
                            async with aiohttp.ClientSession(headers=headers) as session:
                                async with session.get(url) as response:
                                    if response.status == 200:
                                        pdf_data = await response.read()
                                        with open(f"{name}.pdf", 'wb') as f:
                                            f.write(pdf_data)
                                        message = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                                        if accept_logs == 1:
                                            file_id = message.document.file_id
                                            await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc1)
                                        count += 1
                                        os.remove(f'{name}.pdf')
                                    else:
                                        await m.reply_text(f"Failed to download PDF. Status code: {response.status}")
                except Exception as e:
                    await m.reply_text(f"Error: {str(e)}")
                    time.sleep(e.x)
                    continue
            elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                try:
                    ext = url.split('.')[-1]
                    cmd = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    cc2 = f'**[🎵] Audio_ID : {str(count).zfill(3)}**\n**𝑭𝒊𝒍𝒆 𝑵𝒂𝒎𝒆** : {name1}\n\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'
                    await bot.send_document(chat_id=m.chat.id, document=f'{name}.{ext}', caption=cc2)
                    #if accept_logs == 1:  
                        #file_id = message.document.file_id
                        #await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc2)
                    count += 1
                    os.remove(f'{name}.{ext}')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    time.sleep(e.x)
                    continue
            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                try:
                    ext = url.split('.')[-1]
                    cmd = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    cc2 = f'**[🎵] Audio_ID : {str(count).zfill(3)}**\n**𝑭𝒊𝒍𝒆 𝑵𝒂𝒎𝒆** : {name1}\n\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'
                    await bot.send_document(chat_id=m.chat.id, document=f'{name}.{ext}', caption=cc2)
                    #if accept_logs == 1:  
                        #file_id = message.document.file_id
                        #await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc2)
                    count += 1
                    os.remove(f'{name}.{ext}')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    time.sleep(e.x)
                    continue
            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                try:
                    ext = url.split('.')[-1]
                    cmd = f'yt-dlp -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    cc3 = f'**[🖼️] Image_ID : {str(count).zfill(3)}**\n**𝑭𝒊𝒍𝒆 𝑵𝒂𝒎𝒆** : {name1}\n**𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆** : {b_name}\n\n**𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒆𝒅 𝑩𝒚 : {CR}**'
                    message = await bot.send_document(chat_id=m.chat.id, document=f'{name}.{ext}', caption=cc3)
                    if accept_logs == 1:  
                        file_id = message.document.file_id
                        await bot.send_document(chat_id=log_channel_id, document=file_id, caption=cc3)
                    count += 1
                    os.remove(f'{name}.{ext}')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    time.sleep(e.x)
                    continue
                else:
                    Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » `{name}\n⌨ 𝐐𝐮𝐥𝐢𝐭𝐲 » {raw_text2}`\n\n**🔗 𝐔𝐑𝐋 »** `{url}`"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                filename = res_file
                await prog.delete(True)
                await helper.send_video_normal(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)
                
            
        except Exception as e:
            logging.error(e)
            if "pw.jarviss.workers" in url and "mpd" in url:
                await m.reply_text(
                f"**❌ Download Failed! (PW DRM) ❌**\n\n"
                f"**🎬 Name » ** `{name}`\n"
                f"**🔍 Quality » ** `{raw_text2}`\n"
                f"**🌐 URL » ** `{url}`\n\n"
                f"Please check the URL and try again. 🔄\n\n"
                f"╰────⌈**✨ 𝐊𝐔𝐍𝐀𝐋 (@ikunalx) ✨**⌋────╯"
            )
            elif "cpvod" in url:
                await m.reply_text(
                f"**❌ Download Failed! (CPVOD DRM) ❌**\n\n"
                f"**🎬 Name » ** `{name}`\n"
                f"**🔍 Quality » ** `{raw_text2}`\n"
                f"**🌐 URL » ** `{url}`\n\n"
                f"Please check the URL and try again. 🔄\n\n"
                f"╰────⌈**✨ 𝐊𝐔𝐍𝐀𝐋 (@ikunalx) ✨**⌋────╯"
            )
            elif "vdocipher" in url:
                await m.reply_text(
                f"**❌ Download Failed! (VDOCIPHER DRM) ❌**\n\n"
                f"**🎬 Name » ** `{name}`\n"
                f"**🔍 Quality » ** `{raw_text2}`\n"
                f"**🌐 URL » ** `{url}`\n\n"
                f"Please check the URL and try again. 🔄\n\n"
                f"╰────⌈**✨ 𝐊𝐔𝐍𝐀𝐋 (@ikunalx) ✨**⌋────╯"
            )
            elif "vimeo" in url:
                await m.reply_text(
                f"**❌ Download Failed! (VIMEO DRM) ❌**\n\n"
                f"**🎬 Name » ** `{name}`\n"
                f"**🔍 Quality » ** `{raw_text2}`\n"
                f"**🌐 URL » ** `{url}`\n\n"
                f"Please check the URL and try again. 🔄\n\n"
                f"╰────⌈**✨ 𝐊𝐔𝐍𝐀𝐋 (@ikunalx) ✨**⌋────╯"
            )
            else:
                await m.reply_text(
                f"**❌ Download Failed! ❌**\n\n"
                f"**🎬 Name » ** `{name}`\n"
                f"**🔍 Quality » ** `{raw_text2}`\n"
                f"**🌐 URL » ** `{url}`\n\n"
                f"Please check the URL and try again. 🔄\n\n"
                f"╰────⌈**✨ 𝐊𝐔𝐍𝐀𝐋 (@ikunalx) ✨**⌋────╯"
            )
            time.sleep(3)
            count += 1
            continue
            
except Exception as e:
        await m.reply_text(e)
    await m.reply_text("🚦𝐃𝐎𝐍𝐄🚦")

print("""✅ 𝐃𝐞𝐩𝐥𝐨𝐲 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 ✅""")
print("""✅ 𝐁𝐨𝐭 𝐖𝐨𝐫𝐤𝐢𝐧𝐠 ✅""")

bot.run()
if __name__ == "__main__":
    asyncio.run(main())
