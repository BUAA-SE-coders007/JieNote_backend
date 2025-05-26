import fitz
import asyncio

def extract_text_from_pdf(pdf_path):
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    text = ""
    # 遍历每一页
    for page_num in range(len(doc) - 2):
        page = doc.load_page(page_num)  # 加载页面
        page_text = page.get_text("text") 
        text += page_text
    doc.close()  # 关闭PDF文件
    return text

async def read_pdf(pdf_path: str):
    return await asyncio.to_thread(extract_text_from_pdf, pdf_path)