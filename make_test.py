import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json

def make_questions(json_file, markdown_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(markdown_file, "w", encoding="utf-8") as f:
        for idx, item in enumerate(data, start=1):
            f.write(f"## Câu {idx}: {item['question']}\n\n")
            for key in ["a", "b", "c", "d"]:
                option_text = item.get(key, "")
                if item["answer"] == key:
                    f.write(f"**\*{key.upper()}. {option_text}**\n\n")
                elif option_text:
                    f.write(f"{key.upper()}. {option_text}\n\n")
            f.write("\n")

def make_explanations(json_file, pdf_file,
                      pagesize=A4,
                      margin=40,
                      font_name="Helvetica",
                      font_path=None,
                      font_size=12,
                      line_spacing=6):
    """
    Tạo PDF chứa Câu/Đáp án/Giải thích với màu sắc và in đậm từ khóa.
    - Nếu cần tiếng Việt chuẩn: truyền font_path (TTF) + font_name tuỳ ý.
    """

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Register font nếu có font_path
    if font_path:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        bold_font = font_name + "-Bold"
        try:
            pdfmetrics.registerFont(TTFont(bold_font, font_path))
        except:
            bold_font = font_name
    else:
        bold_font = font_name + "-Bold"

    # FIX LỖI Ở ĐÂY: Ép kiểu pdf_file về string bằng str()
    c = canvas.Canvas(str(pdf_file), pagesize=pagesize)
    page_w, page_h = pagesize

    x = margin
    y = page_h - margin

    line_height = font_size + line_spacing
    max_width = page_w - 2 * margin

    def wrap_line(text: str, current_font, current_size):
        """Wrap 1 đoạn text thành nhiều dòng dựa trên độ rộng (points)."""
        words = text.split()
        if not words:
            return [""]
        lines = []
        cur = words[0]
        for w in words[1:]:
            test = f"{cur} {w}"
            if pdfmetrics.stringWidth(test, current_font, current_size) <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def ensure_space(lines_needed=1):
        nonlocal y
        if y < margin + line_height * lines_needed:
            c.showPage()
            y = page_h - margin

    for idx, item in enumerate(data, start=1):
        q = item["question"]
        ans_key = item["answer"]
        ans_text = item.get(ans_key, "")
        ans_label = ans_key.upper() if ans_key else ""
        exp = item.get("explanation", "")

        # Đảm bảo có đủ không gian cho câu mới
        ensure_space(3)
        
        # Question - Màu xanh dương đậm, in đậm
        c.setFont(bold_font, font_size + 2)
        c.setFillColorRGB(0.1, 0.3, 0.7)  # Xanh dương đậm hơn
        question_lines = wrap_line(f"Question {idx}: {q}", bold_font, font_size + 2)
        for line in question_lines:
            ensure_space()
            c.drawString(x, y, line)
            y -= line_height
        
        y -= 6  # Khoảng cách thêm
        
        # Answer label - In đậm
        c.setFont(bold_font, font_size)
        c.setFillColorRGB(0.0, 0.6, 0.1)  # Xanh lá đậm
        c.drawString(x, y, "Answer:")
        y -= line_height
        
        # Answer content
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.0, 0.5, 0.0)  # Xanh lá
        answer_lines = wrap_line(f"{ans_label}. {ans_text}", font_name, font_size)
        for line in answer_lines:
            ensure_space()
            c.drawString(x, y, line)
            y -= line_height
        
        y -= 6  # Khoảng cách thêm
        
        # Explanation label - In đậm, màu cam đậm
        ensure_space()
        c.setFont(bold_font, font_size)
        c.setFillColorRGB(0.8, 0.3, 0)  # Cam đậm
        c.drawString(x, y, "Explanation:")
        y -= line_height
        
        # Nội dung giải thích - Font thường, màu xám
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.2, 0.2, 0.2)  # Xám đậm
        if exp:
            exp_lines = wrap_line(exp, font_name, font_size)
            for line in exp_lines:
                ensure_space()
                c.drawString(x, y, line)
                y -= line_height
        else:
            y -= line_height
        
        # Khoảng cách giữa các câu
        y -= 20

    c.save()


def resolve_json_file(argument):
    candidate = Path(argument)
    if candidate.is_file():
        return candidate

    search_paths = [
        Path(".json") / f"{argument}.json",
        Path(".json") / f"{argument}.json",
        Path(f"{argument}.json"),
    ]

    for path in search_paths:
        if path.is_file():
            return path

    raise FileNotFoundError(f"JSON file not found for input: {argument}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_test.py <name-or-json-path>")
        print("Example: python make_test.py docker_includehelp")
        print("Example: python make_test.py JSON/docker_includehelp.json")
        sys.exit(1)

    json_path = resolve_json_file(sys.argv[1])
    output_name = json_path.stem

    markdown_dir = Path(".md")
    pdf_dir = Path("pdf")
    markdown_dir.mkdir(exist_ok=True)
    pdf_dir.mkdir(exist_ok=True)

    markdown_file = markdown_dir / f"{output_name}.md"
    make_questions(json_path, markdown_file)
    
    # tạo PDF explanations
    pdf_prefix = pdf_dir / f"{output_name}.pdf"
    make_explanations(json_path, pdf_prefix)
    
    sys.stdout.write(f"✅ Converted {json_path} to:\n 📄 {markdown_file}\n 📕 {pdf_prefix}\n")