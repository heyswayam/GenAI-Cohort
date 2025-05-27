import tiktoken 

enc = tiktoken.encoding_for_model("gpt-4o")
text = 'Hello There !'
# response_ecoding =  enc.encode(text)
# print(response_ecoding)


num = [13225, 3274, 1073]

response_decoding = enc.decode(num)
print(response_decoding)
