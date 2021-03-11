import sys
sys.path.append("misc")
import common
globals().update(common.__dict__)


atypes = "wav mp3 ogg opus flac aac m4a webm wma f4a mka mp2 riff".split()
ftypes = [[f"*.{f}" for f in atypes + "mp4 mov qt mkv avi f4v flv wmv raw".split()]]
ftypes[0].append("All supported audio files")


# if 1 or not options.get("init"):
#     yn = easygui.indexbox(
#         "Assign Miza Player as the default application for audio?",
#         "Welcome!",
#         ("Yes", "No", "No and don't ask again")
#     )
#     if yn not in (None, "No"):
#         options.init = True
#     if yn == 0:
#         s = "\n".join(f"assoc .{f}=Miza-Player.{f}" for f in atypes)
#         if s:
#             s += "\n"
#         s += "\n".join(f'ftype Miza-Player.{f}="py" "{os.path.abspath("")}/{sys.argv[0]}" %%*' for f in atypes)
#         with open("assoc.bat", "w", encoding="utf-8") as f:
#             f.write(s)
#         print(ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd", "/k assoc.bat", None, 1))
        # subprocess.run(("runas", "/user:Administrator", "temp.bat"), stderr=subprocess.PIPE)

with open("assoc.bat", "w", encoding="utf-8") as f:
    f.write(f"cd {os.path.abspath('')}\nstart /MIN py {sys.argv[0]} %*")
if not os.path.exists("cache"):
    os.mkdir("cache")


player = cdict(
    paused=False,
    index=0,
    pos=0,
    end=inf,
    amp=0,
    stats=cdict(
        peak=0,
        amplitude=0,
        velocity=0,
        energy=0,
    )
)
sidebar = cdict(
    queue=alist(),
    entries=alist(),
    buttons=alist(),
    particles=alist(),
)
toolbar = cdict(
    pause=cdict(
        speed=0,
        angle=0,
        maxspeed=4,
    ),
    progress=cdict(
        vis=0,
        angle=0,
        spread=0,
        alpha=0,
        num=0,
        particles=alist(),
    ),
)
queue = sidebar.queue
entries = sidebar.entries
progress = toolbar.progress
modified = set()


def setup_buttons():
    try:
        gears = pygame.image.load("misc/gears.bmp").convert_alpha()
        sidebar.buttons.append(cdict(
            sprite=gears,
            click=lambda: sidebar.__setitem__("abspos", sidebar.get("abspos", 0) ^ 1),
        ))
        reset_menu(full=False)
        folder = pygame.image.load("misc/folder.bmp").convert_alpha()
        sidebar.buttons.append(cdict(
            sprite=folder,
            click=enqueue_local,
        ))
        reset_menu(full=False)
        hyperlink = pygame.image.load("misc/hyperlink.bmp").convert_alpha()
        sidebar.buttons.append(cdict(
            sprite=hyperlink,
            click=enqueue_search,
        ))
        reset_menu(full=False)
        microphone = pygame.image.load("misc/microphone.bmp").convert_alpha()
        globals()["pya"] = afut.result()
        sidebar.buttons.append(cdict(
            sprite=microphone,
            click=enqueue_device,
        ))
        reset_menu(full=False)
    except:
        print_exc()

def _enqueue_local(*files):
    try:
        if files:
            sidebar.loading = True
            for fn in files:
                if fn[0] == "<" and fn[-1] == ">":
                    pya = afut.result()
                    dev = pya.get_device_info_by_index(int(fn.strip("<>")))
                    entry = cdict(
                        url=fn,
                        stream=fn,
                        name=dev.get("name"),
                        duration=inf,
                    )
                else:
                    fn = fn.replace("\\", "/")
                    if "/" not in fn:
                        fn = "/" + fn
                    options.path, name = fn.rsplit("/", 1)
                    entry = cdict(
                        url=fn,
                        stream=fn,
                        name=name.rsplit(".", 1)[0],
                        duration=get_duration(fn),
                    )
                queue.append(entry)
            sidebar.loading = False
    except:
        sidebar.loading = False
        print_exc()

def enqueue_local():
    default = None
    if options.get("path"):
        default = options.path.rstrip("/") + "/"
    files = easygui.fileopenbox(
        "Open an audio or video file here!",
        "Miza Player",
        default=default,
        filetypes=ftypes,
        multiple=True,
    )
    if files:
        submit(_enqueue_local, *files)

def _enqueue_search(query):
    try:
        if query:
            sidebar.loading = True
            ytdl = downloader.result()
            entries = ytdl.search(query)
            queue.extend(cdict(e) for e in entries)
            sidebar.loading = False
    except:
        sidebar.loading = False
        print_exc()

def enqueue_search():
    query = easygui.enterbox(
        "Search for one or more songs online!",
        "Miza Player",
        "",
    )
    if query:
        submit(_enqueue_search, query)

