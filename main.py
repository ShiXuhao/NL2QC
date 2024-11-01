from proccessor import OpenAIHandler, CodeValidator, CodeRefiner

handler = OpenAIHandler()
code_validator = CodeValidator()
code_refiner = CodeRefiner(handler)
summary = handler.generate_summary("选择最近5日涨幅大于10%的股票，买入，止损10%", "止损10%")

print(summary)

code = handler.generate_qc_code(summary)
print(code)

flag, info = code_validator.validate_code(code)

while not flag:
    code = code_refiner.refine_code(code, info)
    flag, info = code_validator.validate_code(code)


print("*" * 100)
print(code)