editor = player.editor
note_names = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)
def note_colour(i, s=1, v=1):
    return verify_colour(x * 255 for x in colorsys.hsv_to_rgb(i / 12, s, v))
PW = 48
piano_particles = []

def spawn_particle(p=None, **kwargs):
    p = p or kwargs
    if type(p) is not cdict:
        p = cdict(p)
    if len(piano_particles) >= 1024:
        i = random.randint(0, len(piano_particles) - 1)
        piano_particles[i] = p
    else:
        try:
            i = piano_particles.index(None)
        except (LookupError, ValueError):
            piano_particles.append(p)
            i = len(piano_particles) - 1
        else:
            piano_particles[i] = p
    p.id = i
    p.frame = 0

def delete_particle(p):
    piano_particles[p.id] = None
    while piano_particles and piano_particles[-1] is None:
        piano_particles.pop(-1)

def sparkles_animate(self, duration):
    if self.frame > 4 and (random.random() > 0.97 ** duration or self.frame > 32):
        return delete_particle(self)
    self.vel = np.asanyarray(self.vel, dtype=np.float32)
    self.pos += self.vel * duration
    self.vel *= 0.9 ** duration
def sparkles_render(self):
    fade = (self.frame + 1) ** 0.125
    size = round_random(max(1, 5 / fade) + random.random() * 2)
    reg_polygon_complex(
        DISP,
        self.pos,
        self.col,
        0,
        size,
        size,
        alpha=255 / fade ** 3,
        thickness=min(size, 2),
        repetition=max(1, size - 2),
        soft=True,
    )

def blinds_render(self):
    h = 2
    if "rect" in self:
        r = self.pop("rect")
        self.pos = r[:2]
        self.width = r[2]
        self.blinds = deque()
        for i in range(round(r[3] / h)):
            self.blinds.append([(i & 1) * 2 - 1, self.width * (random.random() + 0.5) / 16])
    rendered = False
    for i, blind in enumerate(self.blinds):
        x1 = self.pos[0] + blind[0] * blind[1] * self.frame
        x2 = x1 + self.width
        if blind[0] >= 0:
            x1 += blind[1] * self.frame * 2
        else:
            x2 -= blind[1] * self.frame * 2
        y = self.pos[1] + i * h
        if x2 > x1:
            rendered = True
            bevel_rectangle(DISP, self.col, (x1, y, x2 - x1, h), bevel=0, alpha=191)
    if not rendered:
        delete_particle(self)

def update_piano():
    ts = editor.setdefault("timestamp", 0)
    t = pc()
    duration = max(0.001, min(t - ts, 0.125))
    rat = 0.75 ** duration
    editor.fade = editor.fade * rat + 1 - rat
    r = 1 + 1 / (duration * 6)
    if not project.patterns:
        project.create_pattern()
    if not project.instruments:
        add_instrument()
    if kspam[K_LEFT]:
        editor.targ_x -= 24 * duration
    if kspam[K_UP]:
        editor.targ_y += 24 * duration
    if kspam[K_RIGHT]:
        editor.targ_x += 24 * duration
    if kspam[K_DOWN]:
        editor.targ_y -= 24 * duration
    if editor.targ_x < 0:
        editor.targ_x = 0
    x, y = editor.scroll_x, editor.scroll_y
    editor.scroll_x = (editor.scroll_x * (r - 1) + editor.targ_x) / r
    editor.scroll_y = (editor.scroll_y * (r - 1) + editor.targ_y) / r
    note_height = 12 * editor.zoom_y
    note_spacing = note_height + 1
    if abs(x - editor.scroll_x) >= 1 / 256 / note_spacing:
        player.editor_surf = None
    elif abs(y - editor.scroll_y) >= 1 / 256 / note_spacing:
        player.editor_surf = None
    for p in piano_particles:
        if p:
            p.frame += duration
            if p.get("animate"):
                p.animate(p, duration)

