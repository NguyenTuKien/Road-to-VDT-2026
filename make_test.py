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
                    # Dùng raw string r"" để fix SyntaxWarning
                    f.write(fr"**\*{key.upper()}. {option_text}**" + "\n\n")
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
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if font_path:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        bold_font = font_name + "-Bold"
        try:
            pdfmetrics.registerFont(TTFont(bold_font, font_path))
        except:
            bold_font = font_name
    else:
        bold_font = font_name + "-Bold"

    c = canvas.Canvas(str(pdf_file), pagesize=pagesize)
    page_w, page_h = pagesize
    x = margin
    y = page_h - margin
    line_height = font_size + line_spacing
    max_width = page_w - 2 * margin

    def wrap_line(text: str, current_font, current_size):
        words = text.split()
        if not words: return [""]
        lines, cur = [], words[0]
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
        q = item.get("question", "")
        ans_key = item.get("answer", "")
        ans_text = item.get(ans_key, "")
        ans_label = ans_key.upper() if ans_key else ""
        exp = item.get("explanation", "")

        ensure_space(3)
        c.setFont(bold_font, font_size + 2)
        c.setFillColorRGB(0.1, 0.3, 0.7)
        for line in wrap_line(f"Question {idx}: {q}", bold_font, font_size + 2):
            ensure_space(); c.drawString(x, y, line); y -= line_height
        
        y -= 6
        c.setFont(bold_font, font_size)
        c.setFillColorRGB(0.0, 0.6, 0.1)
        c.drawString(x, y, "Answer:")
        y -= line_height
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.0, 0.5, 0.0)
        for line in wrap_line(f"{ans_label}. {ans_text}", font_name, font_size):
            ensure_space(); c.drawString(x, y, line); y -= line_height
        
        y -= 6
        ensure_space()
        c.setFont(bold_font, font_size)
        c.setFillColorRGB(0.8, 0.3, 0)
        c.drawString(x, y, "Explanation:")
        y -= line_height
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        if exp:
            for line in wrap_line(exp, font_name, font_size):
                ensure_space(); c.drawString(x, y, line); y -= line_height
        else:
            y -= line_height
        y -= 20

    c.save()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_test.py <folder-name>")
        sys.exit(1)

    target_dir = Path(sys.argv[1])
    if not target_dir.is_dir():
        print(f"❌ Lỗi: Thư mục '{target_dir}' không tồn tại!")
        sys.exit(1)

    json_path = target_dir / "data.json"
    if not json_path.is_file():
        print(f"❌ Lỗi: Không tìm thấy 'data.json' trong '{target_dir}'!")
        sys.exit(1)

    make_questions(json_path, target_dir / "README.md")
    make_explanations(json_path, target_dir / "Explanation.pdf")
    sys.stdout.write(f"✅ Xong! Kiểm tra kết quả tại: {target_dir}/\n")