def enqueue_device():
    globals()["pya"] = afut.result()
    count = pya.get_device_count()
    devices = alist()
    for i in range(count):
        d = cdict(pya.get_device_info_by_index(i))
        if d.maxInputChannels > 0 and d.get("hostAPI", 0) >= 0:
            try:
                if not pya.is_format_supported(
                    48000,
                    i,
                    2,
                    pyaudio.paInt16,
                ):
                    continue
                pya.open(
                    48000,
                    2,
                    pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=48000 >> 2,
                    input_device_index=i,
                    start=False,
                ).close()
            except:
                continue
            d.id = i
            devices.add(d)
    selected = easygui.choicebox(
        "Transfer audio from a sound input device!",
        "Miza Player",
        sorted(str(d.id) + ": " + d.name for d in devices),
    )
    if selected:
        submit(_enqueue_local, "<" + selected.split(":", 1)[0] + ">")

def enqueue_auto(*queries):
    for query in queries:
        q = query.strip()
        if q:
            if is_url(q) or not os.path.exists(q):
                submit(_enqueue_search, q)
            else:
                submit(_enqueue_local, q)


if len(sys.argv) > 1:
    submit(enqueue_auto, *sys.argv[1:])


def reset_menu(full=True, reset=False):
    if full:
        globals().update(options)
        common.__dict__.update(options)
        if reset:
            DISP.fill(0)
            modified.add(tuple(screensize))
    player.rect = (0, 0, screensize[0] - sidebar_width, screensize[1] - toolbar_height)
    sidebar.colour = None
    sidebar.updated = False
    sidebar.rect = (screensize[0] - sidebar_width, 0, sidebar_width, screensize[1] - toolbar_height)
    sidebar.rect2 = (screensize[0] - sidebar_width, 0, sidebar_width, screensize[1] - toolbar_height + 4)
    for i, button in enumerate(sidebar.buttons, -1):
        if i < 0:
            button.pos = (screensize[0] - 48, sidebar.rect[1] + 8)
        else:
            button.pos = (sidebar.rect[0] + 8 + 44 * i, sidebar.rect[1] + 8)
        button.rect = button.pos + (40, 40)
    sidebar.resizing = False
    sidebar.resizer = False
    toolbar.colour = None
    toolbar.updated = False
    toolbar.rect = (0, screensize[1] - toolbar_height, screensize[0], toolbar_height)
    toolbar.pause.radius = toolbar_height // 2 - 2
    toolbar.pause.pos = (toolbar.pause.radius + 2, screensize[1] - toolbar.pause.radius - 2)
    progress.pos = (round(toolbar.pause.pos[0] + toolbar.pause.radius * 1.5 + 4), screensize[1] - toolbar_height * 2 // 3 + 1)
    progress.box = toolbar_height * 3 // 2 + 8
    progress.length = max(0, screensize[0] - progress.pos[0] - toolbar.pause.radius // 2 - progress.box)
    progress.width = min(16, toolbar_height // 6)
    progress.rect = (progress.pos[0] - progress.width // 2 - 3, progress.pos[1] - progress.width // 2 - 3, progress.length + 6, progress.width + 6)
    progress.seeking = False
    toolbar.resizing = False
    toolbar.resizer = False
    osize = (progress.box, toolbar_height * 2 // 3 - 3)
    mixer.stdin.write(f"~osize {' '.join(map(str, osize))}\n".encode("utf-8"))
    mixer.stdin.flush()


submit(setup_buttons)


is_active = lambda: pc() - player.get("last", 0) <= max(player.get("lastframe", 0), 1 / 30) * 4

def prepare(entry, force=False):
    stream = entry.get("stream")
    if not stream or stream.startswith("ytsearch:") or force and (stream.startswith("https://cf-hls-media.sndcdn.com/") or stream.startswith("https://www.yt-download.org/download/") and int(stream.split("/download/", 1)[1].split("/", 3)[3]) < utc() + 60 or is_youtube_stream(stream) and int(stream.split("expire=", 1)[1].split("&", 1)[0]) < utc() + 60):
        ytdl = downloader.result()
        data = ytdl.search(entry.url)[0]
        entry.update(data)
    return entry.stream.strip()

def start_player(entry, pos=0, force=False):
    stream = prepare(entry, force=True)
    duration = entry.duration or get_duration(stream)
    entry.duration = duration
    if pos >= entry.duration:
        return skip()
    elif pos < 0:
        pos = 0
    mixer.stdin.write((stream + "\n" + str(pos) + " " + str(duration) + "\n").encode("utf-8"))
    mixer.stdin.flush()
    if force:
        mixer.state(0)
    player.pos = pos
    player.index = player.pos * 30
    player.end = duration
    return stream, duration

def start():
    mixer.clear()
    if queue:
        return enqueue(queue[0])
    player.last = 0
    player.pos = 0
    player.end = inf
    return None, inf

def skip():
    mixer.clear()
    if queue:
        sidebar.particles.append(queue.popleft())
        if queue:
            return enqueue(queue[0])
    player.last = 0
    player.pos = 0
    player.end = inf
    return None, inf

def seek_abs(pos):
    start_player(queue[0], pos, force=True) if queue else (None, inf)

def seek_rel(pos):
    if not pos:
        return
    if pos >= player.end:
        print("skipped")
        return skip()
    progress.num += pos
    progress.alpha = 255
    if pos > 0 and pos <= 180:
        mixer.drop(pos)
    else:
        seek_abs(max(0, player.pos + pos))

def play():
    try:
        while True:
            osize = list(map(int, mixer.stderr.readline().split()))
            req = np.prod(osize) * 3
            b = mixer.stderr.read(req)
            while len(b) < req:
                if not mixer.is_running():
                    raise StopIteration
                b += mixer.stderr.read(req - len(b))
            osci = pygame.image.frombuffer(b, osize, "RGB")
            osci.set_colorkey((0,) * 3)
            player.osci = osci
    except:
        if not mixer.is_running():
            print(mixer.stderr.read().decode("utf-8", "replace"))
        print_exc()

def pos():
    try:
        while True:
            s = None
            while not s and mixer.is_running():
                s = mixer.stdout.readline().decode("utf-8", "replace").rstrip()
                if s and s[0] != "~":
                    if s[0] in "'\"":
                        s = ast.literal_eval(s)
                    print(s, end="")
                    s = ""
            if not s:
                if not mixer.is_running():
                    raise StopIteration
                continue
            player.last = pc()
            s = s[1:]
            if s == "s":
                skip()
                player.last = 0
                continue
            if s[0] == "x":
                spl = s[2:].split()
                player.stats.peak = spl[0]
                player.stats.amplitude = spl[1]
                player.stats.velocity = spl[2]
                player.stats.energy = spl[3]
                player.amp = float(spl[4])
                continue
            i, dur = map(float, s.split(" ", 1))
            if not progress.seeking:
                player.index = i
                player.pos = round(player.index / 30, 4)
            if dur >= 0:
                player.end = dur
    except:
        if not mixer.is_running():
            print(mixer.stderr.read().decode("utf-8", "replace"))
        print_exc()

submit(play)
submit(pos)

def stop(pause=True):
    try:
        player.paused = pause
        mixer.state(player.paused)
    except:
        pass

def enqueue(entry, start=True):
    try:
        if len(queue) > 1:
            submit(prepare, queue[1])
        stream, duration = start_player(entry)
        progress.num = 0
        progress.alpha = 0
        return stream, duration
    except:
        print_exc()


def update_menu():
    ts = toolbar.pause.setdefault("timestamp", 0)
    t = pc()
    player.lastframe = duration = max(0.001, min(t - ts, 0.125))
    toolbar.pause.timestamp = pc()
    ratio = 1 / (duration * 8)
    progress.vis = (progress.vis * (ratio - 1) + player.pos) / ratio
    progress.alpha *= 0.998 ** (duration * 480)
    if progress.alpha < 16:
        progress.alpha = progress.num = 0
    progress.angle = -t * pi
    if progress.seeking:
        player.amp = 0.5
    elif not is_active():
        player.amp = 0
    progress.spread = min(1, (progress.spread * (ratio - 1) + player.amp) / ratio)
    toolbar.pause.angle = (toolbar.pause.angle + (toolbar.pause.speed + 1) * duration * 2) % tau
    toolbar.pause.speed *= 0.995 ** (duration * 480)
    for i, entry in enumerate(queue):
        entry.pos = (entry.get("pos", 0) * (ratio - 1) + i) / ratio
    if kspam[K_SPACE]:
        player.paused ^= True
        mixer.state(player.paused)
        toolbar.pause.speed = toolbar.pause.maxspeed
    if toolbar.resizing:
        toolbar_height = min(96, max(48, screensize[1] - mpos2[1] + 2))
        if options.toolbar_height != toolbar_height:
            options.toolbar_height = toolbar_height
            reset_menu()
            toolbar.resizing = True
            modified.add(toolbar.rect)
    if progress.seeking:
        orig = player.pos
        if player.end < inf:
            player.pos = max(0, min(1, (mpos2[0] - progress.pos[0] + progress.width // 2) / progress.length) * player.end)
            progress.num += (player.pos - orig)
        progress.alpha = 255
        player.index = player.pos * 30
        if not mheld[0]:
            progress.seeking = False
            if queue and isfinite(queue[0].duration):
                seek_abs(player.pos)
    if sidebar.resizing:
        sidebar_width = min(512, max(144, screensize[0] - mpos2[0] + 2))
        if options.sidebar_width != sidebar_width:
            options.sidebar_width = sidebar_width
            reset_menu()
            sidebar.resizing = True
            modified.add(sidebar.rect)
    if queue and isfinite(queue[0].duration):
        if kspam[K_PAGEUP]:
            seek_rel(300)
        elif kspam[K_PAGEDOWN]:
            seek_rel(-300)
        elif kspam[K_UP]:
            seek_rel(30)
        elif kspam[K_DOWN]:
            seek_rel(-30)
        elif kspam[K_RIGHT]:
            seek_rel(5)
        elif kspam[K_LEFT]:
            seek_rel(-5)
    if in_rect(mpos, toolbar.rect[:3] + (5,)):
        if mclick[0]:
            toolbar.resizing = True
        else:
            toolbar.resizer = True
    if in_circ(mpos, toolbar.pause.pos, max(4, toolbar.pause.radius - 2)):
        if mclick[0]:
            player.paused ^= True
            mixer.state(player.paused)
            toolbar.pause.speed = toolbar.pause.maxspeed
        toolbar.pause.outer = 255
        toolbar.pause.inner = 191
        toolbar.updated = False
        sidebar.updated = False
    else:
        toolbar.pause.outer = 191
        toolbar.pause.inner = 127
    if in_rect(mpos, progress.rect):
        if mclick[0]:
            progress.seeking = True
            if queue and isfinite(queue[0].duration):
                mixer.clear()
    if toolbar.resizing or in_rect(mpos, toolbar.rect):
        c = (64, 32, 96)
    else:
        c = (64, 0, 96)
    toolbar.updated = toolbar.colour != c
    toolbar.colour = c
    if mclick[0]:
        for button in sidebar.buttons:
            if in_rect(mpos, button.rect):
                button.flash = 32
                button.click()
    else:
        for button in sidebar.buttons:
            if "flash" in button:
                button.flash = max(0, button.flash - duration * 64)
    if in_rect(mpos, sidebar.rect[:2] + (5, sidebar.rect[3])):
        if not toolbar.resizing and mclick[0]:
            sidebar.resizing = True
        else:
            sidebar.resizer = True
    if sidebar.resizing or in_rect(mpos, sidebar.rect):
        c = (64, 32, 96)
    else:
        c = (64, 0, 96)
    sidebar.updated = sidebar.colour != c
    sidebar.colour = c
    sidebar.relpos = min(1, (sidebar.get("relpos", 0) * (ratio - 1) + sidebar.get("abspos", 0)) / ratio)

def draw_menu():
    ts = toolbar.progress.setdefault("timestamp", 0)
    t = pc()
    dur = max(0.001, min(t - ts, 0.125))
    if not tick & 7:
        toolbar.progress.timestamp = pc()
    if (sidebar.updated or not tick & 7 or in_rect(mpos2, sidebar.rect) and (any(mclick) or any(kclick))) and sidebar.colour:
        modified.add(sidebar.rect)
        offs = round(sidebar.setdefault("relpos", 0) * -sidebar_width)
        if queue and offs > -sidebar_width + 4:
            DISP2 = pygame.Surface(sidebar.rect2[2:])
            DISP2.fill(sidebar.colour)
            if (kheld[K_LCTRL] or kheld[K_RCTRL]) and kclick[K_v]:
                enqueue_auto(*pyperclip.paste().splitlines())
            if in_rect(mpos, sidebar.rect) and mclick[0] or not mheld[0]:
                sidebar.pop("dragging", None)
            if sidebar.get("last_selected") and not any(entry.get("selected") for entry in queue):
                sidebar.pop("last_selected")
            copies = deque()
            pops = set()
            try:
                if not sidebar.last_selected.selected:
                    raise ValueError
                lq = queue.index(sidebar.last_selected)
            except (AttributeError, ValueError, IndexError):
                sidebar.pop("last_selected", None)
                lq = nan
            swap = None
            maxitems = int(screensize[1] - toolbar_height - 20 >> 5)
            etarget = round((mpos[1] - 68) / 32) if in_rect(mpos, (screensize[0] - sidebar_width + 8, 52, sidebar_width - 16, screensize[1] - toolbar_height - 52)) else nan
            target = min(max(0, round((mpos[1] - 68) / 32)), len(queue) - 1)
            if in_rect(mpos, sidebar.rect) and mclick[0] and not kheld[K_LSHIFT] and not kheld[K_RSHIFT]:
                if etarget not in range(len(queue)):
                    for entry in queue:
                        entry.pop("selected", None)
                        sidebar.pop("last_selected", None)
            if mclick[0] and etarget in range(len(queue)) and in_rect(mpos, sidebar.rect):
                if queue[etarget].get("selected"):
                    sidebar.last_selected = queue[etarget]
            for i, entry in enumerate(queue):
                if entry.get("selected"):
                    if kclick[K_DELETE] or kclick[K_BACKSPACE] or (kheld[K_LCTRL] or kheld[K_RCTRL]) and kclick[K_x]:
                        pops.add(i)
                        if sidebar.get("last_selected") == entry:
                            sidebar.pop("last_selected", None)
                    if (kheld[K_LCTRL] or kheld[K_RCTRL]) and (kclick[K_c] or kclick[K_x]):
                        entry.flash = 16
                        copies.append(entry.url)
                elif (kheld[K_LCTRL] or kheld[K_RCTRL]) and kclick[K_a]:
                    entry.selected = True
                    sidebar.last_selected = queue[-1]
                if i >= maxitems:
                    entry.pop("flash", None)
                    continue
                x = 8 + offs
                if entry.get("selected") and sidebar.get("dragging"):
                    y = round(52 + entry.get("pos", 0) * 32)
                    rect = (x, y, sidebar_width - 16, 32)
                    sat = 0.875
                    val = 1
                    secondary = True
                    entry.colour = col = [round(x * 255) for x in colorsys.hsv_to_rgb(i / 12, sat, val)]
                    bevel_rectangle(
                        DISP2,
                        col,
                        rect,
                        4,
                        alpha=round(255 / (1 + abs(entry.get("pos", 0) - i) / 4)),
                        filled=False,
                    )
                    y = mpos2[1] - 16
                    if not swap and not mclick[0] and not kheld[K_LSHIFT] and not kheld[K_RSHIFT] and sidebar.get("last_selected") is entry:
                        target = min(max(0, round((mpos[1] - 68) / 32)), len(queue) - 1)
                        if target != i:
                            swap = target - i
                else:
                    y = round(52 + entry.get("pos", 0) * 32)
                rect = (x, y, sidebar_width - 16, 32)
                t = 255
                selectable = in_rect((mpos[0] + sidebar_width - screensize[0], mpos[1]), rect)
                if not selectable and sidebar.get("last_selected") and (kheld[K_LSHIFT] or kheld[K_RSHIFT]):
                    b = lq
                    if b >= 0:
                        a = target
                        a, b = sorted((a, b))
                        if a <= i <= b:
                            selectable = True
                if selectable or entry.get("selected"):
                    if mclick[0] and selectable:
                        entry.selected = True
                        sidebar.dragging = True
                    sat = 0.875
                    val = 1
                    secondary = True
                else:
                    sat = 1
                    val = 0.875
                    secondary = False
                if entry.get("flash"):
                    if entry.flash < 0:
                        entry.pop("flash", None)
                    else:
                        sat = max(0, sat - entry.flash / 16)
                        val = min(1, val + entry.flash / 16)
                    entry.flash -= 1
                entry.colour = col = [round(x * 255) for x in colorsys.hsv_to_rgb(i / 12, sat, val)]
                bevel_rectangle(
                    DISP2,
                    col,
                    rect,
                    4,
                    alpha=255 if secondary else round(255 / (1 + abs(entry.get("pos", 0) - i) / 4)),
                    filled=not secondary,
                )
                if secondary:
                    sat = 0.875
                    val = 0.4375
                    if entry.get("flash"):
                        sat = max(0, sat - entry.flash / 16)
                        val = min(1, val + entry.flash / 16)
                    pygame.draw.rect(
                        DISP2,
                        [round(x * 255) for x in colorsys.hsv_to_rgb(i / 12, sat, val)],
                        [rect[0] + 4, rect[1] + 4, rect[2] - 8, rect[3] - 8],
                    )
                if not entry.get("surf"):
                    entry.surf = message_display(
                        "".join(c if ord(c) < 65536 else "\x7f" for c in entry.name[:128]),
                        12,
                        (0,) * 2,
                        align=0,
                    )
                if not t:
                    blit_complex(
                        DISP2,
                        entry.surf,
                        (x + 6, y + 4),
                        area=(0, 0, sidebar_width - 32, 24),
                        colour=(t,) * 3,
                    )
                else:
                    DISP2.blit(
                        entry.surf,
                        (x + 6, y + 4),
                        (0, 0, sidebar_width - 32, 24),
                    )
                message_display(
                    time_disp(entry.duration or inf),
                    10,
                    [x + sidebar_width - 20, y + 28],
                    (t,) * 3,
                    surface=DISP2,
                    align=2,
                )
            if copies:
                pyperclip.copy("\n".join(copies))
            sidebar.particles.extend(queue[i] for i in pops)
            skipping = 0 in pops
            if skipping:
                pops.discard(0)
            queue.pops(pops)
            if skipping:
                submit(skip)
            for i, entry in enumerate(queue):
                if i >= maxitems:
                    break
                if not entry.get("selected"):
                    continue
                x = 8 + offs
                if sidebar.get("dragging"):
                    # x = mpos2[0] - sidebar_width // 2 + 8
                    y = mpos2[1] - 16
                else:
                    y = round(52 + entry.get("pos", 0) * 32)
                rect = (x, y, sidebar_width - 16, 32)
                anima_rectangle(
                    DISP2,
                    [round(x * 255) for x in colorsys.hsv_to_rgb(i / 12 + 1 / 12, 0.9375, 1)],
                    [rect[0] + 1, rect[1] + 1, rect[2] - 3, rect[3] - 3],
                    frame=4,
                    count=2,
                    flash=1,
                    ratio=pc() * 0.4,
                    reduction=0.1,
                )
            if sidebar.get("loading"):
                x = 8 + offs
                y = round(52 + len(queue) * 32)
                rect = (x, y, sidebar_width - 16, 32)
                bevel_rectangle(
                    DISP2,
                    (191,) * 3,
                    rect,
                    4,
                    alpha=255,
                )
                anima_rectangle(
                    DISP2,
                    (255,) * 3,
                    [rect[0] + 1, rect[1] + 1, rect[2] - 3, rect[3] - 3],
                    frame=4,
                    count=2,
                    flash=1,
                    ratio=pc() * 0.4,
                    reduction=0.1,
                )
                if not sidebar.get("loading_text"):
                    sidebar.loading_text = message_display(
                        "Loading...",
                        12,
                        [0] * 2,
                        align=0,
                    )
                DISP2.blit(
                    sidebar.loading_text,
                    (x + 6, y + 4),
                    (0, 0, sidebar_width - 32, 24),
                )
            if swap:
                # moved = queue[0].get("selected")
                dest = deque()
                targets = {}
                for i, entry in enumerate(queue):
                    if i + swap < 0 or i + swap >= len(queue):
                        continue
                    if entry.get("selected"):
                        targets[i + swap] = entry
                        entry.moved = True
                i = 0
                for entry in queue:
                    j = 0
                    if i in targets:
                        dest.append(targets[i])
                        j = 1
                    if not entry.get("moved"):
                        dest.append(entry)
                        j = 1
                    else:
                        entry.pop("moved", None)
                    i += j
                queue[:] = dest
                if 0 in targets:
                    mixer.clear()
                    submit(start_player, queue[0])
            DISP.blit(
                DISP2,
                (screensize[0] - sidebar_width, 0),
            )
        bevel_rectangle(
            DISP,
            sidebar.colour,
            sidebar.rect2,
            4,
            filled=not queue or offs <= -sidebar_width + 4
        )
        if offs <= -4:
            offs2 = offs + sidebar_width
            for i, opt in enumerate(asettings):
                message_display(
                    opt.capitalize(),
                    11,
                    (screensize[0] + offs + 8, 52 + i * 32),
                    surface=DISP,
                    align=0,
                )
        maxb = (sidebar_width - 12) // 44
        for button in sidebar.buttons[:maxb]:
            if button.get("rect"):
                lum = 223 if in_rect(mpos, button.rect) else 191
                lum += button.get("flash", 0)
                bevel_rectangle(
                    DISP,
                    (lum,) * 3,
                    button.rect,
                    4,
                )
                DISP.blit(
                    button.sprite,
                    (button.rect[0] + 5, button.rect[1] + 5),
                )
        if offs > -sidebar_width + 4:
            pops = set()
            for i, entry in enumerate(sidebar.particles):
                if entry.get("life") is None:
                    entry.life = 1
                else:
                    entry.life -= dur
                    if entry.life <= 0:
                        pops.add(i)
                col = [round(i * entry.life) for i in entry.get("colour", (223, 0, 0))]
                y = round(52 + entry.get("pos", 0) * 32)
                ext = round(32 - 32 * entry.life)
                rect = (screensize[0] - sidebar_width + 8 - ext + offs, y - ext * 3, sidebar_width - 16 + ext * 2, 32 + ext * 2)
                bevel_rectangle(
                    DISP,
                    col,
                    rect,
                    4,
                    alpha=round(255 * entry.life),
                )
            sidebar.particles.pops(pops)
        else:
            sidebar.particles.clear()
    highlighted = progress.seeking or in_rect(mpos, progress.rect)
    if (toolbar.updated or not tick & 7) and toolbar.colour:
        bevel_rectangle(
            DISP,
            toolbar.colour,
            toolbar.rect,
            4,
        )
        modified.add(toolbar.rect)
        pos = progress.pos
        length = progress.length
        width = progress.width
        ratio = player.pos / player.end
        if highlighted:
            bevel_rectangle(
                DISP,
                (255, 0, 127),
                progress.rect,
                3,
                filled=False,
            )
        xv = round(length * progress.vis / player.end) if not progress.seeking or player.end < inf else mpos2[0] - pos[0] + width // 2
        xv = max(0, min(xv, length))
        xv2 = max(0, xv - 4)
        if highlighted:
            c = (48, 0, 72)
        else:
            c = (32, 0, 48)
        bevel_rectangle(
            DISP,
            c,
            (xv2 + pos[0] - width // 2, pos[1] - width // 2, length - xv2, width),
            min(4, width >> 1),
        )
        if progress.vis or not player.end < inf:
            if highlighted:
                c = (223, 159, 255)
            else:
                c = (191, 127, 255)
            bevel_rectangle(
                DISP,
                c,
                (pos[0] - width // 2, pos[1] - width // 2, xv, width),
                min(4, width >> 1),
            )
        pos = toolbar.pause.pos
        radius = toolbar.pause.radius
        spl = max(4, radius >> 2)
        lum = round(toolbar.pause.speed / toolbar.pause.maxspeed * toolbar.pause.outer)
        if player.paused:
            c = (toolbar.pause.outer, lum, lum)
        elif is_active():
            c = (lum, toolbar.pause.outer, lum)
        else:
            c = (toolbar.pause.outer, toolbar.pause.outer, lum)
        reg_polygon_complex(
            DISP,
            pos,
            c,
            6,
            radius,
            radius,
            thickness=2,
            repetition=spl,
            angle=toolbar.pause.angle,
        )
        if player.paused:
            c = (toolbar.pause.inner, 0, 0)
        elif is_active():
            c = (lum, toolbar.pause.inner, lum)
        else:
            c = (toolbar.pause.inner, toolbar.pause.inner, lum)
        reg_polygon_complex(
            DISP,
            pos,
            c,
            6,
            radius - spl,
            radius - spl,
            thickness=2,
            repetition=radius - spl,
            angle=toolbar.pause.angle,
        )
        modified.add(toolbar.rect)
        lum = toolbar.pause.outer + 224 >> 1
        rad = max(4, radius // 2)
        col = (lum,) * 3
        if player.paused:
            w = 4
            for i in range(w):
                r = rad + w - i
                x = (w - i) / 2
                x1 = pos[0] - r * (2 - sqrt(3)) // 2
                A = (x1 + r, pos[1])
                B = (x1 - r // 2, pos[1] - r * sqrt(3) // 2)
                C = (x1 - r // 2, pos[1] + r * sqrt(3) // 2)
                c1 = (min(255, (lum + 64) // x),) * 3
                c2 = (min(255, (lum + 256) // x),) * 3
                c3 = (max(0, (lum - 128) // x),) * 3
                pygame.draw.aaline(DISP, c1, A, B)
                pygame.draw.aaline(DISP, c2, B, C)
                pygame.draw.aaline(DISP, c3, A, C)
            x2 = pos[0] - rad * (2 - sqrt(3)) // 2
            pts = (
                (x2 + rad, pos[1]),
                (x2 - rad // 2, pos[1] - rad * sqrt(3) // 2),
                (x2 - rad // 2, pos[1] + rad * sqrt(3) // 2),
            )
            pygame.draw.polygon(DISP, col, pts)
        else:
            bevel_rectangle(
                DISP,
                col,
                (pos[0] - rad, pos[1] - rad, rad * 4 // 5, rad << 1),
                3,
            )
            bevel_rectangle(
                DISP,
                col,
                (pos[0] + (rad + 3) // 5, pos[1] - rad, rad * 4 // 5, rad << 1),
                3,
            )
        if is_active() and player.get("osci"):
            rect = (screensize[0] - 8 - progress.box, screensize[1] - toolbar_height, progress.box, toolbar_height * 2 // 3 - 3)
            surf = player.osci
            if tuple(rect[2:]) != surf.get_size():
                player.osci = surf = pygame.transform.scale(surf, rect[2:])
            DISP.blit(
                surf,
                rect[:2],
            )
        else:
            y = screensize[1] - toolbar_height * 2 // 3 - 2
            pygame.draw.line(
                DISP,
                (255, 0, 0),
                (screensize[0] - 8 - progress.box, y),
                (screensize[0] - 8, y)
            )
        s = f"{time_disp(player.pos)}/{time_disp(player.end)}"
        message_display(
            s,
            min(24, toolbar_height // 3),
            (screensize[0] - 4, screensize[1] - 2),
            surface=DISP,
            align=2,
        )
        x = progress.pos[0] + int(progress.length * progress.vis / player.end) - width // 2 if not progress.seeking or player.end < inf else mpos2[0]
        x = min(progress.pos[0] - width // 2 + progress.length, max(progress.pos[0] - width // 2, x))
        r = ceil(progress.spread * toolbar_height) >> 1
        if r:
            concentric_circle(
                DISP,
                (127, 127, 255),
                (x, progress.pos[1]),
                r,
                fill_ratio=0.5,
            )
        pops = set()
        for i, p in enumerate(progress.particles):
            ri = round(p.life)
            p.hsv[0] = (p.hsv[0] + dur / 12) % 1
            p.hsv[1] = max(p.hsv[0] - dur / 12, 1)
            col = [round(i * 255) for i in colorsys.hsv_to_rgb(*p.hsv)]
            a = round(min(255, (p.life - 2) * 20))
            point = [cos(p.angle) * p.rad, sin(p.angle) * p.rad]
            pos = (p.centre[0] + point[0], p.centre[1] + point[1])
            reg_polygon_complex(
                DISP,
                pos,
                col,
                0,
                ri,
                ri,
                alpha=a,
                thickness=2,
                repetition=ri - 2,
                soft=True,
            )
            p.life -= dur * 2.5
            if p.life <= 6:
                p.angle += dur
                p.rad = max(0, p.rad - 16 * dur)
            if p.life < 3:
                pops.add(i)
        progress.particles.pops(pops)
        for i in shuffle(range(3)):
            hsv = [0.5, 1, 1]
            col = [round(i * 255) for i in colorsys.hsv_to_rgb(*hsv)]
            a = progress.angle + i / 3 * tau
            point = [cos(a) * r, sin(a) * r]
            p = (x + point[0], progress.pos[1] + point[1])
            if r and not tick & 7:
                progress.particles.append(cdict(
                    centre=(x, progress.pos[1]),
                    angle=a,
                    rad=r,
                    life=7,
                    hsv=hsv,
                ))
            ri = max(8, progress.width // 2 + 2)
            reg_polygon_complex(
                DISP,
                p,
                col,
                0,
                ri,
                ri,
                alpha=127 if r else 255,
                thickness=2,
                repetition=ri - 2,
                soft=True,
            )
        a = int(progress.alpha)
        if a >= 16:
            n = round(progress.num)
            if n >= 0:
                s = "+" + str(n)
                c = (0, 255, 0)
            else:
                s = str(n)
                c = (255, 0, 0)
            message_display(
                s,
                min(20, toolbar_height // 3),
                (x, progress.pos[1] - 16),
                c,
                surface=DISP,
                alpha=a,
            )
    if not tick & 7 or toolbar.rect in modified:
        if toolbar.resizing:
            pygame.draw.rect(DISP, (255, 0, 0), toolbar.rect[:3] + (4,))
            if not mheld[0]:
                toolbar.resizing = False
        elif toolbar.resizer:
            pygame.draw.rect(DISP, (191, 127, 255), toolbar.rect[:3] + (4,))
            toolbar.resizer = False
    if not tick & 7 or sidebar.rect in modified:
        if sidebar.resizing:
            pygame.draw.rect(DISP, (255, 0, 0), sidebar.rect[:2] + (4, sidebar.rect[3]))
            if not mheld[0]:
                sidebar.resizing = False
        elif sidebar.resizer:
            pygame.draw.rect(DISP, (191, 127, 255), sidebar.rect[:2] + (4, sidebar.rect[3]))
            sidebar.resizer = False
    if not tick & 7 or toolbar.rect in modified:
        if highlighted:
            pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 13, mpos2[1] - 1), (mpos2[0] + 11, mpos2[1] - 1), width=2)
            pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 1, mpos2[1] - 13), (mpos2[0] - 1, mpos2[1] + 11), width=2)
            pygame.draw.circle(DISP, (255, 0, 0), mpos2, 9, width=2)
            p = max(0, min(1, (mpos2[0] - progress.pos[0] + progress.width // 2) / progress.length) * player.end)
            s = time_disp(p)
            message_display(
                s,
                min(20, toolbar_height // 3),
                (mpos2[0], mpos2[1] - 16),
                (255, 255, 127),
                surface=DISP,
            )


K_a = 4
K_c = 6
K_v = 25
K_x = 120
K_SPACE = 44
K_DELETE = 76
reset_menu(True)
foc = True
minimised = False
mpos = mpos2 = (-inf,) * 2
mheld = mclick = mrelease = mprev = (None,) * 5
kheld = pygame.key.get_pressed()
kprev = kclick = KeyList((None,)) * len(kheld)
last_tick = 0
try:
    for tick in itertools.count(0):
        lpos = mpos
        mprev = mheld
        mheld = get_pressed()
        foc = get_focused()
        if foc:
            minimised = False
        else:
            minimised = is_minimised()
        if not minimised:
            mclick = [x and not y for x, y in zip(mheld, mprev)]
            mrelease = [not x and y for x, y in zip(mheld, mprev)]
            mpos2 = mouse_rel_pos()
            mpos3 = pygame.mouse.get_pos()
            if foc:
                mpos = mpos3
            else:
                mpos = (nan,) * 2
            kprev = kheld
            kheld = KeyList(x + y if y else 0 for x, y in zip(kheld, pygame.key.get_pressed()))
            kclick = KeyList(x and not y for x, y in zip(kheld, kprev))
            kspam = kclick
            # if any(kspam):
            #     print(" ".join(map(str, (i for i, v in enumerate(kspam) if v))), K_a)
            if not tick & 15:
                kspam = KeyList(x or y >= 240 for x, y in zip(kclick, kheld))
            if not tick & 3 or mpos != lpos or (mpos2 != lpos and any(mheld)) or any(mclick) or any(kclick) or any(mrelease) or any(isnan(x) != isnan(y) for x, y in zip(mpos, lpos)):
                try:
                    # print(mpos, mpos3, mpos2, foc, common.rel, mheld)
                    update_menu()
                except:
                    print_exc()
                draw_menu()
            if not player.get("fut"):
                if queue:
                    player.fut = submit(start)
            elif not queue:
                player.pop("fut").result()
            if not queue:
                player.pos = 0
                player.end = inf
                player.last = 0
                progress.num = 0
                progress.alpha = 0
            # if not tick + 4 & 15:
            #     buffer = player.get("buffer")
            #     if buffer is not None:
            #         player.task = submit(update_render, buffer)
            if not tick + 12 & 15 or tuple(screensize) in modified:
                # if player.get("task"):
                #     data = player.task.result()
                #     if data:
                #         DISP.blit(data.surf, (0, 0))
                for i, k in enumerate(("peak", "amplitude", "velocity", "energy")):
                    v = player.stats.get(k, 0) if is_active() else 0
                    message_display(
                        f"{k.capitalize()}: {v}%",
                        13,
                        (2, 14 * i),
                        align=0,
                        surface=DISP,
                    )
                if modified:
                    modified.add(tuple(screensize))
                else:
                    modified.add(player.rect)
            if modified:
                if tuple(screensize) in modified:
                    pygame.display.flip()
                else:
                    pygame.display.update(tuple(modified))
                if not tick + 12 & 15 and (tuple(screensize) in modified or player.rect in modified):
                    DISP.fill(
                        (0,) * 3,
                        player.rect,
                    )
                modified.clear()
        delay = max(0, last_tick - pc() + 1 / 480)
        last_tick = pc()
        time.sleep(delay)
        for event in pygame.event.get():
            if event.type == QUIT:
                raise StopIteration
            elif event.type == VIDEORESIZE:
                flags = get_window_flags()
                if flags == 3:
                    options.maximised = True
                else:
                    options.pop("maximised", None)
                    screensize2[:] = event.w, event.h
                screensize[:] = event.w, event.h
                DISP = pygame.display.set_mode(screensize, RESIZABLE)
                reset_menu(reset=True)
                mpos = (-inf,) * 2
            elif event.type == VIDEOEXPOSE:
                rect = get_window_rect()
                if screenpos2 != rect[:2]:
                    options.screenpos = rect[:2]
                    screenpos2 = None
        pygame.event.clear()
except Exception as ex:
    pygame.quit()
    if type(ex) is not StopIteration:
        print_exc()
    options.screensize = screensize2
    if options != orig_options:
        with open(config, "w", encoding="utf-8") as f:
            json.dump(dict(options), f, indent=4)
    if mixer.is_running():
        mixer.clear()
        time.sleep(0.1)
        try:
            mixer.kill()
        except:
            pass
    PROC = psutil.Process()
    for c in PROC.children(recursive=True):
        try:
            c.kill()
        except:
            pass
    futs = set()
    for fn in os.listdir("cache"):
        if fn[0] in "~\x7f" and fn.endswith(".pcm"):
            futs.add(submit(os.remove, "cache/" + fn))
    for fut in futs:
        try:
            fut.result()
        except:
            pass
    PROC.kill()