def editor_toolbar():
    if kheld[K_LALT] or kheld[K_RALT]:
        if kclick[K_s]:
            editor.change_mode("S")
        elif kclick[K_i]:
            editor.change_mode("I")
        elif kclick[K_p]:
            editor.change_mode("P")
    c = (toolbar_height * 1.5, screensize[1] - toolbar_height // 2)
    w = toolbar_height // 3

    r = (c[0] - w, c[1] - w, w, w)
    ct = (127, 191, 255) if editor.mode == "S" or CTRL[kheld] else (96, 112, 127)
    bevel_rectangle(DISP, ct, r, bevel=3)
    if in_rect(mpos, r):
        if mclick[0]:
            editor.change_mode("S")
        bevel_rectangle(DISP, (255,) * 3, r, bevel=3, filled=False)
    message_display("S", w, (c[0] - w // 2 - 1, c[1] - w // 2 - 1), font="Rockwell", colour=(0, 32, 64), surface=DISP)
    if editor.mode == "S":
        selset = (
            ("freeform", "Freeform select", "Draw a freeform selection shape."),
            ("bounded", "Bounded select", "Select only objects within selection boundaries."),
        )
        mrect = (toolbar_height * 2, screensize[1] - toolbar_height + 12, 192, min(toolbar_height, 64))
        surf = pygame.Surface(mrect[2:], SRCALPHA)
        for i, t in enumerate(selset):
            s, name, description = t
            apos = (mrect[0] + 16, screensize[1] - toolbar_height + i * 32 + 32)
            hovered = hypot(*(np.array(mpos) - apos)) < 16
            if hovered and mclick[0]:
                editor.selection[s] ^= 1
            ripple_f = globals().get("s-ripple", concentric_circle)
            if editor.selection.get(s):
                col = (96, 255, 96)
            else:
                col = (127, 0, 0)
            pos = (16, i * 32 + 16)
            reg_polygon_complex(
                surf,
                pos,
                (255,) * 3 if hovered else col,
                0,
                14,
                14,
                0,
                255 if hovered else 255 * (abs((pc() - i / 2) / 4 % 1 - 0.5) + 0.5),
                2,
                9,
                True,
                soft=True
            )
            ripple_f(
                surf,
                colour=col,
                pos=pos,
                radius=16,
                fill_ratio=0.5,
            )
            message_display(
                name,
                16,
                (36, i * 32 + 4),
                colour=(255,) * 3 if hovered else (223,) * 3,
                align=0,
                surface=surf,
                font="Comic Sans MS",
            )
        if editor.fade < 63 / 64:
            im = pyg2pil(surf)
            a = im.getchannel("A")
            arr = np.linspace(editor.fade * 510, editor.fade * 510 - 255, mrect[2])
            np.clip(arr, 0, 255, out=arr)
            arr = np.tile(arr.astype(np.uint8), (mrect[3], 1))
            a2 = Image.fromarray(arr, "L")
            print(im, a, a2)
            A = ImageChops.multiply(a, a2)
            im.putalpha(A)
            surf = pil2pyg(im)
        DISP.blit(
            surf,
            mrect[:2],
        )

    r = (c[0] - w, c[1], w, w)
    ct = (191, 255, 127) if editor.mode == "I" else (112, 127, 96)
    bevel_rectangle(DISP, ct, r, bevel=3)
    if in_rect(mpos, r):
        if mclick[0]:
            editor.change_mode("I")
        bevel_rectangle(DISP, (255,) * 3, r, bevel=3, filled=False)
    message_display("I", w, (c[0] - w // 2 - 1, c[1] + w // 2 - 1), font="Rockwell", colour=(32, 64, 0), surface=DISP)
    if editor.mode == "I":
        if editor.note.instrument is not None:
            col = project.instruments[editor.note.instrument].colour
        else:
            col = (191,) * 3
        note_width = 60 * editor.zoom_x
        note_height = 12 * editor.zoom_y
        r = (toolbar_height * 2, screensize[1] - toolbar_height + 12, editor.note.length * note_width + 1, note_height + 1)
        col = col + (127 + 256 * abs(pc() % 1 - 0.5),)
        rounded_bev_rect(DISP, col, r, bevel=ceil(note_height / 5))
        pattern = project.patterns[0]
        timesig = pattern.timesig
        barlength = timesig[0] * timesig[1]
        measure = note_width / timesig[1]
        for i in range(ceil(min(editor.note.length * timesig[1] + 1, (screensize[0] - toolbar_height * 3) / measure))):
            col = 64 if i % timesig[1] else 127 if i % (barlength) else 255
            x = toolbar_height * 2 + i * measure
            draw_vline(DISP, round(x), screensize[1] - toolbar_height + 8, screensize[1] - toolbar_height + 17 + note_height, (col,) * 3)
        message_display(f"Length: {round_min(editor.note.length)}", 20, (toolbar_height * 2, screensize[1] - toolbar_height + 21 + note_height), surface=DISP, align=0)
        notesel = (toolbar_height * 2, screensize[1] - toolbar_height + 8, screensize[0] - toolbar_height * 3, note_height + 9)
        if in_rect(mpos, notesel) or editor.note.get("resizing"):
            target_length = (mpos2[0] - toolbar_height * 2) / note_width
            if not kheld[K_LSHIFT]:
                target_length = max(1, round(target_length * timesig[1] * 2)) / timesig[1] / 2
            elif target_length < 1 / 65536:
                target_length = 1 / 65536
            if mclick[0] or editor.note.get("resizing") and mheld[0]:
                editor.note.length = target_length
                editor.note.resizing = True
            else:
                editor.note.pop("resizing", None)
            if mclick[1]:
                sidebar.menu = 0
                enter = easygui.get_string(
                    "Set input note length",
                    "Miza Player",
                    str(round_min(editor.note.length)),
                )
                if enter:
                    editor.note.length = float(enter)
            draw_hline(DISP, round(toolbar_height * 2 + editor.note.length * note_width), mpos2[0] - 1, mpos[1] - 1, (191,) * 3)
            pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 13, mpos2[1] - 1), (mpos2[0] + 11, mpos2[1] - 1), width=2)
            pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 1, mpos2[1] - 13), (mpos2[0] - 1, mpos2[1] + 11), width=2)
            pygame.draw.circle(DISP, (255, 0, 0), mpos2, 9, width=2)
            message_display(
                target_length,
                min(20, toolbar_height // 3),
                (mpos2[0], mpos2[1] + 21),
                (255, 255, 127),
                surface=DISP,
                font="Comic Sans MS",
            )
        else:
            editor.note.pop("resizing", None)
    
    r = (c[0], c[1] - w, w, w)
    ct = (255, 127, 191) if editor.mode == "P" else (127, 96, 112)
    bevel_rectangle(DISP, ct, r, bevel=3)
    if in_rect(mpos, r):
        if mclick[0]:
            editor.change_mode("P")
        bevel_rectangle(DISP, (255,) * 3, r, bevel=3, filled=False)
    message_display("P", w, (c[0] + w // 2 - 1, c[1] - w // 2 - 1), font="Rockwell", colour=(64, 0, 32), surface=DISP)

n_measure = lambda n: n[0]
n_instrument = lambda n: n[1]
n_pos = lambda n: n[2]
n_pitch = lambda n: n[3]
n_length = lambda n: n[4]
n_volume = lambda n: n[5] if len(n) > 5 else 0.25
n_pan = lambda n: n[6] if len(n) > 6 else 0
n_effects = lambda n: n[7] if len(n) > 7 else ()
n_colour = lambda n: project.instruments[n_instrument(n)].colour

def n_rect(n):
    pattern = project.patterns[editor.pattern]
    timesig = pattern.timesig
    note_width = 60 * editor.zoom_x
    note_height = 12 * editor.zoom_y
    note_spacing = note_height + 1
    keys = ceil((player.rect[3] - 16) / note_spacing + 1)
    centre = 48 + (keys + 1 >> 1) + floor(editor.scroll_y)
    x = PW + (n_pos(n) + (n_measure(n) - editor.scroll_x / timesig[0]) * timesig[0]) * note_width
    y = note_spacing * (centre - n_pitch(n) - 1.5) + 1
    w = n_length(n) * note_width
    h = note_height
    return x, y, w, h

def note_from_id(i):
    n = ctypes.cast(i, ctypes.py_object).value
    if not isinstance(n, collections.abc.MutableSequence):
        return
    return n

def create_note(n, particles=True):
    pattern = project.patterns[editor.pattern]
    m = n_measure(n)
    try:
        pattern.measures[m].append(n)
    except KeyError:
        pattern.measures[m] = [n]
    player.editor_surf = None
    if particles:
        note_width = 60 * editor.zoom_x
        note_height = 12 * editor.zoom_y
        col = n_colour(n)
        r = n_rect(n)
        for i in range(round_random(24 * n_length(n))):
            p = np.array(r[:2]) + [random.random() * note_width * n_length(n), random.random() * note_height]
            z = random.random() * tau
            v = random.random() * 9 + 3
            vel = [v * cos(z), v * sin(z)]
            spawn_particle(pos=p, vel=vel, col=col, animate=sparkles_animate, render=sparkles_render)
    return n

def delete_note(n, particles=True):
    pattern = project.patterns[editor.pattern]
    m = n_measure(n)
    pattern.measures[m].remove(n)
    if not pattern.measures[m]:
        pattern.measures.pop(m)
    player.editor_surf = None
    editor.selection.notes.remove(id(n))
    if particles:
        col = n_colour(n)
        r = n_rect(n)
        spawn_particle(rect=r, col=col, render=blinds_render)
    return n

def render_piano():
    pattern = project.patterns[editor.pattern]
    timesig = pattern.timesig
    note_width = 60 * editor.zoom_x
    note_height = 12 * editor.zoom_y
    note_spacing = note_height + 1
    keys = ceil((player.rect[3] - 16) / note_spacing + 1)
    barlength = timesig[0] * timesig[1]
    offs_x = (editor.scroll_x * timesig[1]) % 1 * barlength
    itx = floor(editor.scroll_x * timesig[1])
    offs_y = editor.scroll_y % 1 * note_spacing
    offs_y = round(offs_y - note_spacing / 2)
    centre = 48 + (keys + 1 >> 1) + floor(editor.scroll_y)
    surf = player.get("editor_surf")
    if not surf or surf.get_size() != player.rect[2:]:
        surf = player["editor_surf"] = pygame.Surface(player.rect[2:], SRCALPHA)

        for i in range(keys + 1):
            note = round(centre - i)
            name = note_names[note % 12]
            c = (127,) * 3
            if i != keys:
                draw_hline(surf, 0, player.rect[2], offs_y, c)
            if name.endswith("#"):
                c = note_colour(note % 12, 0.75, 0.125)
                r = (PW, offs_y - note_spacing + 1, player.rect[2], note_height)
                surf.fill(c, r)
            else:
                c = note_colour(note % 12, 0.5, 0.25)
                r = (PW, offs_y - note_spacing + 1, player.rect[2], note_height)
                surf.fill(c, r)
            offs_y += note_spacing

        linec = ceil((player.rect[2] - PW) / note_width * timesig[1])
        for i in range(linec):
            c = 64 if (i + itx) % timesig[1] else 127 if (i + itx) % (barlength) else 255
            x = PW + i * note_width / timesig[1] - offs_x
            if x < PW - 0.125:
                continue
            draw_vline(surf, round(x), 0, player.rect[3], (c,) * 3)
        for i in range(linec):
            x = PW + i * note_width / timesig[1] - offs_x
            if x < PW - 0.125:
                continue
            if not (i + itx) % (barlength):
                message_display((i + itx) // barlength, 12, (x + 3, 0), colour=(255, 255, 0), surface=surf, align=0)

        min_measure = int(editor.scroll_x / timesig[0])
        max_measure = ceil(editor.scroll_x / timesig[0] + (player.rect[2] - PW) / timesig[0] / note_width)
        for i in range(min_measure, max_measure):
            try:
                notes = pattern.measures[i]
            except KeyError:
                continue
            for n in notes[-1024:]:
                col = n_colour(n)
                r = n_rect(n)
                rounded_bev_rect(surf, col + (191,), r, bevel=ceil(note_height / 5))

        offs_y = editor.scroll_y % 1 * note_spacing
        offs_y = round(offs_y - note_spacing / 2)
        for i in range(keys + 1):
            note = round(centre - i)
            name = note_names[note % 12]
            c = note_colour(note % 12, 0.375, 0.875)
            r = (0, offs_y - note_spacing, PW, note_height)
            bevel_rectangle(surf, c, r, bevel=ceil(note_height / 5))
            octave = note // 12
            if not note % 12 and note_height > 6:
                s = ceil(note_height * 0.75)
                message_display(f"C{octave}", s, (PW - 2, offs_y - note_spacing + note_height), colour=(0,) * 3, surface=surf, align=2)
            if name.endswith("#"):
                c = note_colour(note % 12, 0.375, 1 / 3)
                r = (0, offs_y - note_spacing + ceil(note_height / 10), PW * 5 / 8, note_height - ceil(note_height / 10) * 2)
                bevel_rectangle(surf, c, r, bevel=ceil(note_height / 5))
            offs_y += note_spacing

    DISP.blit(surf, player.rect[:2])
    xy = [None, None]
    selecting = editor.mode == "S" or CTRL[kheld]

    offs_y = editor.scroll_y % 1 * note_spacing
    offs_y = round(offs_y - note_spacing / 2)
    pitch = 0
    for i in range(keys + 1):
        note = round(centre - i)
        name = note_names[note % 12]
        rect = (16, offs_y - note_spacing, player.rect[2], note_spacing)
        selected = in_rect(mpos, rect) and in_rect(mpos, player.rect[:3] + (player.rect[3] - 16,))
        playing = (36 <= note < 70) and alphakeys[note - 36]
        if selected or playing:
            pitch = note
            xy[1] = offs_y - note_spacing
            if selecting:
                c = note_colour(note % 12, 0.75, 1)
                r = (0, offs_y - note_spacing, PW, note_height)
                bevel_rectangle(DISP, c, r, bevel=ceil(note_height / 5))
                octave = note // 12
                if not note % 12 and note_height > 6:
                    s = ceil(note_height * 0.75)
                    message_display(f"C{octave}", s, (46, offs_y - note_spacing + note_height), colour=(0,) * 3, surface=DISP, align=2)
                if name.endswith("#"):
                    c = note_colour(note % 12, 0.75, 0.6)
                    r = (0, offs_y - note_spacing + ceil(note_height / 10), PW * 5 / 8, note_height - ceil(note_height / 10) * 2)
                    bevel_rectangle(DISP, c, r, bevel=ceil(note_height / 5))
                c = (255, 255, 255, 48)
                r = (PW, offs_y - note_spacing + 1, player.rect[2] - PW, note_height)
                bevel_rectangle(DISP, c, r, bevel=0)
            if mpos[0] >= PW and selected:
                n = floor((mpos[0] - PW) / note_width * timesig[1])
                space = round(note_width / timesig[1])
                x = PW + n * space
                xy[0] = x
                if selecting:
                    r = (x, 0, space, player.rect[3])
                    bevel_rectangle(DISP, c, r, bevel=0)
                    for i in range(ceil(player.rect[3] / 24)):
                        y = round(24 * i + (pc() * 72) % 24)
                        draw_hline(DISP, x, x + space - 1, y, (255,) * 3)
            if selecting:
                for i in range(ceil(player.rect[2] / 24 - 2)):
                    x = round(24 * i + PW + (pc() * 72) % 24)
                    if x >= player.rect[2]:
                        break
                    draw_vline(DISP, x, offs_y - note_spacing + 1, offs_y - 1, (255,) * 3)
        offs_y += note_spacing
    if all(xy):
        npos = round_min((xy[0] - PW) / note_width % timesig[0])
        measurepos = int((xy[0] - PW) / timesig[0] / note_width)
    else:
        measurepos = npos = None
    measures = pattern.measures
    if all(xy) or editor.selection.point:
        if selecting:
            if editor.selection.point:
                c = (255, 127, 255, 64 + 192 * abs(pc() % 1 - 0.5))
                if not editor.selection.freeform:
                    p = editor.selection.point
                    q = mpos2
                    r = [min(p[0], q[0]), min(p[1], q[1])]
                    r += [max(p[0], q[0]) - r[0], max(p[1], q[1]) - r[1]]
                    if not mheld[0]:
                        editor.selection.point = 0
                        min_measure = int(editor.scroll_x / timesig[0])
                        max_measure = ceil(editor.scroll_x / timesig[0] + (player.rect[2] - PW) / timesig[0] / note_width)
                        for i in range(min_measure, max_measure):
                            try:
                                notes = pattern.measures[i]
                            except KeyError:
                                continue
                            for n in notes[-1024:]:
                                if int_rect(n_rect(n), r):
                                    if id(n) not in editor.selection.notes:
                                        editor.selection.notes.add(id(n))
                    bevel_rectangle(DISP, c, r, bevel=4)
            elif in_rect(mpos, player.rect):
                if mc4[0]:
                    editor.selection.point = mpos2
                    if not CTRL[kheld] and not SHIFT[kheld]:
                        editor.selection.notes.clear()
                pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 13, mpos2[1] - 1), (mpos2[0] + 11, mpos2[1] - 1), width=2)
                pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 1, mpos2[1] - 13), (mpos2[0] - 1, mpos2[1] + 11), width=2)
                pygame.draw.circle(DISP, (255, 0, 0), mpos2, 9, width=2)
        elif editor.mode == "I" and all(xy):
            if mheld[1]:
                editor.selection.notes.clear()
                pygame.draw.line(DISP, (255, 0, 0), (mpos2[0] - 8, mpos2[1] + 6), (mpos2[0] + 6, mpos2[1] - 8), width=2)
                pygame.draw.circle(DISP, (255, 0, 0), mpos2, 12, width=2)
            hnote = False
            min_measure = int(editor.scroll_x / timesig[0])
            max_measure = floor(editor.scroll_x / timesig[0] + (mpos2[0] - PW) / timesig[0] / note_width) + 1
            try:
                for i in range(min_measure, max_measure):
                    try:
                        notes = pattern.measures[i]
                    except KeyError:
                        pass
                    else:
                        for n in notes[-1024:]:
                            r = n_rect(n)
                            if in_rect(mpos, r):
                                if not hnote:
                                    hnote = n
                                if mheld[1]:
                                    delete_note(n)
                                    raise StopIteration
                                if mc4[0]:
                                    if not CTRL[kheld] and not SHIFT[kheld]:
                                        if id(n) not in editor.selection.notes:
                                            editor.selection.notes.clear()
                                    if id(n) not in editor.selection.notes:
                                        editor.selection.notes.add(id(n))
                                    editor.selection.orig = (measurepos, npos, pitch)
                                    raise StopIteration
            except StopIteration:
                pass
            if editor.note.instrument is not None:
                if hnote:
                    r = n_rect(hnote)
                    bevel_rectangle(DISP, (255,) * 3, r, bevel=3, filled=False)
                else:
                    if mc4[0]:
                        if not CTRL[kheld] and not SHIFT[kheld]:
                            editor.selection.notes.clear()
                        m = measurepos
                        N = [m, editor.note.instrument, npos, pitch, editor.note.length]
                        if editor.note.volume != 0.25 or editor.note.pan or editor.note.effects:
                            N.append(editor.note.volume)
                            if editor.note.pan or editor.note.effects:
                                N.append(editor.note.pan)
                                if editor.note.effects:
                                    N.append(list(editor.note.effects))
                        create_note(N, True)
                        print(m, N)
                    elif not any(mheld):
                        r = tuple(xy) + (editor.note.length * note_width + 1, note_height + 1)
                        c = project.instruments[editor.note.instrument].colour + (96 + 192 * abs(pc() % 1 - 0.5),)
                        rounded_bev_rect(DISP, c, r, bevel=ceil(note_height / 5))

    ntuple = (measurepos, npos, pitch)
    if CTRL[kheld] or SHIFT[kheld]:
        move = None
    elif mheld[0] and all(xy) and all(editor.selection.orig) and editor.selection.orig != ntuple:
        move = [x - y for x, y in zip(ntuple, editor.selection.orig)]
        m = move.pop(0)
        move[0] += m * timesig[0]
        if not any(move):
            move = None
    else:
        move = None
    for n in map(note_from_id, editor.selection.notes):
        if kheld[K_DELETE]:
            delete_note(n)
            continue
        if move:
            print(measures)
            x, y = move
            x += n_measure(n) * timesig[0] + n_pos(n)
            a, b = divmod(x, timesig[0])
            if a != n_measure(n):
                delete_note(n, False)
                n[0] = a
                n[2] = b
                n[3] += y
                create_note(n, False)
                editor.selection.notes.add(id(n))
            else:
                n[2] = b
                n[3] += y
            print(n)
            print(measures)
        col = n_colour(n) + (191,)
        r = n_rect(n)
        speed = 0.75 / n_length(n) ** 0.5
        anima_rectangle(
            DISP,
            col,
            r,
            frame=3,
            count=max(1, round(1.5 / speed)),
            flash=0,
            ratio=pc() * speed,
            reduction=0.2 * speed,
        )
        anima_rectangle(
            DISP,
            col,
            r,
            frame=0,
            count=0,
            flash=1,
            ratio=pc() / 2,
        )
    if move:
        player.editor_surf = None
        if not mheld[0]:
            editor.selection.orig = (None, None)
        else:
            editor.selection.orig = ntuple

    r = player.rect[:2] + (16, player.rect[3] - 16)
    hovered = in_rect(mpos, r)
    A = (191 if editor.get("y-scrolling") else 127 if hovered else 16,)
    c = (32,) * 3 + A
    bevel_rectangle(DISP, c, r, bevel=4)
    dnc = (player.rect[3] - 16) / note_spacing
    ratio = max(8, (player.rect[3] - 16) * dnc / 128)
    if hovered and mc4[0] or editor.get("y-scrolling"):
        editor["y-scrolling"] = True
        y = mpos2[1]
        editor.targ_y = (y / player.rect[3] - 0.5) * -128
    if not any(mheld):
        editor.pop("y-scrolling", None)
    y = (editor.scroll_y / -128 + 0.5) * (player.rect[3] - 16) - round(ratio / 2)
    r = [player.rect[0], y, 16, ratio]
    c = (223,) * 3 + A
    bevel_rectangle(DISP, c, r, bevel=4)

    measurecount = max(pattern.measures or (4,)) + 4
    r = (PW, player.rect[3] - 16, player.rect[2] - PW, 16)
    hovered = in_rect(mpos, r)
    A = (191 if editor.get("x-scrolling") else 127 if hovered else 16,)
    c = (32,) * 3 + A
    bevel_rectangle(DISP, c, r, bevel=4)
    dnc = (player.rect[2] - PW) / note_width / timesig[0]
    ratio = max(8, (player.rect[2] - PW) * dnc / measurecount)
    if hovered and mc4[0] or editor.get("x-scrolling"):
        editor["x-scrolling"] = True
        x = mpos2[0]
        editor.targ_x = ((x - PW) / (player.rect[2] - PW)) * measurecount
    if not any(mheld):
        editor.pop("x-scrolling", None)
    x = (editor.scroll_x / measurecount) * (player.rect[2] - PW) - round(ratio / 2)
    r = [x, player.rect[3] - 16, ratio, 16]
    c = (223,) * 3 + A
    bevel_rectangle(DISP, c, r, bevel=4)

    for p in piano_particles:
        if p and p.get("render"):
            p.render(p)