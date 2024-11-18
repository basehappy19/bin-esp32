# นำเข้าไลบรารีที่จำเป็น
from machine import Pin, PWM  # ใช้ควบคุมพิน GPIO
from time import sleep  # ใช้สำหรับการหน่วงเวลา
import time  # ใช้สำหรับการติดตามเวลา

# ตั้งค่าพินสำหรับควบคุมอุปกรณ์
IN1 = Pin(14, Pin.OUT)  # พินควบคุมมอเตอร์
BUZZER_PIN = Pin(25, Pin.OUT)  # พินควบคุมบัซเซอร์
SENSOR_PIN = Pin(15, Pin.IN)  # พินรับข้อมูลจากเซนเซอร์
BUTTON_PIN = Pin(13, Pin.IN, Pin.PULL_UP)  # พินรับข้อมูลจากปุ่มกด

# ตัวแปรสำหรับควบคุมสถานะ
counter = 0  # ตัวนับจำนวนขวดที่ตรวจจับได้
studentID = ""  # ตัวแปรเก็บรหัสนักเรียน
maxIDLength = 6  # จำนวนตัวอักษรสูงสุดสำหรับรหัสนักเรียน
lastBottleTime = 0  # เวลาที่บันทึกการตรวจจับขวดครั้งล่าสุด
idleStartTime = 0  # เวลาที่เริ่มเข้าสู่สถานะว่าง
noBottleInterval = 5000  # ระยะเวลาระหว่างการตรวจจับขวด (มิลลิวินาที)
maxBottleInterval = 20000  # ระยะเวลาสูงสุดที่ระบบจะรอตรวจจับขวด (มิลลิวินาที)
idleTimeout = 30000  # ระยะเวลาที่ระบบจะอยู่ในสถานะว่างก่อนกลับไปเริ่มต้นใหม่ (มิลลิวินาที)
currentState = "WELCOME"  # สถานะปัจจุบันของระบบ

# การเริ่มต้นระบบ
print("Initializing system...")  # แสดงข้อความเริ่มต้นระบบ
print("Welcome! Press the button to start.")  # แสดงข้อความเชิญชวนให้กดปุ่ม

# วนลูปเพื่อควบคุมการทำงานของระบบ
while True:
    buttonState = BUTTON_PIN.value()  # อ่านสถานะของปุ่มกด
    current_time = time.ticks_ms()  # อ่านเวลาปัจจุบันในมิลลิวินาที

    # สถานะ WELCOME: รอการกดปุ่มเพื่อเริ่ม
    if currentState == "WELCOME":
        if buttonState == 0:  # ถ้ากดปุ่ม
            print("Motor started for 10 seconds.")  # แสดงข้อความ
            IN1.value(1)  # เริ่มมอเตอร์
            sleep(10)  # ทำงานเป็นเวลา 10 วินาที
            IN1.value(0)  # ปิดมอเตอร์
            print("Enter Student ID:")  # แสดงข้อความให้ใส่รหัสนักเรียน
            currentState = "ENTER_STUDENT_ID"  # เปลี่ยนสถานะ
            idleStartTime = current_time  # บันทึกเวลาเริ่มต้นของสถานะ

    # สถานะ ENTER_STUDENT_ID: รอการป้อนรหัสนักเรียน
    elif currentState == "ENTER_STUDENT_ID":
        key = input("Enter key (* to delete, # to confirm): ")  # รับค่าจากผู้ใช้
        if key == "#":  # ถ้ากดปุ่มยืนยัน
            print("Not Found Bottle")  # แสดงข้อความ
            currentState = "SENSOR_DETECTION"  # เปลี่ยนสถานะ
            lastBottleTime = current_time  # บันทึกเวลาปัจจุบัน
        elif key == "*" and len(studentID) > 0:  # ถ้ากดปุ่มลบ
            studentID = studentID[:-1]  # ลบตัวอักษรตัวสุดท้าย
        elif len(studentID) < maxIDLength:  # ถ้ารหัสยังไม่เกินความยาวสูงสุด
            studentID += key  # เพิ่มตัวอักษรที่ป้อนเข้ามา
        print(f"Student ID: {studentID}")  # แสดงรหัสนักเรียน

        # กลับไปสถานะเริ่มต้นถ้าไม่มีการตอบสนองในเวลาที่กำหนด
        if time.ticks_diff(current_time, idleStartTime) > idleTimeout:
            IN1.value(1)  # เปิดมอเตอร์
            sleep(10)  # ทำงานเป็นเวลา 10 วินาที
            IN1.value(0)  # ปิดมอเตอร์
            print("Welcome! Press the button to start.")  # แสดงข้อความ
            currentState = "WELCOME"  # เปลี่ยนสถานะกลับไปเริ่มต้น

    # สถานะ SENSOR_DETECTION: รอตรวจจับขวด
    elif currentState == "SENSOR_DETECTION":
        if SENSOR_PIN.value() == 0:  # ถ้าตรวจจับขวดได้
            counter += 1  # เพิ่มจำนวนขวด
            lastBottleTime = current_time  # บันทึกเวลาปัจจุบัน
            print(f"Bottle detected: {counter}")  # แสดงจำนวนขวดที่ตรวจจับได้
            BUZZER_PIN.value(1)  # เปิดบัซเซอร์
            sleep(0.25)  # หน่วงเวลา
            BUZZER_PIN.value(0)  # ปิดบัซเซอร์
            sleep(1)  # หน่วงเวลา
        elif time.ticks_diff(current_time, lastBottleTime) > maxBottleInterval:  # ถ้าเวลารอนานเกินกำหนด
            IN1.value(1)  # เปิดมอเตอร์
            sleep(10)  # ทำงานเป็นเวลา 10 วินาที
            IN1.value(0)  # ปิดมอเตอร์
            print("Welcome! Press the button to start.")  # แสดงข้อความ
            currentState = "WELCOME"  # เปลี่ยนสถานะกลับไปเริ่มต้น
        elif time.ticks_diff(current_time, lastBottleTime) > noBottleInterval and counter > 0:  # ถ้าตรวจจับขวดสำเร็จ
            print(f"Saving to sheet: Bottle Count: {counter}")  # แสดงข้อความบันทึกข้อมูล
            currentState = "THANK_YOU"  # เปลี่ยนสถานะเป็นขอบคุณ
            print("Thank you for bottle!")  # แสดงข้อความขอบคุณ

    # สถานะ THANK_YOU: แสดงข้อความขอบคุณ
    elif currentState == "THANK_YOU":
        sleep(3)  # หน่วงเวลา 3 วินาที
        counter = 0  # รีเซ็ตตัวนับขวด
        print("Welcome! Press the button to start.")  # แสดงข้อความ
        currentState = "WELCOME"  # เปลี่ยนสถานะกลับไปเริ่มต้น

    sleep(0.1)  # หน่วงเวลาสั้น ๆ
