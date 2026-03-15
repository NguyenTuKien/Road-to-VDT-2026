import scrapy
import re

class IncludehelpSpider(scrapy.Spider):
    name = 'includehelp'
    allowed_domains = ['includehelp.com']
    start_urls = ['https://www.includehelp.com/mcq/docker-mcqs.aspx']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    def parse(self, response):
        # Lấy tất cả các thẻ <ol> làm mốc
        ols = response.xpath('//ol[contains(@style, "upper-alpha")]')
        
        for index, ol in enumerate(ols, start=1):
            
            # 1. Lấy câu hỏi và cắt bỏ số thứ tự ở đầu (vd: "1. Which of..." -> "Which of...")
            raw_question = "".join(ol.xpath('preceding-sibling::p[1]//text()').getall()).strip()
            question = re.sub(r'^\d+\.\s*', '', raw_question)
            
            # 2. Lấy danh sách các đáp án A, B, C, D
            options = [opt.strip() for opt in ol.xpath('./li//text()').getall() if opt.strip()]
            
            # 3. Trích xuất chữ cái đáp án đúng
            answer_node = ol.xpath('following-sibling::p[b[contains(text(), "Answer:")]]')
            if answer_node:
                raw_answer = answer_node[0].xpath('./text()').get(default='')
                # Tìm chữ cái A, B, C, D đầu tiên xuất hiện (không phân biệt hoa thường)
                match = re.search(r'([A-Da-d])', raw_answer)
                answer = match.group(1).lower() if match else ""
            else:
                answer = ""
            
            # 4. Lấy phần giải thích chi tiết
            explanation_heading = ol.xpath('following-sibling::p[b[contains(text(), "Explanation:")]]')
            if explanation_heading:
                explanation = "".join(explanation_heading[0].xpath('following-sibling::p[1]//text()').getall()).strip()
            else:
                explanation = ""

            # 5. Đóng gói dữ liệu theo đúng chuẩn JSON thầy yêu cầu
            yield {
                "no": index,
                "question": question,
                "a": options[0] if len(options) > 0 else "",
                "b": options[1] if len(options) > 1 else "",
                "c": options[2] if len(options) > 2 else "",
                "d": options[3] if len(options) > 3 else "",
                "answer": answer,
                "explanation": explanation,
                "source": response.url
            }