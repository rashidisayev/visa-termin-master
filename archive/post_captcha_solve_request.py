import sys
import os
import requests

#curl -v -F username=rashidisayev -F password=Ra1501894491199 -F captchafile=@"/home/rashidi/Desktop/visachecker/visa-appointment-helper-master/target/captcha.jpg" http://api.dbcapi.me/api/captcha

imagepath = "/home/rashidi/Desktop/visachecker/visa-appointment-helper-master/target/captcha.jpg"
posturl = "http://api.dbcapi.me/api/captcha"
#register in deathbycaptcha to get credentials
multipart_form_data = {
    'captchafile': open(imagepath, 'rb'),
    'username': ('', 'username'),
    'password': ('', 'password')
}

response = requests.post('http://api.dbcapi.me/api/captcha', files=multipart_form_data)

import pprint
pprint.pprint(response.content)
