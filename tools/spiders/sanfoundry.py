import re
import tools


class SanfoundrySpider(tools.Spider):
    name = "sanfoundry"
    allowed_domains = ["sanfoundry.com"]
    start_urls = ["https://www.sanfoundry.com/kubernetes-mcq-multiple-choice-questions/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en",
        },
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def parse(self, response):
        # mỗi câu hỏi thường nằm trong 1 <p> trong entry-content
        for p in response.css("div.entry-content p"):
            first_text = p.xpath("normalize-space(text()[1])").get()
            if not first_text or not re.match(r"^\d+\.", first_text):
                continue

            # lấy lines trong <p> (có cả <br>)
            lines = p.xpath(".//text()[normalize-space()]").getall()
            lines = [re.sub(r"\s+", " ", x).strip() for x in lines if x.strip()]

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
                elif re.match(r"^[a-dA-D]\)", line):
                    found_first_option = True
                    key = line[0].lower()
                    val = line[3:].strip()
                    options[key] = val
                elif not found_first_option and question_parts:
                    # Phần tiếp theo của câu hỏi (sau strong tag, etc.)
                    question_parts.append(line)
            
            # Ghép tất cả các phần của câu hỏi lại
            if question_parts:
                question = " ".join(question_parts).strip()

            # lấy id của nút View Answer
            btn_id = p.css("span.collapseomatic::attr(id)").get()

            answer = None
            explanation = None

            if btn_id:
                target_id = f"target-{btn_id}"

                # tìm div đáp án bằng id (ở cùng page)
                ans_texts = response.css(f"#{target_id} ::text").getall()
                ans_texts = [re.sub(r"\s+", " ", t).strip() for t in ans_texts if t.strip()]
                ans_block = " ".join(ans_texts)

                # parse "Answer: d" và "Explanation: ..."
                m_ans = re.search(r"Answer:\s*([a-dA-D])\b", ans_block)
                if m_ans:
                    answer = m_ans.group(1).lower()

                m_exp = re.search(r"Explanation:\s*(.*)$", ans_block)
                if m_exp:
                    explanation = m_exp.group(1).strip()

            yield {
                "no": q_no,
                "question": question,
                "a": options.get("a"),
                "b": options.get("b"),
                "c": options.get("c"),
                "d": options.get("d"),
                "answer": answer,
                "explanation": explanation,
                "source": response.url,
            }
