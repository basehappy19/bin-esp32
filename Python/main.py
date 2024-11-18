import gspread
from oauth2client.service_account import ServiceAccountCredentials
from machine import Pin
from time import sleep
import time
import network 

# ตั้งค่า PIN
IN1 = Pin(14, Pin.OUT)  # พินควบคุมมอเตอร์
BUZZER_PIN = Pin(25, Pin.OUT)  # พินควบคุมบัซเซอร์
SENSOR_PIN = Pin(15, Pin.IN)  # พินรับข้อมูลจากเซนเซอร์
BUTTON_PIN = Pin(13, Pin.IN, Pin.PULL_UP)  # พินรับข้อมูลจากปุ่มกด

# ตัวแปรสำหรับสถานะและการทำงาน
counter = 0  # ตัวนับจำนวนขวด
studentID = ""  # เก็บรหัสนักเรียน
maxIDLength = 6  # กำหนดความยาวสูงสุดของรหัสนักเรียน
lastBottleTime = 0  # เวลาที่ตรวจจับขวดล่าสุด
idleStartTime = 0  # เวลาที่เริ่มเข้าสู่สถานะว่าง
noBottleInterval = 5000  # เวลารอการตรวจจับขวด (มิลลิวินาที)
maxBottleInterval = 20000  # เวลาสูงสุดที่ระบบจะรอ (มิลลิวินาที)
idleTimeout = 30000  # เวลาที่ระบบจะอยู่ในสถานะว่างก่อนรีเซ็ต (มิลลิวินาที)
currentState = "WELCOME"  # สถานะเริ่มต้น

# ตั้งค่า Wi-Fi
wifi_ssid = "Your_SSID"  # ชื่อ Wi-Fi
wifi_password = "Your_PASSWORD"  # รหัสผ่าน Wi-Fi

# ฟังก์ชันเชื่อมต่อ Wi-Fi
def connect_to_wifi():
    print("Connecting to Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)  # ตั้งค่าเป็น Station Mode
    wlan.active(True)  # เปิดการเชื่อมต่อ
    wlan.connect(wifi_ssid, wifi_password)  # เชื่อมต่อด้วย SSID และรหัสผ่าน

    retry_count = 0
    while not wlan.isconnected():  # รอจนกว่าจะเชื่อมต่อสำเร็จ
        print("Attempting to connect...")
        retry_count += 1
        sleep(1)
        if retry_count > 10:  # ถ้าลองเกิน 10 ครั้งให้รีเซ็ตระบบ
            print("Failed to connect to Wi-Fi. Restarting...")
            machine.reset()
    
    print("Wi-Fi connected!")
    print(f"IP Address: {wlan.ifconfig()[0]}")  # แสดง IP Address

# เชื่อมต่อ Wi-Fi
connect_to_wifi()

# ตั้งค่า Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]  # สิทธิ์เข้าถึง
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)  # โหลดไฟล์ credentials
gc = gspread.authorize(credentials)  # เชื่อมต่อ Google Sheets
sheet = gc.open("Your Google Sheet Name").sheet1  # ชื่อ Google Sheet ที่จะใช้งาน

# เริ่มต้นระบบ
print("Initializing system...")
print("Welcome! Press the button to start.")

while True:
    buttonState = BUTTON_PIN.value()  # อ่านสถานะปุ่มกด
    current_time = time.ticks_ms()  # อ่านเวลาปัจจุบัน

    if currentState == "WELCOME":  # สถานะเริ่มต้น
        if buttonState == 0:  # ถ้ากดปุ่ม
            print("Motor started for 10 seconds.")
            IN1.value(1)  # เปิดมอเตอร์
            sleep(10)  # ทำงาน 10 วินาที
            IN1.value(0)  # ปิดมอเตอร์
            print("Enter Student ID:")  # แสดงข้อความ
            currentState = "ENTER_STUDENT_ID"  # เปลี่ยนสถานะ
            idleStartTime = current_time  # บันทึกเวลาเริ่มต้น

    elif currentState == "ENTER_STUDENT_ID":  # สถานะป้อนรหัสนักเรียน
        key = input("Enter key (* to delete, # to confirm): ")  # รับคีย์จากผู้ใช้
        if key == "#":  # ยืนยันรหัส
            currentState = "SENSOR_DETECTION"
            lastBottleTime = current_time
            print("Not Found Bottle")
        elif key == "*" and len(studentID) > 0:  # ลบรหัสตัวสุดท้าย
            studentID = studentID[:-1]
        elif len(studentID) < maxIDLength:  # เพิ่มตัวอักษรในรหัส
            studentID += key
        print(f"Student ID: {studentID}")  # แสดงรหัสนักเรียน

        # ถ้าไม่มีการตอบสนองนานเกินกำหนด กลับสู่สถานะเริ่มต้น
        if time.ticks_diff(current_time, idleStartTime) > idleTimeout:
            IN1.value(1)
            sleep(10)
            IN1.value(0)
            print("Welcome! Press the button to start.")
            currentState = "WELCOME"

    elif currentState == "SENSOR_DETECTION":  # สถานะตรวจจับขวด
        if SENSOR_PIN.value() == 0:  # ตรวจพบขวด
            counter += 1  # เพิ่มตัวนับขวด
            lastBottleTime = current_time  # อัปเดตเวลาล่าสุด
            print(f"Bottle detected: {counter}")
            BUZZER_PIN.value(1)  # เปิดบัซเซอร์
            sleep(0.25)
            BUZZER_PIN.value(0)  # ปิดบัซเซอร์
            sleep(1)
        elif time.ticks_diff(current_time, lastBottleTime) > maxBottleInterval:  # เกินเวลาที่กำหนด
            IN1.value(1)
            sleep(10)
            IN1.value(0)
            print("Welcome! Press the button to start.")
            currentState = "WELCOME"
        elif time.ticks_diff(current_time, lastBottleTime) > noBottleInterval and counter > 0:  # จบการตรวจจับ
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                sheet.append_row([timestamp, studentID, counter])  # บันทึกลง Google Sheets
                print(f"Saved to Google Sheets: {timestamp}, {studentID}, {counter}")
            except Exception as e:
                print(f"Error saving to Google Sheets: {e}")
            currentState = "THANK_YOU"
            print("Thank you for bottle!")

    elif currentState == "THANK_YOU":  # สถานะขอบคุณ
        sleep(3)  # หน่วงเวลา 3 วินาที
        counter = 0  # รีเซ็ตตัวนับขวด
        print("Welcome! Press the button to start.")
        currentState = "WELCOME"  # กลับไปสถานะเริ่มต้น

    sleep(0.1)  # หน่วงเวลาสั้น ๆ
