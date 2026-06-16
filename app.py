from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

bot_state = {"running": False, "questions": 0}

def run_bot_thread():
    bot_state["running"] = True
    bot_state["questions"] = 0
    
    # YOUR CREDENTIALS
    SENEC_EMAIL = "malik.azouz@elawnswood.co.uk"
    SENEC_PASS = "malekazouz2020"
    LN_USER = "AzouzM"
    LN_PASS = "raven42689"
    SPARX_USER = "malikazouz"
    SPARX_PASS = "malekazouz2020"

    socketio.emit('update', {'type': 'log', 'message': '🚀 Starting Chrome Driver...'})
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        
        # 1. SENEC LEARNING
        socketio.emit('update', {'type': 'log', 'message': '🔐 Logging into Seneca...')
        driver.get("https://student.senecalearning.com")
        try:
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            pass_field = driver.find_element(By.ID, "password")
            email_field.send_keys(SENEC_EMAIL)
            pass_field.send_keys(SENEC_PASS)
            driver.find_element(By.ID, "login-button").click()
            time.sleep(4)
            socketio.emit('update', {'type': 'log', 'message': '✅ Seneca Logged In')
            
            # Try to click a subject
            try:
                subject = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".subject-card, .card"))
                subject.click()
                time.sleep(2)
                try:
                    driver.find_element(By.XPATH, "//button[contains(text(), 'Start')]").click()
                except: pass
                time.sleep(2)
                
                for i in range(5):
                    bot_state["questions"] += 1
                    socketio.emit('update', {'type': 'question', 'count': bot_state["questions"], 'detail': f'Seneca Q{i+1}')
                    try:
                        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                        if radios: radios[0].click()
                        time.sleep(1)
                        driver.find_element(By.CSS_SELECTOR, "button.check-answer, .btn-primary").click()
                        time.sleep(2)
                        try:
                            driver.find_element(By.CSS_SELECTOR, "button.next-question").click()
                        except: pass
                    except Exception as e:
                        socketio.emit('update', {'type': 'log', 'message': f'⚠️ Seneca Q: {str(e)}')
                        break
            except Exception as e:
                socketio.emit('update', {'type': 'log', 'message': f'⚠️ Seneca Nav: {str(e)}')

        except Exception as e:
            socketio.emit('update', {'type': 'log', 'message': f'❌ Seneca Login: {str(e)}')

        # 2. LANGUAGE NUT
        socketio.emit('update', {'type': 'log', 'message': '📚 Logging into Language Nut...')
        driver.get("https://www.languagenut.com")
        try:
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            pass_field = driver.find_element(By.ID, "password")
            email_field.send_keys(LN_USER)
            pass_field.send_keys(LN_PASS)
            driver.find_element(By.ID, "login-button").click()
            time.sleep(4)
            socketio.emit('update', {'type': 'log', 'message': '✅ LN Logged In')
            
            try:
                topic = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".topic-card, .card"))
                topic.click()
                time.sleep(3)
                questions = driver.find_elements(By.CSS_SELECTOR, ".question-block, .q-row")
                for q in questions:
                    bot_state["questions"] += 1
                    socketio.emit('update', {'type': 'question', 'count': bot_state["questions"], 'detail': f'LN Q')
                    try:
                        opts = q.find_elements(By.CSS_SELECTOR, ".option, label")
                        if opts: opts[0].click()
                    except: pass
                try:
                    driver.find_element(By.ID, "submit-answers").click()
                except: pass
                socketio.emit('update', {'type': 'log', 'message': '✅ LN Submitted')
            except Exception as e:
                socketio.emit('update', {'type': 'log', 'message': f'⚠️ LN Solve: {str(e)}')
        except Exception as e:
            socketio.emit('update', {'type': 'log', 'message': f'❌ LN Login: {str(e)}')

        socketio.emit('update', {'type': 'finish', 'message': '🏁 Bot Finished!')
        bot_state["running"] = False

    except Exception as e:
        socketio.emit('update', {'type': 'log', 'message': f'❌ Critical: {str(e)}')
        bot_state["running"] = False
    finally:
        if driver: driver.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    if bot_state["running"]:
        return jsonify({"status": "error", "message": "Bot running!"})
    thread = threading.Thread(target=run_bot_thread)
    thread.start()
    return jsonify({"status": "success", "message": "Bot started!"})

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)
