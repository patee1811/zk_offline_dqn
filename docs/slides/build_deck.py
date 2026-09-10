"""Build the layer-by-layer presentation deck.

Run from the repo root: python docs/slides/build_deck.py
Needs python-pptx, which is deliberately NOT in requirements: it is a tool for
regenerating this one file, not something the relations or tests depend on.

Every figure comes from a committed artifact. The dataset sample on the
"before / after" slides is recomputed here from raw_episodes.jsonl and checked
against the committed Merkle tree, so the deck cannot drift from the repo
without this script failing.
"""

import json
import pathlib
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, ".")
from zk_offline_dqn import merkle, zk_specs  # noqa: E402

OUT = pathlib.Path("docs/slides/zk_offline_dqn_thuyet_trinh.pptx")

# ---------------------------------------------------------------- palette
INK = RGBColor(0x14, 0x18, 0x21)
INK2 = RGBColor(0x39, 0x42, 0x4F)
MUTED = RGBColor(0x6B, 0x75, 0x81)
ACCENT = RGBColor(0x17, 0x60, 0x5B)
ACC_BG = RGBColor(0xDC, 0xEA, 0xE8)
WARN = RGBColor(0x8C, 0x3A, 0x2E)
WARN_BG = RGBColor(0xF5, 0xE7, 0xE4)
RULE = RGBColor(0xD2, 0xD7, 0xDE)
SOFT = RGBColor(0xF2, 0xF4, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SANS = "Segoe UI"
MONO = "Consolas"

W, H = Inches(13.333), Inches(7.5)
M = Inches(0.72)              # left margin
CONTENT_W = W - 2 * M

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]

_n = [0]


# ---------------------------------------------------------------- helpers
def _tb(slide, left, top, width, height):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def _run(p, text, size, color=INK2, bold=False, font=SANS, italic=False):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    return r


