from app.utils import xunfei_translate

print(xunfei_translate.check_language("WHAT IS MIG?"))
text="WHAT IS MIG?"
if all(ord(ch) < 128 for ch in text):
    print("ENGLISH")
print(xunfei_translate.translate("i want to use tigdc", "en"))