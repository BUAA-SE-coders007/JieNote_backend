from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import numpy as np

def pdf_to_text(pdf_path):
    """
    使用 PaddleOCR 将 PDF 文件转换为文字。

    :param pdf_path: PDF 文件路径
    :param output_dir: 可选，保存中间图像文件的目录（如果需要）
    :return: 提取的文字内容
    """
    # 初始化 PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 支持中文

    # 将 PDF 转换为图像
    images = convert_from_path(pdf_path)

    extracted_text = []

    for i, image in enumerate(images):  # 解包 enumerate 返回的元组
        # 将 PIL 图像转换为 OCR 可处理的格式
        image_np = np.array(image)

        # 使用 PaddleOCR 进行文字识别
        result = ocr.ocr(image_np, cls=True)

        # 提取文字部分
        for line in result[0]:
            extracted_text.append(line[1][0])  # line[1][0] 是识别的文字

    return "\n".join(extracted_text)


if __name__ == "__main__":
    pdf_path = "example.pdf"
    text = pdf_to_text(pdf_path)
    print(text)