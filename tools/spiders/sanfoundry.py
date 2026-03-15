import re
import scrapy
from scrapy.selector import Selector

# ĐÃ SỬA: Phải kế thừa từ scrapy.Spider
class SanfoundrySpider(scrapy.Spider):
    name = "sanfoundry"
    allowed_domains = ["sanfoundry.com"]
    start_urls = ["http://127.0.0.1:5500/.web/kubernetes_sanfoundry.html"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def parse(self, response):
        # Lặp qua tất cả các thẻ <p>
        for p in response.css("div.entry-content > p"):
            p_html = p.get()
            if not p_html:
                continue

            # Đổi thẻ <br> thành dấu xuống dòng (\n) để giữ nguyên cấu trúc các đáp án
            p_html = re.sub(r'<br\s*/?>', '\n', p_html, flags=re.IGNORECASE)

            # Rút trích text tinh khiết, xuyên qua các thẻ <strong>, <code>
            clean_text = Selector(text=p_html).xpath('string(.)').get()
            
            lines = [x.strip() for x in clean_text.split('\n') if x.strip()]
            if not lines:
                continue

            if not re.match(r"^\d+\.", lines[0]):
                continue

            q_no = None
            question = None
            options = {}
            question_parts = []
            found_first_option = False
            
            for line in lines:
                if re.match(r"^\d+\.", line):
                    m = re.match(r"^(\d+)\.\s*(.*)$", line)
                    if m:
                        q_no = int(m.group(1))
                        question_parts.append(m.group(2).strip())
                elif re.match(r"^[a-dA-D][\)\.]", line):
                    found_first_option = True
                    key = line[0].lower()
                    val = re.sub(r"^[a-dA-D][\)\.]\s*", "", line).strip()
                    options[key] = val
                elif not found_first_option and question_parts:
                    question_parts.append(line)
            
            if question_parts:
                question = " ".join(question_parts).strip()

            # --- Lấy Đáp Án và Giải Thích ---
            btn_id = p.css("span.collapseomatic::attr(id)").get()
            answer = None
            explanation = None

            if btn_id:
                target_id = f"target-{btn_id}"
                ans_texts = response.css(f"#{target_id} ::text").getall()
                ans_block = " ".join([re.sub(r"\s+", " ", t).strip() for t in ans_texts if t.strip()])

                m_ans = re.search(r"Answer:\s*([a-dA-D])\b", ans_block, re.IGNORECASE)
                if m_ans:
                    answer = m_ans.group(1).lower()

                m_exp = re.search(r"Explanation:\s*(.*)$", ans_block, re.IGNORECASE)
                if m_exp:
                    explanation = m_exp.group(1).strip()

            if q_no and question:
                yield {
                    "no": q_no,
                    "question": question,
                    "a": options.get("a", ""),
                    "b": options.get("b", ""),
                    "c": options.get("c", ""),
                    "d": options.get("d", ""),
                    "answer": answer,
                    "explanation": explanation,
                    "source": response.url,
                }