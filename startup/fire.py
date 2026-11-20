import curses
import random
import time

ART = (
    "██████▓██   ██▓ ███▄    █  ▄████▄      ██▓███   █    ██  ██▓      ██████ ▓█████",
    "▒██    ▒ ▒██  ██▒ ██ ▀█   █ ▒██▀ ▀█     ▓██░  ██▒ ██  ▓██▒▓██▒    ▒██    ▒ ▓█   ▀",
    "░ ▓██▄    ▒██ ██░▓██  ▀█ ██▒▒▓█    ▄    ▓██░ ██▓▒▓██  ▒██░▒██░    ░ ▓██▄   ▒███",
    "  ▒   ██▒ ░ ▐██▓░▓██▒  ▐▌██▒▒▓▓▄ ▄██▒   ▒██▄█▓▒ ▒▓▓█  ░██░▒██░      ▒   ██▒▒▓█  ▄",
    "▒██████▒▒ ░ ██▒▓░▒██░   ▓██░▒ ▓███▀ ░   ▒██▒ ░  ░▒▒█████▓ ░██████▒▒██████▒▒░▒████▒",
    "▒ ▒▓▒ ▒ ░  ██▒▒▒ ░ ▒░   ▒ ▒ ░ ░▒ ▒  ░   ▒▓▒░ ░  ░░▒▓▒ ▒ ▒ ░ ▒░▓  ░▒ ▒▓▒ ▒ ░░░ ▒░ ░",
    "░ ░▒  ░ ░▓██ ░▒░ ░ ░░   ░ ▒░  ░  ▒      ░▒ ░     ░░▒░ ░ ░ ░ ░ ▒  ░░ ░▒  ░ ░ ░ ░  ░",
    "░  ░  ░  ▒ ▒ ░░     ░   ░ ░ ░           ░░        ░░░ ░ ░   ░ ░   ░  ░  ░     ░",
    "      ░  ░ ░              ░ ░ ░                     ░         ░  ░      ░     ░  ░",
    "         ░ ░                ░",
)

def _safe_add(stdscr, y, x, value, attr, width):
    if y < 0 or y >= stdscr.getmaxyx()[0] or width <= 0:
        return
    try:
        stdscr.addnstr(y, max(0, x), value, max(0, width - max(0, x) - 1), attr)
    except curses.error:
        pass

def _draw(stdscr, duration=4.5):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(35)
    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        pass
    for pair, color in ((1, curses.COLOR_RED), (2, curses.COLOR_YELLOW),
                        (3, curses.COLOR_WHITE), (4, curses.COLOR_MAGENTA)):
        try:
            curses.init_pair(pair, color, -1)
        except curses.error:
            pass

    started = time.monotonic()
    heat = []
    frame = 0
    art_width = max(map(len, ART))
    while time.monotonic() - started < duration:
        height, width = stdscr.getmaxyx()
        if height < 8 or width < 24:
            stdscr.erase()
            _safe_add(stdscr, max(0, height // 2), 0, "SYNC PULSE", curses.A_BOLD, width)
            stdscr.refresh()
            time.sleep(0.08)
            continue

        fire_height = max(3, height - 1)
        if len(heat) != fire_height or (heat and len(heat[0]) != width):
            heat = [[0 for _ in range(width)] for _ in range(fire_height)]
        for x in range(width):
            heat[-1][x] = random.randint(150, 255) if random.random() > 0.08 else random.randint(40, 120)
        for y in range(fire_height - 2, -1, -1):
            for x in range(width):
                below = heat[y + 1][x]
                left = heat[y + 1][max(0, x - 1)]
                right = heat[y + 1][min(width - 1, x + 1)]
                below_two = heat[min(fire_height - 1, y + 2)][x]
                heat[y][x] = max(0, (below + left + right + below_two) // 4 - random.randint(0, 24))

        stdscr.erase()
        chars = " .:-=+*#%@"
        for y, row in enumerate(heat):
            for x, value in enumerate(row):
                if value < 18:
                    continue
                char = chars[min(len(chars) - 1, value * len(chars) // 256)]
                pair = 1 if value < 100 else 2 if value < 180 else 3
                try:
                    stdscr.addch(y, x, char, curses.color_pair(pair) | curses.A_BOLD)
                except curses.error:
                    pass

        art_start = max(0, (height - len(ART)) // 2 - 1)
        reveal = min(art_width, 22 + frame * 4)
        if width >= art_width + 2:
            offset = (width - art_width) // 2
            for index, line in enumerate(ART):
                color = curses.color_pair(3 if frame % 8 < 4 else 1) | curses.A_BOLD
                _safe_add(stdscr, art_start + index, offset, line[:reveal], color, width)
        else:
            travel = art_width + width
            offset = width - (frame * 2 % travel)
            for index, line in enumerate(ART):
                visible = line[max(0, -offset):max(0, -offset) + width - 1]
                color = curses.color_pair(3 if frame % 8 < 4 else 1) | curses.A_BOLD
                _safe_add(stdscr, art_start + index, max(0, offset), visible, color, width)

        footer_y = min(height - 2, art_start + len(ART) + 1)
        _safe_add(stdscr, footer_y, 1, "MADE BY SYNC  |  SYNC PULSE", curses.color_pair(2) | curses.A_BOLD, width)
        _safe_add(stdscr, height - 1, 1, "discord.gg/8rUgJDpE8y  |  SPACE / ESC / Q TO SKIP", curses.color_pair(1), width)
        stdscr.refresh()
        frame += 1
        try:
            if stdscr.getch() in (ord("q"), 27, ord(" ")):
                break
        except curses.error:
            pass

def run_fire_splash(duration=4.5):
    try:
        curses.wrapper(_draw, duration)
    except (curses.error, OSError, AttributeError):
        return