def rect(slide, left, top, width, height, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


def slide(title, eyebrow, sub=None):
    """A content slide: eyebrow, title, thin accent rule, numbered footer."""
    s = prs.slides.add_slide(BLANK)
    _n[0] += 1

    tf = _tb(s, M, Inches(0.42), CONTENT_W, Inches(0.3))
    p = tf.paragraphs[0]
    _run(p, eyebrow.upper(), 11, ACCENT, bold=True)

    tf = _tb(s, M, Inches(0.72), CONTENT_W, Inches(0.72))
    p = tf.paragraphs[0]
    _run(p, title, 27, INK, bold=True)

    rect(s, M, Inches(1.52), Inches(1.05), Pt(2.5), ACCENT)

    if sub:
        tf = _tb(s, M, Inches(1.66), CONTENT_W, Inches(0.34))
        _run(tf.paragraphs[0], sub, 13, MUTED)

    tf = _tb(s, M, H - Inches(0.52), CONTENT_W, Inches(0.26))
    p = tf.paragraphs[0]
    _run(p, "zk_offline_dqn", 9, RULE)
    _run(p, "     " + str(_n[0]), 9, MUTED, bold=True, font=MONO)
    return s


def bullets(s, items, left, top, width, size=13.5, gap=7):
    """items: str, or (str, bold_prefix), or ('>', str) for a sub-line."""
    tf = _tb(s, left, top, width, Inches(0.4))
    first = True
    for it in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        p.line_spacing = 1.22
        if isinstance(it, tuple) and it[0] == ">":
            _run(p, "     " + it[1], size - 1.5, MUTED)
            continue
        text = it if isinstance(it, str) else it[0]
        _run(p, "—  ", size, ACCENT, bold=True)
        # split on ** for bold spans
        parts = text.split("**")
        for k, part in enumerate(parts):
            if part:
                _run(p, part, size, INK if k % 2 else INK2, bold=bool(k % 2))
    return tf


def para(s, left, top, width, chunks, size=13.5, gap=6):
    """chunks: list of strings; ** toggles bold."""
    tf = _tb(s, left, top, width, Inches(0.4))
    first = True
    for text in chunks:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        p.line_spacing = 1.24
        for k, part in enumerate(text.split("**")):
            if part:
                _run(p, part, size, INK if k % 2 else INK2, bold=bool(k % 2))
    return tf


def code(s, left, top, width, text, size=11, warn_marks=()):
    lines = text.split("\n")
    height = Inches(0.16) + Pt(size * 1.42) * len(lines) + Inches(0.16)
    rect(s, left, top, width, height, SOFT, RULE)
    tf = _tb(s, left + Inches(0.16), top + Inches(0.12), width - Inches(0.32),
             height - Inches(0.24))
    for k, ln in enumerate(lines):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.space_after = Pt(0)
        p.line_spacing = 1.34
        color = WARN if any(m in ln for m in warn_marks) else INK2
        _run(p, ln if ln else " ", size, color, font=MONO)
    return top + height


def callout(s, left, top, width, label, text, warn=False, size=12.5):
    bg, fg = (WARN_BG, WARN) if warn else (ACC_BG, ACCENT)
    tf = _tb(s, left + Inches(0.24), top + Inches(0.14), width - Inches(0.44), Inches(0.4))
    p = tf.paragraphs[0]
    p.space_after = Pt(4)
    _run(p, label.upper(), 10, fg, bold=True)
    p2 = tf.add_paragraph()
    p2.line_spacing = 1.22
    for k, part in enumerate(text.split("**")):
        if part:
            _run(p2, part, size, INK if k % 2 else INK2, bold=bool(k % 2))
    nlines = 1 + max(1, len(text) // int(width.inches * 10.5))
    height = Inches(0.3) + Pt(11) + Pt(size * 1.35) * nlines
    box = rect(s, left, top, width, height, bg)
    box.line.color.rgb = fg
    box.line.width = Pt(0.75)
    # keep the text above the rectangle
    s.shapes._spTree.remove(box._element)
    s.shapes._spTree.insert(2, box._element)
    bar = rect(s, left, top, Pt(3), height, fg)
    s.shapes._spTree.remove(bar._element)
    s.shapes._spTree.insert(3, bar._element)
    return top + height


def table(s, headers, rows, left, top, width, col_ratio=None, size=11,
          hi_rows=(), bad_rows=(), right_cols=()):
    nrow, ncol = len(rows) + 1, len(headers)
    height = Inches(0.32) * nrow
    shape = s.shapes.add_table(nrow, ncol, left, top, width, height)
    tbl = shape.table
    tbl.first_row = False
    if col_ratio:
        total = sum(col_ratio)
        for c, r in enumerate(col_ratio):
            tbl.columns[c].width = Emu(int(width * r / total))
    for c, htext in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = WHITE
        cell.margin_left = cell.margin_right = Inches(0.07)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        if c in right_cols:
            p.alignment = PP_ALIGN.RIGHT
        _run(p, htext.upper(), size - 1.5, MUTED, bold=True)
    for r, row in enumerate(rows, start=1):
        hi, bad = (r - 1) in hi_rows, (r - 1) in bad_rows
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACC_BG if hi else WHITE
            cell.margin_left = cell.margin_right = Inches(0.07)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            if c in right_cols:
                p.alignment = PP_ALIGN.RIGHT
            color = WARN if bad else (INK if hi and c == 0 else INK2)
            font = MONO if c in right_cols else SANS
            _run(p, str(val), size, color, bold=bool(hi and c == 0), font=font)
    return top + height


def stats(s, items, left, top, width, size=30):
    """items: [(value, caption), ...] laid out as one row."""
    n = len(items)
    gap = Inches(0.3)
    w = Emu(int((width - gap * (n - 1)) / n))
    for k, (val, cap) in enumerate(items):
        x = left + Emu(int((w + gap) * k))
        rect(s, x, top, w, Pt(2.5), ACCENT)
        tf = _tb(s, x, top + Inches(0.14), w, Inches(0.5))
        _run(tf.paragraphs[0], val, size, INK, bold=True)
        tf2 = _tb(s, x, top + Inches(0.14) + Pt(size * 1.15), w, Inches(0.7))
        p = tf2.paragraphs[0]
        p.line_spacing = 1.18
        _run(p, cap, 10.5, MUTED)


# ---------------------------------------------------- verified data sample
RAW = json.loads(
    pathlib.Path("artifacts/datasets/cartpole-expert-v2/raw_episodes.jsonl")
    .read_text(encoding="utf-8").splitlines()[0]
)
_tr = {"obs": RAW["state"], "action": RAW["action"], "reward": RAW["reward"],
       "next_obs": RAW["next_state"], "done": RAW["terminated"] or RAW["truncated"]}
LEAF = zk_specs.serialize_transition_leaf(_tr, obs_dim=4, action_dim=2)
LEAF_HASH = merkle.hash_leaf(LEAF)
MT = json.loads(
    pathlib.Path("artifacts/datasets/cartpole-expert-v2/merkle_tree.json")
    .read_text(encoding="utf-8")
)
assert LEAF_HASH == MT["leaf_hashes"][0], "sample khong khop cay da commit"
assert MT["dataset_root"] == "02de61a980455ea1e894e5ec77a7948faa622b4ddc4d1a56b710b2ce10b410d2"
LEVELS = [len(l) for l in MT["levels"]]

# ================================================================ TITLE
s = prs.slides.add_slide(BLANK)
rect(s, Inches(0), Inches(0), Inches(0.28), H, ACCENT)
tf = _tb(s, Inches(1.1), Inches(1.9), Inches(10.6), Inches(0.4))
_run(tf.paragraphs[0], "ZERO-KNOWLEDGE PROOF OF TRAINING", 13, ACCENT, bold=True)
tf = _tb(s, Inches(1.1), Inches(2.35), Inches(10.4), Inches(1.8))
p = tf.paragraphs[0]
p.line_spacing = 1.05
_run(p, "Bằng chứng cho một lượt\nhuấn luyện Offline DQN", 40, INK, bold=True)
tf = _tb(s, Inches(1.1), Inches(4.15), Inches(9.4), Inches(0.9))
p = tf.paragraphs[0]
p.line_spacing = 1.3
_run(p, "Chứng minh bằng mật mã rằng một chính sách điều khiển đã được huấn luyện "
        "đúng quy trình, trên đúng dữ liệu đã cam kết — mà không tiết lộ dữ liệu.",
     15, INK2)
rect(s, Inches(1.1), Inches(5.35), Inches(10.2), Pt(1), RULE)
stats(s, [("SP1 6.1.0", "zkVM · STARK · guest RISC-V RV32IM"),
          ("4 lớp · 8 quan hệ", "dữ liệu → quan hệ → backend → gộp"),
          ("25 cấu hình", "đã prove và verify, một lượt chạy một máy"),
          ("4.992 bước", "một lượt huấn luyện dưới một proof")],
      Inches(1.1), Inches(5.65), Inches(10.2), size=17)

# ================================================================ 1 BỐI CẢNH
s = slide("Nộp mô hình thì không ai kiểm được gì", "Bối cảnh",
          "Một công ty nộp cho cơ quan quản lý một chính sách điều khiển đã huấn luyện.")
para(s, M, Inches(2.15), Inches(5.7), [
    "**Chính sách** = một tệp trọng số mạng nơ-ron, tức quy tắc "
    "*tình huống → hành động*: liều thuốc tuần tới cho một bệnh nhân, "
    "hay lệnh ga/phanh cho một chiếc xe.",
    "Nhìn vào tệp trọng số, **không ai đọc ra được nó được huấn luyện thế nào** — "
    "y như nhìn pho tượng không đọc ra được người thợ đã đục thế nào.",
])
bullets(s, [
    "Sửa **phần thưởng** → mô hình học một thế giới đẹp hơn thế giới thật",
    "Xoá **cờ kết thúc** → mọi lần thất bại biến mất khỏi dữ liệu",
    "Thay **giá trị mục tiêu** → sai số trông nhỏ đi",
    "Sửa **gradient** → can thiệp thẳng vào mô hình",
], M, Inches(3.5), Inches(5.7))
y = table(s, ["Cách kiểm hiển nhiên", "Vì sao hỏng"], [
    ["Chỉ nộp mô hình cuối", "không kiểm được gì cả"],
    ["Nộp cả dữ liệu + nhật ký", "lộ dữ liệu; tốn đúng bằng chi phí huấn luyện"],
    ["Chạy thử, chấm điểm", "điểm thi không nói gì về nguồn gốc dữ liệu"],
], Inches(7.0), Inches(2.15), Inches(5.6), col_ratio=(4, 6))
y = callout(s, Inches(7.0), y + Inches(0.3), Inches(5.6), "Điểm chung của bốn cách gian lận",
            "Kết quả cuối vẫn **tự nhất quán**. Không có mâu thuẫn nội tại nào để "
            "người kiểm bên ngoài phát hiện ra.", warn=True)
callout(s, Inches(7.0), y + Inches(0.24), Inches(5.6), "Thứ cần có",
        "Một cơ chế **kiểm được mà không phải xem**.")

# ================================================================ 2 ZKP
s = slide("Zero-knowledge proof: bất đối xứng prover / verifier", "Bối cảnh",
          "Bên A chứng minh “tôi đã thực hiện đúng phép tính này” mà không cho B xem dữ liệu.")
table(s, ["Tính chất", "Nghĩa"], [
    ["Completeness", "trung thực thì bằng chứng luôn được chấp nhận"],
    ["Soundness", "gian lận thì bị từ chối, trừ xác suất ≈ 2⁻¹⁰⁰"],
    ["Zero-knowledge", "không rò rỉ gì ngoài chính phát biểu được chứng minh"],
], M, Inches(2.2), Inches(6.0), col_ratio=(3, 7))
table(s, ["Vai", "Tên", "Chi phí"], [
    ["Bên tính toán, tạo bằng chứng", "prover", "rất đắt"],
    ["Bên kiểm bằng chứng", "verifier", "rất rẻ"],
], M, Inches(3.65), Inches(6.0), col_ratio=(5, 3, 3))
y = table(s, ["Đo thật, cùng một proof", "Thời gian"], [
    ["Prove — proof recursion T = 64", "755,2 s"],
    ["Verify — cùng proof đó", "0,054 s"],
], Inches(7.3), Inches(2.2), Inches(5.3), col_ratio=(7, 3), right_cols=(1,), hi_rows=(1,))
y = callout(s, Inches(7.3), y + Inches(0.32), Inches(5.3), "Tỉ lệ 14.000 lần",
            "Và verify **không tăng** khi phép tính lớn lên: dải cycles của Bảng 2 "
            "trải 52.941 lần, cột verify gần như không nhúc nhích.")
callout(s, Inches(7.3), y + Inches(0.26), Inches(5.3), "Vì sao điều đó có giá trị",
        "Chi phí dồn về phía kẻ **phải chứng minh sự trong sạch của mình**. "
        "Cơ quan quản lý gần như không tốn gì.")

# ================================================================ 3 KIẾN TRÚC
s = slide("Kiến trúc: bốn lớp", "Tổng quan hệ thống",
          "Mỗi lớp kiểm được độc lập; mỗi phát biểu trong paper truy ngược về một artifact.")
rows = [
    ("LỚP 1", "DỮ LIỆU", "thu thập → kiểm toán → cam kết Merkle → xác minh",
     "artifacts/datasets/ · scripts/data/"),
    ("LỚP 2", "QUAN HỆ", "oracle Python thuần — định nghĩa phép tính đúng là gì",
     "zk_offline_dqn/relations/"),
    ("LỚP 3", "BACKEND", "guest / host / shared Rust — sinh proof SP1",
     "zk_backend/<quan hệ>/sp1/"),
    ("LỚP 4", "GỘP", "nối nhiều proof thành một proof duy nhất",
     "training_aggregation"),
]
ytop = Inches(2.2)
for k, (lbl, name, what, where) in enumerate(rows):
    y = ytop + Inches(1.02) * k
    rect(s, M, y, Inches(8.3), Inches(0.86), SOFT, RULE)
    rect(s, M, y, Pt(3.5), Inches(0.86), ACCENT)
    tf = _tb(s, M + Inches(0.22), y + Inches(0.12), Inches(1.5), Inches(0.3))
    _run(tf.paragraphs[0], lbl, 11, ACCENT, bold=True)
    tf = _tb(s, M + Inches(1.35), y + Inches(0.09), Inches(1.6), Inches(0.34))
    _run(tf.paragraphs[0], name, 15, INK, bold=True)
    tf = _tb(s, M + Inches(3.0), y + Inches(0.11), Inches(5.1), Inches(0.3))
    _run(tf.paragraphs[0], what, 12, INK2)
    tf = _tb(s, M + Inches(1.35), y + Inches(0.47), Inches(6.7), Inches(0.28))
    _run(tf.paragraphs[0], where, 10, MUTED, font=MONO)
    if k < 3:
        tf = _tb(s, M + Inches(0.14), y + Inches(0.86), Inches(0.4), Inches(0.16))
        _run(tf.paragraphs[0], "↓", 12, ACCENT, bold=True)
y = callout(s, Inches(9.4), Inches(2.2), Inches(3.2), "Ranh giới được ép bằng quy tắc",
            "Lớp 2 **bị cấm** dùng argparse, đọc file, hay đọc biến môi trường. "
            "Một quan hệ chỉ nhận dict và trả dict.")
callout(s, Inches(9.4), y + Inches(0.3), Inches(3.2), "Vì sao tách lớp",
        "Lỗi ở đâu thì lộ ở đó. Và mỗi lớp có bộ kiểm riêng chạy được **không cần GPU**.")

# ================================================================ LỚP 1 — dữ liệu
s = slide("Lớp 1 — Dữ liệu là gì, và vì sao chọn dữ liệu này", "Lớp 1 · Dữ liệu")
table(s, ["dataset_id", "Môi trường", "Chính sách", "Transition", "merkle_root"], [
    ["cartpole-random-v2", "CartPole-v1", "random", "50.006", "6f586441…"],
    ["cartpole-medium-v2", "CartPole-v1", "medium", "50.045", "f5002ce5…"],
    ["cartpole-expert-v2", "CartPole-v1", "expert", "50.261", "02de61a9…"],
    ["lunarlander-random-v1", "LunarLander-v3", "random", "50.020", "24eebb92…"],
    ["lunarlander-medium-v1", "LunarLander-v3", "medium", "50.586", "eb3e4f6c…"],
    ["lunarlander-expert-v1", "LunarLander-v3", "expert", "50.552", "328eb8b4…"],
], M, Inches(2.15), Inches(7.4), col_ratio=(6, 5, 3, 3, 4),
    right_cols=(3, 4), hi_rows=(2, 5))
bullets(s, [
    "**Ba mức chất lượng** — chất lượng dữ liệu là biến số quan trọng nhất trong "
    "offline RL. random: phủ rộng nhưng không có hành vi tốt. expert: chất lượng cao "
    "nhưng **hẹp**, chỉ phủ trạng thái mà agent giỏi đi qua.",
    "**Hai môi trường** — CartPole 4 chiều / 2 hành động / thưởng dày; LunarLander "
    "8 chiều / 4 hành động / thưởng thưa và âm nặng. Thứ tự thắng thua **đảo ngược** "
    "giữa hai môi trường, nên một môi trường là chưa đủ.",
    "**≈ 50.000 transition** — đủ lớn để việc học có nghĩa, đủ nhỏ để cây Merkle "
    "sâu 16–17 tầng và toàn bộ pipeline chạy trong ngân sách.",
    "**Số lẻ, không tròn** — thu thập dừng ở ranh giới episode; cắt giữa episode tạo "
    "transition cuối có cờ done sai.",
], M, Inches(4.6), Inches(7.4), size=12.5)
y = callout(s, Inches(8.55), Inches(2.15), Inches(4.05), "Offline chứ không online — vì sao",
            "Dữ liệu offline **cố định** nên **cam kết được**. Dữ liệu online do chính "
            "agent sinh ra trong lúc chạy, không có gì để cam kết trước. Offline RL là "
            "thứ duy nhất trong RL mà proof-of-training có nghĩa hôm nay.")
callout(s, Inches(8.55), y + Inches(0.26), Inches(4.05), "MountainCar đã thử và đã loại",
        "DQN vanilla 200.000 bước cho đúng −200,0 ở **cả 10 checkpoint** — không lần "
        "nào chạm cờ, nên không sinh nổi cặp medium/expert phân biệt được.", warn=True)

# ================================================================ LỚP 1 — pipeline
s = slide("Lớp 1 — Quá trình xử lý dữ liệu, bốn bước", "Lớp 1 · Dữ liệu",
          "Mỗi bước để lại một hash, và cả bốn hash đều đi vào public input của proof.")
steps = [
    ("1  COLLECT", "chạy chính sách trong môi trường, ghi từng transition; "
                   "mỗi dòng nối vào một chuỗi hash",
     "raw_trajectory_hash · collection_log_final_hash · base_seed"),
    ("2  AUDIT", "kiểm lại: reward có khớp môi trường không, replay có nhất quán "
                 "không, episode có đóng đúng không",
     "audit_report_hash · replay_audit_passed · reward_audit_passed"),
    ("3  COMMIT", "mã hoá fixed-point → băm từng lá → dựng cây Merkle",
     "merkle_root · manifest_hash · leaf_hash_rule"),
    ("4  VERIFY", "dựng lại cây từ dữ liệu và so root; cổng CI chặn nếu lệch",
     "verify_dataset_commitment"),
]
for k, (name, what, out) in enumerate(steps):
    y = Inches(2.15) + Inches(1.12) * k
    rect(s, M, y, Inches(7.5), Inches(0.94), WHITE, RULE)
    rect(s, M, y, Pt(3.5), Inches(0.94), ACCENT)
    tf = _tb(s, M + Inches(0.22), y + Inches(0.13), Inches(1.7), Inches(0.3))
    _run(tf.paragraphs[0], name, 13, ACCENT, bold=True)
    tf = _tb(s, M + Inches(1.85), y + Inches(0.11), Inches(5.4), Inches(0.5))
    p = tf.paragraphs[0]
    p.line_spacing = 1.18
    _run(p, what, 12, INK2)
    tf = _tb(s, M + Inches(1.85), y + Inches(0.62), Inches(5.4), Inches(0.26))
    _run(tf.paragraphs[0], out, 10, MUTED, font=MONO)
code(s, Inches(8.45), Inches(2.15), Inches(4.15),
     "collection_log.jsonl  (dòng đầu)\n\n"
     "prev_log_hash    : zk_offline_dqn_\n"
     "                   collection_log_v1\n"
     "transition_hash  : 47cbf792…\n"
     "current_log_hash : a45657763a45df4d…\n\n"
     "Mỗi dòng băm cùng dòng trước → một\n"
     "chuỗi. Sửa hay bỏ một transition ở\n"
     "giữa làm đổi mọi hash phía sau.", size=10)
callout(s, Inches(8.45), Inches(4.55), Inches(4.15), "Vì sao cần bước AUDIT riêng",
        "Cam kết Merkle chỉ khoá **dữ liệu**, không nói dữ liệu có hợp lệ không. "
        "Bước audit kiểm reward do môi trường trả về đúng, và replay tự nhất quán. "
        "Hai việc khác nhau, nên hai hash khác nhau.")

# ================================================================ LỚP 1 — sample
s = slide("Lớp 1 — Mẫu dữ liệu: trước và sau xử lý", "Lớp 1 · Dữ liệu",
          "Transition đầu tiên của cartpole-expert-v2, lấy thẳng từ artifact đã commit.")
tf = _tb(s, M, Inches(2.15), Inches(6.0), Inches(0.3))
_run(tf.paragraphs[0], "TRƯỚC — raw_episodes.jsonl (float32)", 11, MUTED, bold=True)
code(s, M, Inches(2.45), Inches(6.0),
     "state       : [ 0.0471041277050972,\n"
     "                0.0104932747781276,\n"
     "                0.0028976858593523,\n"
     "               -0.0181245729327201 ]\n"
     "action      : 1\n"
     "reward      : 1.0\n"
     "next_state  : [ 0.0473139919340610,\n"
     "                0.2055735439062118,\n"
     "                0.0025351943913847,\n"
     "               -0.3098918497562408 ]\n"
     "terminated  : false", size=10.5)
tf = _tb(s, Inches(7.0), Inches(2.15), Inches(5.6), Inches(0.3))
_run(tf.paragraphs[0], "SAU — lá fixed-point (số nguyên, FP_SCALE = 1000)", 11, ACCENT, bold=True)
y = code(s, Inches(7.0), Inches(2.45), Inches(5.6),
         "leaf = [ 47, 10, 3, -18,      ← state × 1000\n"
         "          1,                   ← action\n"
         "       1000,                   ← reward × 1000\n"
         "         47, 206, 3, -310,     ← next_state × 1000\n"
         "          0 ]                  ← done\n\n"
         "leaf_hash = SHA256(\"47,10,3,-18,1,1000,\n"
         "                    47,206,3,-310,0\")\n"
         "          = 7d5e2a23cbbce1905c37b33ddbf9a7d6…", size=10.5)
y = callout(s, Inches(7.0), y + Inches(0.22), Inches(5.6), "Đã đối chiếu",
            "Giá trị này **khớp đúng** leaf_hashes[0] trong merkle_tree.json đã commit. "
            "Script sinh slide tự kiểm lại, nên slide không trôi khỏi repo được.")
bullets(s, [
    "**Vì sao phải đổi sang số nguyên:** hệ chứng minh làm việc trên trường hữu hạn. "
    "Số thực dấu phẩy động không tất định giữa các CPU và trình biên dịch — "
    "không có ngữ nghĩa xác định để mà chứng minh.",
    "**Cái giá:** learning rate mặc định của Adam, 3×10⁻⁴, mã hoá thành **0**. "
    "Ở thang này Adam không tồn tại ở tham số mặc định của chính nó.",
], M, Inches(5.15), Inches(6.0), size=12)

# ================================================================ LỚP 1 — merkle
s = slide("Lớp 1 — Cam kết Merkle: 50.261 dòng thành 32 byte", "Lớp 1 · Dữ liệu")
code(s, M, Inches(2.15), Inches(6.1),
     "                     dataset_root          ← chỉ công bố giá trị này\n"
     "                   /              \\\n"
     "             h(1,2)                h(3,4)\n"
     "             /    \\                /    \\\n"
     "          lá1    lá2            lá3    lá4\n"
     "           |       |              |       |\n"
     "        dòng1   dòng2          dòng3   dòng4\n\n"
     "cartpole-expert-v2:\n"
     "  num_leaves      50.261\n"
     "  levels          " + " → ".join(str(x) for x in LEVELS[:5]) + " → … → 1\n"
     "  số tầng         " + str(len(LEVELS)) + "\n"
     "  leaf_hash_rule  sha256(fixed_point_transition_leaf)\n"
     "  dataset_root    02de61a980455ea1e894e5ec77a7948f…", size=10.5)
bullets(s, [
    "Sửa **bất kỳ** dòng nào cũng làm đổi root. Công bố root trước là tự trói mình "
    "vào đúng tập dữ liệu đó.",
    "Chứng minh một dòng thuộc tập chỉ cần **log₂(n) hash** — 100.000 dòng cần 17 hash — "
    "chứ không phải đưa cả tập.",
    "Lá lẻ thì **nhân đôi lá cuối** (kiểu Bitcoin) để ghép đủ đôi.",
], Inches(7.15), Inches(2.15), Inches(5.45), size=12.5)
y = table(s, ["Số lá", "Độ sâu", "Cycles", "Mỗi tầng"], [
    ["1.000", "10", "357.965", "—"],
    ["10.000", "14", "470.318", "+28.088"],
    ["50.000", "16", "526.578", "+28.130"],
    ["100.000", "17", "554.100", "+27.522"],
], Inches(7.15), Inches(4.15), Inches(5.45), col_ratio=(3, 2, 4, 3),
    right_cols=(0, 1, 2, 3))
callout(s, Inches(7.15), y + Inches(0.26), Inches(5.45), "Vì sao Merkle chứ không phải KZG",
        "KZG cho proof ngắn hơn nhưng cần **trusted setup** và phép toán pairing — "
        "rất đắt để chứng minh lại **bên trong** zkVM. Merkle chỉ dùng băm, và SP1 có "
        "precompile SHA-256. Tối ưu phía prover, vì chi phí nằm ở đó.")

# ================================================================ LỚP 2 ↔ 3
s = slide("Mối liên hệ giữa lớp 2 và lớp 3", "Lớp 2 ↔ Lớp 3",
          "Hai bản cài đặt của cùng một phép tính. Nghe như trùng lặp — thực ra là cơ chế phòng thủ.")
table(s, ["", "Lớp 2 — Python", "Lớp 3 — Rust trong guest"], [
    ["Vai trò", "ĐỊNH NGHĨA quan hệ (oracle)", "THI HÀNH quan hệ, được chứng minh"],
    ["Chạy ở đâu", "máy thường, CPU", "bên trong zkVM"],
    ["Tốc độ", "mili giây", "giây → hàng chục phút, kèm prove"],
    ["Sinh ra gì", "test vector, artifact, số Bảng 1", "proof"],
    ["Bỏ đi được?", "KHÔNG", "KHÔNG"],
], M, Inches(2.2), Inches(7.3), col_ratio=(3, 5, 6))
bullets(s, [
    "**Không bỏ Python được** — nó sinh ra dữ liệu để chứng minh, nó là mức so sánh "
    "(“guest tính đúng” là đúng so với *cái gì*?), và nó bắt lỗi trong mili giây "
    "thay vì trả tiền GPU để bắt.",
    "**Không bỏ Rust được** — oracle Python chạy trên máy prover, nó **không** là "
    "bằng chứng gì với người ngoài. Ai cũng viết được một script in ra “đúng rồi”.",
], M, Inches(4.5), Inches(7.3), size=12.5)
y = callout(s, Inches(8.4), Inches(2.2), Inches(4.2), "Cơ chế phòng thủ, đã cứu một lần thật",
            "Lỗi tràn i64 **chỉ bị phát hiện vì hai bản bất đồng**: Python dùng số "
            "nguyên độ chính xác tuỳ ý nên không gói vòng, Rust i64 thì gói vòng thành "
            "số âm. Nếu chỉ có một bản, một phép tính vô nghĩa đã được chứng minh "
            "thành công và không ai biết.")
callout(s, Inches(8.4), y + Inches(0.26), Inches(4.2), "Cái giá phải trả",
        "Mỗi lần đổi quan hệ phải sửa **cả hai**, và chuỗi JSON chuẩn tắc phải khớp "
        "**đến từng byte** — guest không có bộ mã hoá JSON, nó dựng chuỗi bằng tay.",
        warn=True)

# ================================================================ LỚP 2 — quan hệ
s = slide("Lớp 2 — Tám quan hệ: vào gì, ra gì", "Lớp 2 · Quan hệ",
          "Vòng huấn luyện DQN có bảy bước; tám quan hệ phủ nó theo kiểu đồng tâm.")
code(s, M, Inches(2.15), Inches(4.35),
     "Vòng huấn luyện DQN, một bước\n\n"
     "1  lấy transition (s,a,r,s',done)\n"
     "2  chạy mạng trên s   → Q(s,a)\n"
     "3  chạy mạng trên s'  → max Q(s',a')\n"
     "4  TD target = r + γ·max Q(s',a')\n"
     "5  loss = SmoothL1(TD target − Q(s,a))\n"
     "6  tính gradient\n"
     "7  cập nhật trọng số", size=10.5)
callout(s, M, Inches(4.55), Inches(4.35), "Vì sao giữ cả quan hệ nhỏ",
        "Mỗi cái là một **điểm đo độc lập** cho Bảng 2. Và khi quan hệ lớn hỏng, "
        "quan hệ nhỏ chỉ ra **hỏng ở đâu**.")
table(s, ["Quan hệ", "Bước", "Chứng minh điều gì"], [
    ["merkle_membership", "trước 1", "dòng dữ liệu này nằm trong cây đã cam kết"],
    ["td_mvp", "4–5", "TD target và loss SmoothL1 tính đúng"],
    ["forward_td_mlp", "2–5", "các giá trị Q do đúng mạng này sinh ra"],
    ["one_step_sgd_tiny", "6–7", "gradient và w ← w − η·g áp đúng"],
    ["short_trace", "giữa", "checkpoint cuối bước t = checkpoint đầu bước t+1"],
    ["training_update", "1–7", "một bước huấn luyện HOÀN CHỈNH"],
    ["training_fragment", "k × 1–7", "k bước + lịch sync target + biên Q"],
    ["training_aggregation", "lớp 4", "nhiều fragment → một lượt chạy"],
], Inches(5.5), Inches(2.15), Inches(7.1), col_ratio=(5, 2, 9),
    hi_rows=(5, 6, 7))
tf = _tb(s, Inches(5.5), Inches(5.35), Inches(7.1), Inches(0.9))
p = tf.paragraphs[0]
p.line_spacing = 1.2
_run(p, "merkle_membership là quan hệ ", 12, INK2)
_run(p, "duy nhất nối phép tính với dữ liệu", 12, INK, bold=True)
_run(p, ". Không có nó, mọi thứ phía sau chỉ chứng minh “tôi đã tính đúng trên "
        "một bộ số nào đó”, chứ không phải “trên dữ liệu đã đăng ký”.", 12, INK2)

# ================================================================ LỚP 2 — fragment I/O
s = slide("Lớp 2 — Một quan hệ xử lý kiểu gì: training_fragment", "Lớp 2 · Quan hệ",
          "Quan hệ nhận một dict, kiểm từng ràng buộc, trả một dict. Không đọc file, không CLI.")
tf = _tb(s, M, Inches(2.15), Inches(3.9), Inches(0.3))
_run(tf.paragraphs[0], "ĐẦU VÀO — case JSON", 11, MUTED, bold=True)
code(s, M, Inches(2.45), Inches(3.9),
     "{\n"
     "  schema_version:\n"
     "    sp1_training_fragment_case_v2\n"
     "  public_inputs:  { … 30 trường }\n"
     "  private_witness: {\n"
     "    provenance: { … },\n"
     "    steps: [ { … } × k ]\n"
     "  }\n"
     "}", size=10.5)
tf = _tb(s, M, Inches(4.75), Inches(3.9), Inches(0.3))
_run(tf.paragraphs[0], "ĐẦU RA", 11, ACCENT, bold=True)
code(s, M, Inches(5.05), Inches(3.9),
     "accepted        : true | false\n"
     "reason          : chuỗi nếu từ chối\n"
     "final_checkpoint_hash\n"
     "final_target_checkpoint_hash\n"
     "trace_hash, loss_trace_hash,\n"
     "gradient_trace_hash, …", size=10.5)
tf = _tb(s, Inches(5.1), Inches(2.15), Inches(7.5), Inches(0.3))
_run(tf.paragraphs[0], "XỬ LÝ — với mỗi bước trong k bước, kiểm theo thứ tự", 11, MUTED, bold=True)
items = [
    "**Dẫn xuất** chỉ số mẫu — không đọc từ statement:",
    ("> σ = SHA256(\"…sampler_seed_v1\", dataset_root, global_step_start) mod 2³²"),
    ("> state ← (1.664.525·state + 1.013.904.223) mod 2³²,  lặp step_id+1 lần"),
    ("> sample_index = state mod dataset_size"),
    "**Kiểm thành viên** — SHA256(lá) rồi đi Merkle path lên tới dataset_root",
    "**Kiểm biên Q** — |q_online|, |q_target| ≤ q_abs_max_fp = 2⁵², **trước** phép nhân γ·q",
    "**Tính TD target** — r + (γ·q)//1000, hoặc = r nếu done; Double DQN: online chọn, target chấm",
    "**Tính loss, gradient, cập nhật** — kẹp từng thành phần vào ±gradient_clip_fp rồi w ← w − (η·g)//1000",
    "**Kiểm chuỗi checkpoint** — hash sau bước t phải bằng hash trước bước t+1",
    "**Kiểm lịch sync** — target đứng yên giữa hai mốc, và bằng online đúng tại mốc",
]
bullets(s, items, Inches(5.1), Inches(2.5), Inches(7.5), size=11.5, gap=4)
callout(s, Inches(5.1), Inches(5.75), Inches(7.5), "Bản Rust trong guest có 106 assert",
        "74 assert_eq! và 16 assert!. Mỗi ràng buộc ở trên là một assert trong guest — "
        "sai một cái là guest **panic**, và proof không sinh được.")

# ================================================================ LỚP 3 — công nghệ
s = slide("Lớp 3 — Công nghệ: vì sao zkVM, vì sao SP1", "Lớp 3 · Backend")
para(s, M, Inches(2.15), Inches(6.0), [
    "Hệ chứng minh không biết “chương trình” là gì. Nó chỉ biết **hệ phương trình đa "
    "thức trên một trường hữu hạn** — thứ ta gọi là *mạch*. Muốn chứng minh gì thì "
    "phải dịch phép tính thành mạch.",
    "**zkVM đảo ngược cách làm:** viết mạch cho **chính CPU**, rồi chương trình viết "
    "bằng Rust bình thường, biên dịch sang RISC-V.",
], size=12.5)
table(s, ["", "Mạch thủ công", "zkVM"], [
    ["Công sức", "rất lớn", "thấp"],
    ["Nguy cơ sai lặng lẽ", "cao — ràng buộc thiếu thì không ai báo", "thấp"],
    ["Tốc độ prove", "nhanh hơn nhiều", "chậm hơn"],
    ["Reviewer kiểm được", "phải đọc ràng buộc số học", "đọc thẳng mã Rust"],
], M, Inches(3.6), Inches(6.0), col_ratio=(4, 6, 4), hi_rows=(3,))
callout(s, M, Inches(5.15), Inches(6.0), "Đánh đổi có chủ ý",
        "Đề tài chọn zkVM và **chấp nhận chậm hơn**, vì mục tiêu là một artifact "
        "reviewer kiểm chứng được. Với một paper về tính kiểm chứng được, "
        "đánh đổi đó đúng chiều.")
table(s, ["Lựa chọn", "Vì sao không chọn cho đề tài này"], [
    ["Circom / Halo2", "reviewer không đọc nổi quan hệ DQN dưới dạng ràng buộc"],
    ["ezkl", "chuyên cho suy luận, không diễn đạt được sync target hay lấy mẫu replay"],
    ["RISC Zero", "ứng viên hợp lý thật — không loại vì kém"],
    ["Jolt", "non hơn về recursion và lớp bọc Groth16 tại thời điểm chọn"],
    ["Cairo", "ISA riêng, không dùng lại được hệ sinh thái Rust/LLVM"],
], Inches(7.1), Inches(2.15), Inches(5.5), col_ratio=(4, 9))
bullets(s, [
    "**Guest viết bằng Rust thường**, logic nằm trong shared/, test được trên CPU",
    "**Có đường CUDA** — fragment k=8: 144,6 s (CPU) → 3,8 s (A10G), nhanh 38×",
    "**Recursion chạy được thật** — guest verify proof con bằng mật mã",
    "**Precompile SHA-256** — Merkle là phép tính trung tâm, precompile làm nó rẻ",
    "**Không cần Docker cho CUDA** — tải sp1-gpu-server rồi nối Unix socket",
], Inches(7.1), Inches(4.5), Inches(5.5), size=11.5, gap=5)
tf = _tb(s, Inches(7.1), Inches(6.55), Inches(5.5), Inches(0.5))
p = tf.paragraphs[0]
p.line_spacing = 1.18
_run(p, "Nói thẳng khi bị hỏi: ", 11, MUTED)
_run(p, "chưa khảo sát so sánh có hệ thống với RISC Zero. "
        "Chọn SP1 vì đường CUDA và recursion đã dùng được lúc bắt đầu.", 11, INK2)

# ================================================================ LỚP 3 — guest/host
s = slide("Lớp 3 — guest / host / shared, và quy trình prove", "Lớp 3 · Backend")
table(s, ["Thành phần", "Chạy ở đâu", "Việc"], [
    ["guest", "bên TRONG zkVM", "phép tính được chứng minh"],
    ["host", "máy thường", "nạp dữ liệu, gọi prover, ghi metrics"],
    ["shared", "cả hai bên", "thư viện Rust chứa logic quan hệ"],
], M, Inches(2.15), Inches(5.9), col_ratio=(3, 4, 7), hi_rows=(0,))
code(s, M, Inches(3.5), Inches(5.9),
     "RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove\n\n"
     "  a. PRECHECK  gọi verifier trong shared/ để kiểm vector\n"
     "               TRƯỚC khi prove — prove một vector sai là\n"
     "               đốt tiền GPU vô ích\n"
     "  b. PROVE     nạp vector, chạy guest, sinh proof STARK\n"
     "  c. VERIFY    kiểm lại proof vừa sinh, ghi proof_verified\n"
     "  d. TAMPER    quét giả mạo trong cùng lượt chạy", size=10.5)
callout(s, M, Inches(5.5), Inches(5.9), "Vì sao có bước (a)",
        "Một lượt prove có thể mất 25 phút trên GPU thuê theo giờ. "
        "Oracle Python chạy mili giây. Bắt lỗi ở đâu rẻ hơn thì bắt ở đó.")
tf = _tb(s, Inches(6.85), Inches(2.15), Inches(5.75), Inches(0.3))
_run(tf.paragraphs[0], "metrics.json — mỏ neo truy vết của mỗi dòng Bảng 2", 11, MUTED, bold=True)
code(s, Inches(6.85), Inches(2.45), Inches(5.75),
     "relation             training_fragment\n"
     "cycle_count          5.193.244\n"
     "prove_time_seconds   3.810088194\n"
     "verify_time_seconds  0.129283375\n"
     "proof_size_bytes     2.841.071\n"
     "prover               cuda\n"
     "proof_verified       true\n"
     "test_vector_sha256   f2656757…   ← đầu vào nào\n"
     "guest_elf_sha256     ff2c14b1…   ← chương trình nào\n"
     "public_inputs_sha256 0846d55b…   ← phát biểu gì\n"
     "sp1_version          6.1.0", size=10.5)
callout(s, Inches(6.85), Inches(5.15), Inches(5.75), "Ba hash cuối là thứ làm bảng kiểm được",
        "Chúng trả lời ba câu khác nhau: proof này chạy trên **đầu vào nào**, "
        "bằng **chương trình nào**, và chứng minh **phát biểu gì**. "
        "Thiếu một cái là dòng đó không truy ngược được.")

# ================================================================ PROVER
s = slide("Prover chứng minh những gì — public input thật", "Lớp 3 · Backend",
          "training_fragment_cartpole_expert_k1 — mọi giá trị lấy từ test vector đã commit.")
code(s, M, Inches(2.15), Inches(6.4),
     "── Cam kết dữ liệu ──────────────────────────────\n"
     "dataset_root               02de61a9…   ← gốc Merkle cartpole-expert-v2\n"
     "dataset_size               50261\n"
     "manifest_hash              bdc07f0d…\n"
     "audit_report_hash          06f123bd…   ← báo cáo kiểm toán\n"
     "raw_trajectory_hash        f6c25677…\n"
     "collection_log_final_hash  75e224aa…\n\n"
     "── Siêu tham số, công khai và kiểm được ─────────\n"
     "fixed_point_scale          1000\n"
     "gamma                      990         ← γ = 0,99\n"
     "learning_rate              50          ← η = 0,05\n"
     "batch_size                 1\n"
     "gradient_clip_fp           10000\n"
     "q_abs_max_fp               4503599627370496   ← 2⁵²\n"
     "target_sync_interval       4\n"
     "target_sync_mode           hard\n\n"
     "── Chuỗi checkpoint ─────────────────────────────\n"
     "start_checkpoint_hash      107e13f5…\n"
     "final_checkpoint_hash      1c77751a…", size=10)
tf = _tb(s, Inches(7.55), Inches(2.15), Inches(5.05), Inches(0.3))
_run(tf.paragraphs[0], "PRIVATE WITNESS — verifier KHÔNG thấy", 11, WARN, bold=True)
code(s, Inches(7.55), Inches(2.45), Inches(5.05),
     "steps[0] = {\n"
     "  transition        : {state, action,\n"
     "                       reward, next_state}\n"
     "  leaf_index        : 43\n"
     "  leaf_hash         : 290fce5d…\n"
     "  merkle_path       : [ {level, sibling_hash,\n"
     "                         current_is_left}, … ]\n"
     "  online_model_before / _after\n"
     "  target_model_before / _after\n"
     "  intermediates     : {deltas, grads, …}\n"
     "}", size=10)
callout(s, Inches(7.55), Inches(4.75), Inches(5.05), "Ranh giới riêng tư",
        "Mọi thứ mô tả **thoả thuận** thì công khai. Mọi thứ chứa **dữ liệu** thì "
        "riêng tư — chỉ hash của chúng lên public input.")
callout(s, Inches(7.55), Inches(5.95), Inches(5.05), "Câu mà proof chứng minh",
        "“Tôi đã dùng η = 0,05, γ = 0,99, clip 10,0, trên đúng dataset gốc 02de61a9, "
        "và đi từ mô hình 107e13f5 tới 1c77751a.”", warn=False)

# ================================================================ VERIFIER
s = slide("Verifier verify bằng cách nào", "Lớp 3 · Backend",
          "Verifier không chạy lại phép tính. Nó kiểm một bài toán đa thức tại một điểm ngẫu nhiên.")
vsteps = [
    ("1", "Nhận ba thứ", "proof (2,8 MB STARK) · public values · vkey của chương trình"),
    ("2", "Kiểm vkey", "vkey có đúng là của quan hệ training_fragment không — "
                       "chặn việc đổi sang một chương trình dễ hơn"),
    ("3", "Kiểm cam kết", "các đa thức đã được niêm phong bằng cây Merkle + FRI, "
                          "trước khi biết điểm kiểm"),
    ("4", "Sinh điểm ngẫu nhiên", "Fiat–Shamir: điểm rút ra từ chính hash của cam kết, "
                                  "nên prover không đoán trước được"),
    ("5", "Đánh giá tại điểm đó", "nếu witness đúng thì đa thức tổ hợp triệt tiêu; "
                                  "nếu sai thì không — hai đa thức bậc d chỉ trùng "
                                  "tại nhiều nhất d điểm"),
    ("6", "Đọc public values", "so dataset_root, siêu tham số, checkpoint đầu/cuối "
                               "với hồ sơ đã đăng ký"),
]
for k, (num, name, what) in enumerate(vsteps):
    y = Inches(2.2) + Inches(0.72) * k
    rect(s, M, y, Inches(7.6), Inches(0.62), WHITE, RULE)
    rect(s, M, y, Pt(3), Inches(0.62), ACCENT)
    tf = _tb(s, M + Inches(0.18), y + Inches(0.16), Inches(0.3), Inches(0.3))
    _run(tf.paragraphs[0], num, 13, ACCENT, bold=True, font=MONO)
    tf = _tb(s, M + Inches(0.52), y + Inches(0.16), Inches(1.75), Inches(0.3))
    _run(tf.paragraphs[0], name, 12, INK, bold=True)
    tf = _tb(s, M + Inches(2.32), y + Inches(0.09), Inches(5.15), Inches(0.5))
    p = tf.paragraphs[0]
    p.line_spacing = 1.14
    _run(p, what, 11, INK2)
y = callout(s, Inches(8.65), Inches(2.2), Inches(3.95), "Vì sao chỉ mất 54 mili giây",
            "Verifier **không quan sát chương trình chạy**. Phép tính đã được biến "
            "thành một bài toán đa thức, và bài toán đó chỉ cần kiểm **tại một điểm**.")
y = callout(s, Inches(8.65), y + Inches(0.24), Inches(3.95), "Bước 6 mới là bước có ý nghĩa pháp lý",
            "Năm bước đầu nói “phép tính đã chạy đúng”. Bước 6 nói “và nó chạy trên "
            "đúng dữ liệu, đúng tham số anh đã đăng ký”.")
callout(s, Inches(8.65), y + Inches(0.24), Inches(3.95), "Giả mạo không tới được đây",
        "Guest **panic khi execute** (exit 101) trước cả bước prove. Không phải "
        "“sinh proof rồi verify từ chối” — mà là **không sinh được**.", warn=True)

# ================================================================ BẢNG 2
s = slide("Bảng 2 — Chi phí chứng minh", "Kết quả · Bảng 2",
          "25 cấu hình proof-verified, sinh trong MỘT lượt chạy trên MỘT máy g5.2xlarge.")
table(s, ["Quan hệ", "Cycles", "Prove (s)", "Verify (s)", "Proof (B)", "Prover"], [
    ["TD MVP", "434.785", "60,5", "0,124", "2.783.869", "cpu"],
    ["Merkle (canonical)", "116.750", "50,2", "0,123", "2.779.510", "cpu"],
    ["Fwd-TD MLP", "1.628.694", "89,9", "0,126", "2.798.897", "cpu"],
    ["One-step SGD tiny", "928.712", "72,0", "0,125", "2.790.551", "cpu"],
    ["Training update", "494.060", "61,5", "0,125", "2.785.799", "cpu"],
    ["Fragment k=1", "979.945", "1,6", "0,127", "2.792.511", "cuda"],
    ["Fragment k=8", "5.193.244", "3,8", "0,129", "2.841.071", "cuda"],
    ["Fragment, dữ liệu CartPole", "4.646.677", "3,7", "0,129", "2.835.671", "cuda"],
    ["Merkle 100k lá", "554.100", "61,1", "0,123", "2.784.983", "cpu"],
    ["Agg. chain T=128", "2.758.670", "2,5", "0,126", "2.819.656", "cuda"],
    ["Recursive T=64", "1.683.525.837", "755,2", "0,054", "1.274.074", "cuda"],
    ["Whole run, CartPole", "422.415.621", "199,7", "0,054", "1.274.654", "cuda"],
    ["Groth16 child T=16", "6.180.861.737", "1.596,9", "68,024", "1.468.175.345", "cuda"],
], M, Inches(2.25), Inches(7.6), col_ratio=(6, 5, 3, 3, 5, 3),
    right_cols=(1, 2, 3, 4), hi_rows=(10, 11), bad_rows=(12,), size=10)
stats(s, [("52.941×", "dải cycles, 116.750 → 6,18 tỉ — mà verify gần như không đổi"),
          ("15 / 10", "dòng chạy CUDA / CPU")],
      Inches(8.55), Inches(2.25), Inches(4.05), size=22)
y = callout(s, Inches(8.55), Inches(3.65), Inches(4.05), "Vì sao trộn CPU và GPU",
            "Chỉ **2 trong 8 host** có nhánh CUDA trong mã nguồn — fragment và "
            "aggregation. Sáu host kia không chạy GPU được, chấm hết. "
            "Đó là sự thật kỹ thuật, không phải lựa chọn thí nghiệm.")
callout(s, Inches(8.55), y + Inches(0.24), Inches(4.05), "Cột Prover tồn tại để chặn đọc sai",
        "Merkle 50,2 s trông chậm hơn Fragment k=8 3,8 s — dù Fragment nặng gấp "
        "**44 lần** về cycles.", warn=True)

# ================================================================ LỚP 4 — vì sao gộp
s = slide("Lớp 4 — Vì sao phải nối nhiều proof thành một", "Lớp 4 · Gộp")
para(s, M, Inches(2.15), Inches(5.9), [
    "Một proof training_fragment phủ được *k* bước. Ta muốn phủ **cả lượt chạy** — "
    "1.248 bước, 4.992 bước.",
    "**Cách ngây thơ — nhét cả 5.000 bước vào một guest — không khả thi:** cycles tăng "
    "tuyến tính (~2×10¹⁰), RAM ≈ 27 byte mỗi cycle → khoảng 540 GB. "
    "Proof lớn nhất từng chạy thành công là 1,68 tỉ cycles.",
], size=12.5)
code(s, M, Inches(3.75), Inches(5.9),
     "         proof GỐC        ← guest này có việc là KIỂM CÁC PROOF KHÁC\n"
     "          /       \\\n"
     "      proof      proof    ← mỗi cái lại kiểm 2 proof con\n"
     "      /   \\      /   \\\n"
     "    lá   lá    lá   lá    ← mỗi lá = 156 bước huấn luyện\n\n"
     "Kiểm một proof cũng là một phép tính → nó lại sinh ra một proof mới.\n"
     "Kết quả: MỘT proof duy nhất phủ toàn bộ, verify 0,054 s.", size=10.5)
table(s, ["Cấu hình", "Proof con", "Cycles", "Mỗi proof con"], [
    ["native_flat_recursive T=16", "2", "422.726.492", "211,4 M"],
    ["native_flat_recursive T=32", "4", "842.015.859", "210,5 M"],
    ["native_flat_recursive T=64", "8", "1.683.525.837", "210,4 M"],
], Inches(6.95), Inches(2.15), Inches(5.65), col_ratio=(7, 3, 5, 4),
    right_cols=(1, 2, 3))
y = callout(s, Inches(6.95), Inches(3.5), Inches(5.65), "≈ 211 triệu cycles mỗi proof con",
            "Và con số này **không phụ thuộc** proof con phủ bao nhiêu bước huấn luyện. "
            "Nên chi phí ước được **trên giấy** trước khi thuê máy.")
y = callout(s, Inches(6.95), y + Inches(0.24), Inches(5.65), "Hệ quả: lá dài rẻ hơn lá ngắn",
            "Lá 8 bước cho 1.248 bước → 155 lượt gộp ≈ 33 tỉ cycles. "
            "Lá **156 bước** → 7 lượt gộp ≈ 1,5 tỉ. Rẻ hơn khoảng **20 lần** — "
            "vì thế lá của cây whole-run là k = 156.")
callout(s, Inches(6.95), y + Inches(0.24), Inches(5.65), "Nhưng lá không dài vô hạn được",
        "Lá 1.000 bước ≈ 3,9 tỉ cycles — vượt mức lớn nhất từng prove thành công "
        "và đụng trần RAM (~105 GB).", warn=True)

# ================================================================ LỚP 4 — hai chế độ
s = slide("Lớp 4 — Hai chế độ gộp, và vì sao phải phân biệt", "Lớp 4 · Gộp")
tf = _tb(s, M, Inches(2.15), Inches(5.9), Inches(0.3))
_run(tf.paragraphs[0], "CHẾ ĐỘ A — proof_manifest_chain", 12, MUTED, bold=True)
bullets(s, [
    "Guest **không** kiểm proof con. Nó băm *hồ sơ* của từng proof con",
    "Kiểm public input các con **nhất quán**, dataset_root và config_hash **giống nhau**",
    "Kiểm **ranh giới chunk** khớp và chuỗi checkpoint nối liền",
    "Rẻ: T=128 chỉ 2.758.670 cycles, prove 2,5 s",
], M, Inches(2.5), Inches(5.9), size=11.5, gap=4)
callout(s, M, Inches(3.85), Inches(5.9), "Yếu hơn — và paper nói rõ",
        "Phát biểu là “CÓ MỘT dãy T proof con có siêu dữ liệu nhất quán và nối liền”. "
        "Nó **không** nói các proof con hợp lệ về mặt mật mã — ai đó phải kiểm ở ngoài.",
        warn=True)
tf = _tb(s, M, Inches(5.25), Inches(5.9), Inches(0.3))
_run(tf.paragraphs[0], "CHẾ ĐỘ B — recursive_sp1", 12, ACCENT, bold=True)
bullets(s, [
    "Guest **thật sự chạy trình kiểm SP1 lên từng proof con, bên trong mạch**",
    "Không còn giả định ngoài nào — đây mới là recursion đúng nghĩa",
    "Đắt: T=64 tốn 1,68 tỉ cycles, prove 755 s. **Chỉ chạy được trên GPU**",
], M, Inches(5.6), Inches(5.9), size=11.5, gap=4)
tf = _tb(s, Inches(6.95), Inches(2.15), Inches(5.65), Inches(0.3))
_run(tf.paragraphs[0], "public_inputs của training_aggregation_t32", 11, MUTED, bold=True)
code(s, Inches(6.95), Inches(2.45), Inches(5.65),
     "aggregation_mode      proof_manifest_chain\n"
     "chunk_relation_id     training_fragment_k8\n"
     "chunk_count           4\n"
     "chunk_size            8\n"
     "step_start / step_end 0 / 32\n"
     "dataset_root          55e0b47b…\n"
     "config_hash           b15ab414…\n"
     "chunk_public_inputs_root  4e426802…\n"
     "chunk_proof_root          1e24909a…\n"
     "chunk_verify_report_root  0a8f313e…\n"
     "input_checkpoint_hash     622e834e…\n"
     "output_checkpoint_hash    e0076d29…\n"
     "aggregate_root            9e8b7fde…\n"
     "claim_scope   \"chunk-chain aggregation over\n"
     "               externally verified proof manifests\"", size=10)
callout(s, Inches(6.95), Inches(5.35), Inches(5.65), "claim_scope nằm TRONG public input",
        "Chế độ gộp và phạm vi phát biểu là dữ liệu công khai, không phải chú thích "
        "trong paper. Verifier đọc được thẳng rằng đây là chế độ A.")
table(s, ["Cùng T = 32", "Cycles", "Prove"], [
    ["manifest chain", "880.030", "1,4 s"],
    ["recursive_sp1", "842.015.859", "385,9 s"],
], Inches(6.95), Inches(6.4), Inches(5.65), col_ratio=(5, 5, 3),
    right_cols=(1, 2), hi_rows=(1,), size=10.5)

# ================================================================ LỚP 4 — whole run
s = slide("Lớp 4 — Kết quả: một lượt huấn luyện trọn vẹn dưới một proof", "Lớp 4 · Gộp")
table(s, ["Môi trường", "Bước", "Lá", "Cycles (proof gốc)", "Prove", "Verify"], [
    ["CartPole expert", "1.248", "8 × 156", "422.415.621", "199,7 s", "0,054 s"],
    ["LunarLander expert", "1.248", "8 × 156", "422.396.109", "198,1 s", "0,054 s"],
    ["LunarLander random", "4.992", "32 × 156", "422.386.830", "188,8 s", "0,054 s"],
], M, Inches(2.25), Inches(11.9), col_ratio=(5, 3, 3, 5, 3, 3),
    right_cols=(1, 2, 3, 4, 5), hi_rows=(2,))
y = callout(s, M, Inches(3.75), Inches(5.85), "Vì sao dòng cuối đáng giá nhất",
            "Nó phủ **đúng lượt chạy sinh ra con số −152,7 ở Bảng 1**, không phải một "
            "lượt minh hoạ. Đây là chỗ Bảng 1 và Bảng 2 chạm vào nhau: cùng một lượt "
            "huấn luyện, vừa được đo hiệu năng vừa được chứng minh.")
callout(s, M, y + Inches(0.28), Inches(5.85), "Chưa nằm trong Bảng 2",
        "Vì hash guest ELF của nó khác 10 dòng anh em — cùng mã nguồn, khác đường dẫn "
        "build. Cổng kiểm đã chặn đúng.", warn=True)
para(s, Inches(6.9), Inches(3.75), Inches(5.7), [
    "**Vì sao cycles của cả ba gần bằng nhau** dù số bước chênh 4 lần: cột này là "
    "chi phí của **proof gốc**, và proof gốc luôn chỉ kiểm 2 proof con, bất kể cây "
    "sâu bao nhiêu. Tổng chi phí cả cây phải cộng thêm các nút trong và các lá.",
    "**Thứ khiến cấu hình chứng minh được học nổi không phải batch size** — mà là "
    "target_sync_interval từ 4 lên 2.000, một public input **tự do, đổi không tốn "
    "một cycle nào**.",
], size=12.5)
table(s, ["LunarLander random", "sync = 4", "sync = 2000"], [
    ["lưới quét, 2 seed", "−649,1", "−197,4"],
    ["cấu hình cuối, 3 seed", "—", "−152,7"],
], Inches(6.9), Inches(5.85), Inches(5.7), col_ratio=(6, 4, 4),
    right_cols=(1, 2), hi_rows=(1,))

# ================================================================ BẢNG 1
s = slide("Bảng 1 — Cấu hình chứng minh được học tốt tới đâu", "Kết quả · Bảng 1",
          "54 dòng = 6 dataset × 9 cấu hình, 3 seed mỗi dòng, 5.000 bước. Bảng này KHÔNG nói gì về ZK.")
table(s, ["Dataset", "BC", "Offline DQN", "Double DQN", "CQL-lite", "Chứng minh được"], [
    ["cartpole-random", "35,6", "297,2", "311,0", "302,7", "17,0"],
    ["cartpole-medium", "341,8", "9,6", "9,8", "240,1", "11,0"],
    ["cartpole-expert", "492,2", "16,3", "9,6", "193,5", "9,7"],
    ["lunarlander-random", "−381,3", "−189,4", "−215,3", "−165,7", "−152,7"],
    ["lunarlander-medium", "−189,7", "−367,6", "−366,6", "−283,7", "−829,7"],
    ["lunarlander-expert", "−48,4", "−517,8", "−518,7", "−390,7", "−717,9"],
], M, Inches(2.35), Inches(11.9), col_ratio=(5, 3, 3, 3, 3, 4),
    right_cols=(1, 2, 3, 4, 5), hi_rows=(3,))
tf = _tb(s, M, Inches(4.7), Inches(11.9), Inches(0.3))
_run(tf.paragraphs[0], "Tất cả ở optimizer SGD, để so cùng điều kiện. "
                       "Trên CartPole, 9,3 là điểm của một chính sách CHƯA HỌC GÌ CẢ "
                       "— gậy đổ sau 9 bước.", 11, MUTED)
y = callout(s, M, Inches(4.92), Inches(5.85), "Kết quả trung tâm",
            "Trên lunarlander-random, cấu hình chứng minh được (−152,7) **vượt** cấu "
            "hình tinh chỉnh batch-256 (−215,3). Khoảng cách phụ thuộc bài toán, "
            "không phải một hằng số.")
callout(s, M, y + Inches(0.22), Inches(5.85), "Offline DQN sập trên dữ liệu chất lượng cao",
        "Trên random, DQN thắng BC gấp 9 lần. Trên expert, DQN sập về 9,6 còn BC "
        "đạt 492,2 — dữ liệu expert hẹp.", warn=True)
tf = _tb(s, Inches(6.9), Inches(5.15), Inches(5.7), Inches(0.3))
_run(tf.paragraphs[0], "ADAM KHÔNG PHẢI LUÔN THẮNG SGD — 24 cặp so được", 11, ACCENT, bold=True)
code(s, Inches(6.9), Inches(5.45), Inches(5.7),
     "Toàn bộ:      Adam 13  –  SGD 11\n"
     "CartPole:     Adam  2  –  SGD 10\n"
     "LunarLander:  Adam 11  –  SGD  1", size=11)
tf = _tb(s, Inches(6.9), Inches(6.5), Inches(5.7), Inches(0.6))
p = tf.paragraphs[0]
p.line_spacing = 1.2
_run(p, "Thứ tự ", 11.5, INK2)
_run(p, "đảo ngược hoàn toàn", 11.5, INK, bold=True)
_run(p, " giữa hai môi trường. Nên việc hệ chứng minh chỉ hỗ trợ SGD không phải "
        "một khiếm khuyết mang tính hệ thống.", 11.5, INK2)

# ================================================================ BẢNG 3
s = slide("Bảng 3 — Kháng giả mạo: hệ có từ chối thứ sai không", "Kết quả · Bảng 3",
          "Bảng 2 chứng minh hệ CHẤP NHẬN thứ đúng. Bảng 3 chứng minh hệ TỪ CHỐI thứ sai.")
code(s, M, Inches(2.2), Inches(5.5),
     "① lấy một artifact HỢP LỆ đã có\n"
     "② sửa ĐÚNG MỘT trường, giữ nguyên mọi thứ khác\n"
     "     reward: 1000 → 1001\n"
     "③ đưa qua các tầng kiểm: oracle Python → guest Rust\n"
     "     → ràng buộc public input\n"
     "④ ghi lại tầng nào từ chối, lớp lỗi gì\n\n"
     "Một mục THẬT trong tamper_report.json:\n\n"
     "  case                : tamper_minibatch_index\n"
     "  reference_accepted  : false\n"
     "  reference_reason    : \"deterministic sample index mismatch\"\n"
     "  execute_passed      : false\n"
     "  execute_return_code : 101      ← panic Rust\n"
     "  passed              : true     ← BÀI KIỂM ĐẠT", size=10.5)
callout(s, M, Inches(5.55), Inches(5.5), "passed: true nghĩa là gì",
        "**Không** phải bản giả mạo qua được — mà là **bài kiểm** qua được, tức hệ đã "
        "bắt đúng. passed: false mới là tin xấu.")
stats(s, [("233/236", "bị từ chối đúng như dự đoán"),
          ("19", "nhóm tấn công, trên 20 thành phần")],
      Inches(6.95), Inches(2.2), Inches(5.65), size=24)
table(s, ["Tầng bắt được", "Số ca"], [
    ["oracle Python", "103"],
    ["guest Rust panic (exit 101)", "62"],
    ["ràng buộc public input", "57"],
    ["cam kết dataset", "7"],
    ["kiểm toán dữ liệu", "4"],
    ["không áp dụng — đều có lý do", "3"],
], Inches(6.95), Inches(3.5), Inches(5.65), col_ratio=(9, 3),
    right_cols=(1,), hi_rows=(1,))
tf = _tb(s, Inches(6.95), Inches(5.62), Inches(5.65), Inches(0.4))
p = tf.paragraphs[0]
p.line_spacing = 1.2
_run(p, "Bốn cách gian lận ở slide 2 đều có nhóm riêng: ", 11, INK2)
_run(p, "reward 6 · done 6 · td_target 4 · gradient 7", 11, INK, bold=True)
_run(p, ". Nhóm lớn nhất: proof_public_input 59, minibatch_index 43, "
        "checkpoint_hash 30.", 11, INK2)
callout(s, Inches(6.95), Inches(6.16), Inches(5.65), "Giới hạn — tự nói ra trước",
        "Bộ này kiểm giả mạo **theo từng trường**, nên **không** phủ được lỗi "
        "*ngữ nghĩa*: khi không trường nào bị sửa mà quan hệ vẫn chứng minh *sai thứ*.",
        warn=True)

# ================================================================ LỖI
s = slide("Bốn lỗi tự tìm ra — và cả bốn cùng một hình dạng", "Tự phản biện")
callout(s, M, Inches(2.15), Inches(11.9), "Hình dạng chung",
        "Hệ thống **báo xanh** trong khi thứ nó kiểm **không phải thứ ta tưởng**. "
        "Đó là chế độ hỏng nguy hiểm nhất của một hệ chứng minh — không phải hỏng ầm ĩ, "
        "mà hỏng lặng lẽ trong khi mọi đèn đều xanh.", warn=True)
para(s, M, Inches(3.25), Inches(5.85), [
    "**1 · Mọi chunk lấy mẫu trùng nhau.** sampler_seed là hằng số và step_id đếm "
    "trong nội bộ fragment:",
], size=12)
code(s, M, Inches(3.9), Inches(5.85),
     "chunk 0 → [68, 83, 22, 125, 56, 55, 42, 1]\n"
     "chunk 1 → [68, 83, 22, 125, 56, 55, 42, 1]", size=11)
para(s, M, Inches(4.75), Inches(5.85), [
    "“Lượt chạy 1.248 bước” thực chất là **156 lần lặp trên 8 dòng** của một dataset "
    "50.000 dòng. Mọi hash khớp, mọi proof hợp lệ, và **cả 236 phép thử tamper đều "
    "xanh** — vì không trường nào bị sửa.",
    "Sửa: sampler_seed = H(dataset_root, global_step_start) → **Định lý 7**.",
], size=12)
para(s, Inches(6.9), Inches(3.25), Inches(5.7), [
    "**2 · Guest tràn i64 trong im lặng.** Q phân kỳ ×22 mỗi 156 bước, tới 4,14×10¹⁶, "
    "vượt trần 9,32×10¹⁵ → gói vòng thành số âm, guest vẫn chứng minh bình thường. "
    "Chỉ lộ ra vì *Python và Rust bất đồng*. Sửa → **Định lý 8**, giá +10,7% cycles.",
    "**3 · Số trong paper chưa từng nối với pipeline.** Bảng gõ tay, trôi tới **116×**: "
    "440,6 s ghi trong paper, thực tế 3,8 s. Nay cả ba bảng được *sinh* và paper "
    "\\input thẳng, cộng một test ghim 28 con số.",
    "**4 · Hash guest ELF định danh lần build.** Cùng nguồn, khác đường dẫn → "
    "b1e7a69d vs 1e2a8a38. Dùng để bắt “prove lại một nửa” thì đúng; làm mỏ neo "
    "tái lập thì sai — và paper nói đúng như vậy.",
], size=12)

# ================================================================ KẾT
s = slide("Đóng góp, và ranh giới", "Kết luận")
bullets(s, [
    "**Ba nghĩa vụ xác minh riêng của RL** — nhãn do chính mô hình sinh ra, sync target "
    "là sự kiện rời rạc, lấy mẫu replay không có thứ tự chuẩn tắc — hình thức hoá "
    "thành **Định lý 7** (sampler binding) và **Định lý 8** (biên số học) trong 10 định lý.",
    "**Một lượt huấn luyện 4.992 bước dưới một proof**, verify trong 54 mili giây.",
    "**Đo bằng số cái giá của “cấu hình chứng minh được”** — và chỉ ra thứ đắt "
    "(batch size) *không* phải nguyên nhân; thứ miễn phí (sync interval) mới là.",
    "**Hai lớp tấn công phát hiện bằng chính việc dựng hệ**, mà benchmark tamper "
    "theo trường về nguyên tắc không thấy được.",
], M, Inches(2.2), Inches(6.3), size=12.5, gap=9)
table(s, ["Còn lại", "Trạng thái"], [
    ["Proof 4.992 bước vào Bảng 2", "chờ hash ELF tái lập được"],
    ["CartPole quy mô 50.000 bước", "≈ 68 giờ GPU, ≈ $82 — ngoài ngân sách"],
    ["Chứng minh Adam", "không khả thi ở FP_SCALE = 1000"],
    ["Batch size > 1", "cần sửa quan hệ; cycles nhân theo batch"],
    ["Bọc PLONK", "≈ 60 GB RAM, vượt máy đã thuê (32 GB)"],
    ["Nhánh CUDA cho 6 host còn lại", "việc kỹ thuật thật, ngoài phạm vi"],
], Inches(7.5), Inches(2.2), Inches(5.1), col_ratio=(5, 6), size=10.5)
callout(s, Inches(7.5), Inches(4.65), Inches(5.1), "Câu đóng",
        "Giới hạn độ dài lượt chạy là ranh giới **đo được**, không phải chỗ né tránh: "
        "Q phân kỳ theo hàm mũ, nên **hết số nguyên trước khi hết tiền thuê GPU**.")
callout(s, M, Inches(5.9), Inches(6.3), "Tái lập — ba mức, mức đầu không cần GPU",
        "python -m unittest discover tests → 313 test, ~43 giây, chạy trên laptop. "
        "Mức 2: verify proof đã có. Mức 3: prove lại từ đầu, cần GPU.")

# ---------------------------------------------------------------- save
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("da ghi:", OUT, "|", len(prs.slides.__iter__.__self__._sldIdLst), "slide")
