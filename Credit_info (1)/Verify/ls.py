import pytesseract
from PIL import ImageGrab, Image


def grab():
    img = ImageGrab.grab([800, 220, 840, 239])
    out = img.resize((80, 38), Image.ANTIALIAS)
    text = pytesseract.image_to_string(out)  # 训练的数字库
    return text


def grab2():
    img = ImageGrab.grab([500, 225, 660, 248])
    out = img.resize((348, 55), Image.ANTIALIAS)
    text = pytesseract.image_to_string(out)  # 原始库，待训练
    new_text = text.replace(' ', '').replace("\n", "")  # 替换空行及空格
    return new_text


def main():
    print('识别数字为：', grab())
    print('识别汉字为：', grab2())


if __name__ == '__main__':
    main()
