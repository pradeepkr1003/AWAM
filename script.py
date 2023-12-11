import requests, json, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from config import Configure as configs

# system prompt 
s_prompt = '''
You are an AI chat responder. You are given a task to respond to the messages of students.
You will be provided with messages and you have to extract what they are asking, the message will include their name and time and the message content.
(you might receive a message like this: "John Doe 12:00 PM: Hi, I have a question about the assignment")
'''

invoke_url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/35ec3354-2681-4d0e-a8dd-80325dcf7c63"
headers = {
    "Authorization": configs.your_api,
    "accept": "text/event-stream",
    "content-type": "application/json",
}

chat_profile_name = "type the name of the chat profile here"


# Set the path to the Firefox profile directory
firefox_profile_path = "./firefox_profile"

# Configure Firefox options
options = webdriver.FirefoxOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--profile-directory=' + firefox_profile_path)

driver = webdriver.Firefox(options=options)
cookies = ""

if (open('cookies.txt', 'r').read() != ""):
    cookies = open('cookies.txt', 'r').read()
    for cookie in cookies:
        driver.add_cookie(cookie)
    
    driver.get("https://web.whatsapp.com")
    WebDriverWait(driver, 150).until(lambda driver: driver.find_element(by=By.XPATH, value="//button[@aria-label='Archived ']"))
    driver.refresh()

else:
    print('...taking the second route...')
    driver.get("https://web.whatsapp.com")
    WebDriverWait(driver, 110).until(lambda driver: driver.find_element(by=By.XPATH, value="//canvas[@aria-label='Scan me!']"))
    WebDriverWait(driver, 150).until(lambda driver: driver.find_element(by=By.XPATH, value="//button[@aria-label='Archived ']"))
    cookies = driver.get_cookies()

    with open('cookies.txt', 'w') as filehandle:
        for cookie in cookies:
            filehandle.write('%s\n' % cookie)
        print("Cookies: ", cookies)

WebDriverWait(driver, 20).until(lambda driver: driver.find_element(by=By.XPATH, value=f"//span[@title='{chat_profile_name}']"))
driver.find_element(by=By.XPATH, value=f"//span[@title='{chat_profile_name}']").click()
driver.execute_script("""
    var element = document.getElementById("side");
    element.parentNode.removeChild(element);
    """)

# pattern

WebDriverWait(driver, 20).until(lambda driver: driver.find_elements(by=By.CSS_SELECTOR, value="div[aria-label^='Open chat details for']"))
elms = driver.find_elements(by=By.CSS_SELECTOR, value="div[aria-label^='Open chat details for']")
p_elm = elms[-1].find_element(by=By.XPATH, value="..")
last_message_text = p_elm.text

print('here is your last messages: ', last_message_text)
payload = {
    "messages" : [
        {
            "role": "system",
            "content" : s_prompt
        },
        {
            "role": "user",
            "content" : last_message_text
        },
    ], 
    "temperature": 0.5,
    "top_p": 0.7,
    "max_tokens": 200,
    "stream": True,
}

print('A reply for student')
WebDriverWait(driver, 20).until(lambda driver: driver.find_element(by=By.CSS_SELECTOR, value="div[title='Type a message'"))
text_input = driver.find_element(by=By.CSS_SELECTOR, value="div[title='Type a message'")

# send message to the server
response = requests.post(invoke_url, json=payload, headers=headers, stream=True)
_bot_response = ''
print('response: ', response)
for line in response.iter_lines():
    if line:
        try:
            _json_res = line.decode('utf-8').replace('data: ', '')
            _res = json.loads(_json_res)
            if _res['choices'][0]['finish_reason'] == 'stop': break
            _bot_response += _res['choices'][0]['delta']['content']

        except Exception as e:
            print('error: ', e)
            continue

print('bot response: ', _bot_response)

# send response to student
for char in _bot_response:
    text_input.send_keys(char)
    time.sleep(0.05)

# text_input.send_keys(Keys.ENTER)
# Close the browser window
time.sleep(10)
driver.quit()

