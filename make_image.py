#!/usr/bin/env python3
"""make.fun entry: news-image-20261127.

One 1024x1024 poster summing up Friday 27 November 2026 world news.

* Canvas 1024x1024 drawn at 2x supersample, downscaled deterministically.
* Every text run >= MIN_FONT (19 CSS px), measured with real font metrics,
  wrapped to its box, and asserted to stay inside its card and the canvas.
* All 32 stories (8 leads + 24 briefs) rendered, in story order, deterministically.
* Prints "ALL LAYOUT CHECKS PASSED" and exits 0.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

# --- fixed constants -------------------------------------------------------
SIZE = 1024
SCALE = 2
W = H = SIZE * SCALE
MIN_FONT = 19 * SCALE          # 19 CSS px floor, enforced on every text run

BG = "#0B1220"
CARD = "#151F33"
HAIR = "#2A3A57"
BODY = "#D7DEEA"
WHITE = "#F7FAFF"
AMBER = "#F2B33D"
TEAL = "#4FD1C5"
MUTED = "#8FA1BE"

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
_font_cache = {}


def font(px: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (px, bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_REG
        _font_cache[key] = ImageFont.truetype(path, px)
    return _font_cache[key]


# --- story model -----------------------------------------------------------
@dataclass(frozen=True)
class Story:
    sid: str
    region: str
    place: str
    headline: str
    summary: str
    lead: bool = False


LEADS: Tuple[Story, ...] = (
    Story("L1", "EUROPE", "KYIV, UKRAINE",
          "RUSSIA PREPARES NEW MASS STRIKE ON UKRAINE",
          "Zelensky says Moscow is preparing a new mass strike; ballistic missiles hit a Kyiv shopping centre, wounding seven.", True),
    Story("L2", "AMERICAS", "WASHINGTON, US",
          "US PROPOSES TARIFFS ON 14 ECONOMIES",
          "USTR proposes 15-35% duties on China, EU, India, Japan and 10 others; China could face up to 40%.", True),
    Story("L3", "AFRICA", "BUNIA, DR CONGO",
          "EBOLA CASES IN CONGO PASS 12,000",
          "DRC reports 12,021 confirmed Bundibugyo Ebola cases and 5,904 deaths as fighting disrupts the response.", True),
    Story("L4", "MIDDLE EAST", "KUWAIT CITY, KUWAIT",
          "TWO ITALIANS KILLED IN KUWAIT DRONE ATTACK",
          "Debris from intercepted drones killed two Italian technicians; Iran denied carrying out the attack.", True),
    Story("L5", "OCEANIA", "MELBOURNE, AUSTRALIA",
          "VICTORIA VOTES AS LABOR FACES WIPEOUT",
          "Victorians head to the polls Saturday with polls tipping the Coalition to end 12 years of Labor rule.", True),
    Story("L6", "EUROPE", "BRUSSELS, EU",
          "EU LEADERS CLASH OVER BUDGET AND UKRAINE",
          "Leaders wrestle over a EUR 1.6 trillion 2028-2034 budget and a proposed EUR 45 billion Ukraine loan.", True),
    Story("L7", "AMERICAS", "UNITED STATES",
          "THANKSGIVING STORMS CUT POWER TO 750,000",
          "Heavy rain, wind and flooding hit much of the US, postponing the Macy's parade and leaving 750,000 without power.", True),
    Story("L8", "ASIA-PACIFIC", "BEIJING, CHINA",
          "CHINA SLAMS NEW AU-PHILIPPINES PACT",
          "Beijing said the new defence pact between Australia and the Philippines would exacerbate South China Sea tensions.", True),
)

BRIEFS: Tuple[Story, ...] = (
    Story("B1", "EUROPE", "MOSCOW, RUSSIA",
          "TRUMP URGES PUTIN TO PULL BACK IN EUROPE",
          "Trump said he asked Putin to scale back military aggression in Europe to help end the Ukraine war."),
    Story("B2", "EUROPE", "KYIV, UKRAINE",
          "UKRAINE STRIKES FOURTH RUSSIAN AIRBASE",
          "Neptune missiles struck an airbase used for glide-bomb attacks; drones hit a Transneft oil facility."),
    Story("B3", "EUROPE", "WARSAW, POLAND",
          "POLAND WARNS ON MISSILES NEAR BORDER",
          "Poland's top diplomat called Russian missiles near its border a direct threat; NATO was cool on shooting them down."),
    Story("B4", "EUROPE", "BERLIN, GERMANY",
          "MERZ SAYS RUSSIA THREAT TO EUROPE IS ESCALATING",
          "German Chancellor Merz accused Russia of escalating threats and defended higher defence spending."),
    Story("B5", "EUROPE", "PARIS, FRANCE",
          "DEPARDIEU TO STAND TRIAL ON RAPE CHARGE",
          "French actor Gerard Depardieu will stand trial on a rape charge, his lawyer said."),
    Story("B6", "AMERICAS", "WASHINGTON, US",
          "JUDGE BLOCKS NEW BIRTHRIGHT CITIZENSHIP CURBS",
          "A federal judge blocked the administration's latest attempt to restrict birthright citizenship under the 14th Amendment."),
    Story("B7", "AMERICAS", "WASHINGTON, US",
          "TRUMP CALLS REVISED GDP DATA FAKE",
          "Trump demanded an investigation after Q3 growth was revised up to 4.3% from 3.4%; he gave no evidence."),
    Story("B8", "AMERICAS", "UNITED STATES",
          "SPACEX CLEARED TO LAUNCH 1 MILLION SATELLITES",
          "The FCC authorised SpaceX to build orbital data centres, approving a constellation of one million satellites."),
    Story("B9", "AMERICAS", "MISSISSIPPI COAST, US",
          "SIX KILLED IN PLANE CRASH OFF MISSISSIPPI",
          "Six people, including children, were killed in a plane crash off the Mississippi coast."),
    Story("B10", "AMERICAS", "SAN FRANCISCO, US",
          "HUGE KING TIDES BATTER CALIFORNIA COAST",
          "Year's highest tides flooded parts of the San Francisco waterfront as a storm reached California."),
    Story("B11", "AMERICAS", "PANAMA CITY, PANAMA",
          "EARTHQUAKE TRIGGERS TSUNAMI WARNINGS",
          "An earthquake in Panama triggered tsunami warnings across parts of the Americas."),
    Story("B12", "ASIA-PACIFIC", "NEW DELHI, INDIA",
          "INDIA SEEKS EARLY US TRADE DEAL",
          "India said it has no structural excess capacity and remains committed to an early trade deal with Washington."),
    Story("B13", "ASIA-PACIFIC", "TOKYO, JAPAN",
          "JAPAN WARNS CHINA SHIPS LEAVE DISPUTED WATERS",
          "Japan warned Chinese vessels to leave waters near the disputed islands."),
    Story("B14", "ASIA-PACIFIC", "DHAKA, BANGLADESH",
          "MINISTER DISMISSES HASINA RETURN",
          "A minister said ousted PM Sheikh Hasina could return only in handcuffs; a former aide was arrested in Dhaka."),
    Story("B15", "ASIA-PACIFIC", "BEIJING, CHINA",
          "CHINA INDUSTRIAL PROFITS REBOUND IN OCTOBER",
          "China's industrial profits rose sharply in October on a low base and an easing price war."),
    Story("B16", "ASIA-PACIFIC", "NEW DELHI, INDIA",
          "TOP COURT ASKS FOR FOOD WARNING LABELS",
          "India's Supreme Court asked for separate warning labels on packaged foods high in salt, sugar and fat."),
    Story("B17", "ASIA-PACIFIC", "HONIARA, SOLOMON ISLANDS",
          "SOLOMONS PACT ENDS CHINA SECURITY DEAL",
          "A new defence treaty between Solomon Islands and Australia ended the nation's security pact with China."),
    Story("B18", "AFRICA", "KINSHASA, DR CONGO",
          "CONGO TO SUSPEND ALL COBALT EXPORTS",
          "The regulator said DR Congo will suspend all cobalt exports from 30 November until further notice."),
    Story("B19", "AFRICA", "NAIROBI, KENYA",
          "KENYA COURT HALTS EBOLA QUARANTINE SITE",
          "A court ruled a US-backed Ebola quarantine facility violated the constitution and halted its construction."),
    Story("B20", "AFRICA", "BUNIA, DR CONGO",
          "EBOLA VACCINE TRIALS TO START NEXT WEEK",
          "WHO said two Ebola vaccine candidates will begin phase 2 trials in DR Congo next week."),
    Story("B21", "MIDDLE EAST", "RIYADH, SAUDI ARABIA",
          "HOUTHI STRIKE HITS JAZAN OIL REFINERY",
          "A Houthi projectile struck the Jazan refinery, killing a Nepalese worker; the coalition destroyed a launch pad."),
    Story("B22", "MIDDLE EAST", "RIYADH, SAUDI ARABIA",
          "SAUDI DEFENCES INTERCEPT MISSILES OVER RIYADH",
          "Saudi air defences intercepted two ballistic missiles toward Riyadh and two drones over the Eastern Province."),
    Story("B23", "MIDDLE EAST", "STRAIT OF HORMUZ",
          "TANKERS HIT SEA MINES IN HORMUZ, IRAN SAYS",
          "Iran's Guard said two tankers that crossed without permission hit sea mines; a tanker master reported a blast."),
    Story("B24", "OCEANIA", "CANBERRA, AUSTRALIA",
          "AUSTRALIA PASSES GAS RESERVATION SCHEME",
          "The government passed its National Gas Reservation scheme in the final sitting week in Canberra."),
)

ALL_STORIES: Tuple[Story, ...] = LEADS + BRIEFS

REGION_COLORS = {
    "EUROPE": AMBER,
    "AMERICAS": TEAL,
    "ASIA-PACIFIC": AMBER,
    "AFRICA": TEAL,
    "MIDDLE EAST": AMBER,
    "OCEANIA": TEAL,
}

# --- text measurement helpers ---------------------------------------------
def fit_text(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> bool:
    return f.getlength(text) <= max_w + 0.5


def fit_line(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> str:
    """Return *text* if it fits, otherwise truncate with an ellipsis."""
    if fit_text(text, f, max_w):
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fit_text(text[:mid] + "...", f, max_w):
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "..."


def wrap_words(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    """Greedy word wrap measured with real font metrics."""
    lines: List[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if fit_text(candidate, f, max_w):
            current = candidate
        else:
            if current:
                lines.append(current)
            current = fit_line(word, f, max_w)
    if current:
        lines.append(current)
    return lines


def balance_two(lines: Sequence[str], f: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    """Rebalance a two-line headline so neither line is unnecessarily long."""
    if len(lines) != 2:
        return list(lines)
    a, b = lines[0], lines[1]
    if f.getlength(a) <= f.getlength(b):
        a, b = b, a
    words = a.split()
    if len(words) < 2:
        return list(lines)
    for cut in range(len(words) - 1, 0, -1):
        head = " ".join(words[:cut])
        tail = " ".join(words[cut:])
        if fit_text(head, f, max_w) and fit_text(tail, f, max_w):
            cand = [head, tail]
            if max(f.getlength(x) for x in cand) < max(f.getlength(a), f.getlength(b)):
                return cand
    return list(lines)


# --- canvas + primitives ---------------------------------------------------
class Canvas:
    def __init__(self):
        self.im = Image.new("RGB", (W, H), BG)
        self.draw = ImageDraw.Draw(self.im)
        self.runs = 0

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        x0, y0, x1, y1 = box
        if radius:
            self.draw.rounded_rectangle(box, radius=radius, fill=fill,
                                        outline=outline, width=width)
        else:
            self.draw.rectangle(box, fill=fill, outline=outline, width=width)

    def line(self, points, fill, width=1):
        self.draw.line(points, fill=fill, width=width)

    def text(self, xy, text, f, fill, anchor="lt", bounds=None, name=""):
        """Draw one measured text run; assert font floor and all bounds."""
        assert text, f"empty run: {name}"
        assert f.size >= MIN_FONT, f"font too small: {f.size} < {MIN_FONT} ({name})"
        x, y = xy
        l, t, r, b = self.draw.textbbox((x, y), text, font=f, anchor=anchor)
        if bounds is not None:
            bx0, by0, bx1, by1 = bounds
            assert l >= bx0 - 0.5 and t >= by0 - 0.5, \
                f"run {name!r} starts outside its box: {(l, t)} < {(bx0, by0)}"
            assert r <= bx1 + 0.5 and b <= by1 + 0.5, \
                f"run {name!r} overflows its box: {(r, b)} > {(bx1, by1)} text={text!r}"
        assert l >= 0 and t >= 0 and r <= W and b <= H, \
            f"run {name!r} outside canvas: {(l, t, r, b)} text={text!r}"
        self.draw.text((x, y), text, font=f, fill=fill, anchor=anchor)
        self.runs += 1


def s(px: int) -> int:
    return px * SCALE


# --- poster ----------------------------------------------------------------
# Short, source-faithful place labels for the two places whose full string is
# wider than a 4-column card at the 19 px floor.  Region stays the main chip.
PLACE_SHORT = {
    "MELBOURNE, AUSTRALIA": "MELBOURNE",
    "HONIARA, SOLOMON ISLANDS": "SOLOMON ISLANDS",
}


def place_label(story: Story) -> str:
    return PLACE_SHORT.get(story.place, story.place)


def draw_poster() -> Image.Image:
    c = Canvas()

    # ---- header: the day named in the largest type on the poster ----
    header_h = s(100)
    c.rect((0, 0, W, header_h), fill="#101B2E")
    c.line((0, header_h, W, header_h), fill=AMBER, width=s(2))

    day_font = font(s(44), True)
    day = "FRIDAY 27 NOVEMBER 2026"
    assert fit_text(day, day_font, W - s(60)), "day headline does not fit header"
    c.text((s(32), s(8)), day, day_font, WHITE, name="day")

    if True:
        sub_font = font(s(19), False)
        day_ink_bottom = s(8) + day_font.getbbox("Hg")[3]
        sub_y = max(s(56), day_ink_bottom + s(2))
        assert sub_y + s(24) <= header_h, "subtitle does not fit header"
        c.text((s(34), sub_y),
               "WORLD NEWS  /  ONE DAY  /  32 STORIES  /  SIX CONTINENTS",
               sub_font, BODY, name="subtitle")

    # ---- grid: all 32 stories in 4 columns; uniform 3-line cards ----
    grid_y = header_h + s(10)
    margin = s(24)
    gap = s(6)
    cols = 4
    card_w = (W - 2 * margin - (cols - 1) * gap) // cols
    inner_w = card_w - 2 * s(6)

    head_font = font(s(19), True)
    region_font = font(s(19), True)
    place_font = font(s(19), False)
    # 19 CSS px caps have ~18.5 device px of ink; 39 device px is the line box.
    line_h = 39
    card_pad_v = s(4)
    head_lines_max = 3
    card_h = (2 + head_lines_max) * line_h + 2 * card_pad_v

    row_heights = []
    for start in range(0, len(ALL_STORIES), cols):
        row = ALL_STORIES[start:start + cols]
        for st in row:
            n = len(wrap_words(st.headline, head_font, inner_w))
            assert 1 <= n <= head_lines_max, \
                f"{st.sid}: {n} headline lines > {head_lines_max}: {st.headline!r}"
            assert fit_text(st.region, region_font, inner_w), \
                f"{st.sid}: region too wide: {st.region!r}"
            assert fit_text(place_label(st), place_font, inner_w), \
                f"{st.sid}: place too wide: {place_label(st)!r}"
        row_heights.append(card_h)

    grid_bottom = grid_y + sum(row_heights) + gap * (len(row_heights) - 1)
    assert grid_bottom <= H - s(24), \
        f"grid overflows canvas: bottom={grid_bottom} > {H - s(24)}"

    for idx, story in enumerate(ALL_STORIES):
        col, row = idx % cols, idx // cols
        x0 = margin + col * (card_w + gap)
        y0 = grid_y + row * (card_h + gap)
        x1, y1 = x0 + card_w, y0 + card_h
        outline = AMBER if story.lead else HAIR
        border = s(2) if story.lead else s(1)
        c.rect((x0, y0, x1, y1), fill=CARD, outline=outline, width=border,
               radius=s(5))
        c.rect((x0, y0 + s(3), x0 + s(3), y1 - s(3)),
               fill=REGION_COLORS[story.region])
        draw_card(c, story, x0 + s(6), y0 + card_pad_v,
                  x1 - s(6), y1 - card_pad_v,
                  head_font=head_font, region_font=region_font,
                  place_font=place_font, line_h=line_h,
                  head_lines_max=head_lines_max, inner_w=inner_w,
                  prefix=story.sid)

    # ---- footer ----
    foot_font = font(s(19), False)
    foot = "SOURCES: WIRE REPORTS · 26-27 NOV 2026 · ALL TIMES UTC"
    assert fit_text(foot, foot_font, W - s(40)), "footer too wide"
    c.text((s(24), H - s(18)), foot, foot_font, MUTED, name="footer")

    return c.im


def draw_card(c: Canvas, story: Story, x0: int, y0: int, x1: int, y1: int,
              head_font: ImageFont.FreeTypeFont,
              region_font: ImageFont.FreeTypeFont,
              place_font: ImageFont.FreeTypeFont,
              line_h: int, head_lines_max: int, inner_w: int,
              prefix: str) -> None:
    """Draw one story card: region chip, place, headline; all measured."""
    card_bounds = (x0 - s(4), y0, x1 + s(4), y1)
    c.text((x0, y0), story.region, region_font, REGION_COLORS[story.region],
           bounds=card_bounds, name=prefix + "-region")
    c.text((x0, y0 + line_h), place_label(story), place_font, MUTED,
           bounds=card_bounds, name=prefix + "-place")

    head_lines = wrap_words(story.headline, head_font, inner_w)
    head_lines = balance_two(head_lines, head_font, inner_w)
    assert 1 <= len(head_lines) <= head_lines_max, \
        f"{prefix}: {len(head_lines)} headline lines > {head_lines_max}: {story.headline!r}"
    yy = y0 + 2 * line_h + s(2)
    for i, line in enumerate(head_lines):
        assert fit_text(line, head_font, inner_w), \
            f"{prefix}: headline line too wide: {line!r}"
        c.text((x0, yy), line, head_font, WHITE,
               bounds=card_bounds, name=f"{prefix}-head{i}")
        yy += line_h
    assert yy - line_h <= y1, f"{prefix}: headline overflows card"



def validate_data() -> None:
    ids = [st.sid for st in ALL_STORIES]
    assert len(ALL_STORIES) == 32, f"expected 32 stories, got {len(ALL_STORIES)}"
    assert len(LEADS) == 8 and len(BRIEFS) == 24
    assert len(set(ids)) == 32, "duplicate story ids"
    assert all(st.lead for st in LEADS) and all(not st.lead for st in BRIEFS)
    regions = {st.region for st in ALL_STORIES}
    assert regions == {"EUROPE", "AMERICAS", "ASIA-PACIFIC", "AFRICA",
                       "MIDDLE EAST", "OCEANIA"}, regions
    for st in ALL_STORIES:
        assert st.headline and st.place and st.region and st.summary


def main() -> None:
    validate_data()
    big = draw_poster()
    assert big.size == (W, H)
    final = big.resize((SIZE, SIZE), Image.LANCZOS)
    final.save("entry.png", format="PNG", optimize=False)
    print("ALL LAYOUT CHECKS PASSED")


if __name__ == "__main__":
    main()
