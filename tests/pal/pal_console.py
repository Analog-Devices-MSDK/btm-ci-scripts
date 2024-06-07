import string
import sys
from random import choice
from typing import List
import time
import serial


def generate_text(length=100, chars=string.ascii_letters + string.digits):
    return "".join([choice(chars) for i in range(length)]).encode("utf-8")


def base_test(console: serial.Serial, text, delay):
    for line in text:
        for char in line:
            console.write(char)
            print(chr(char))
            echo = console.read().decode("utf-8")

            print(echo)

            if echo != chr(char):
                print(f"MISMATCH! Got {echo} Expected {char}")
                return False

            time.sleep(delay)

    return True


def fast_test(console: serial.Serial, text: List[str]):
    return base_test(console, text, delay=0)


def slow_test(console: serial.Serial, text: List[str]):
    return base_test(console, text, delay=0.075)


if __name__ == "__main__":
    console_port = sys.argv[1]

    print(f"Running test on console port {console_port}")

    console = serial.Serial(sys.argv[1], baudrate=115200, timeout=1)
    time.sleep(1)
    if len(sys.argv) >= 3:
        num_lines = sys.argv[2]
    else:
        num_lines = 100

    random_text = []
    for i in range(num_lines):
        random_text.append(generate_text())

    random_text = ["hello world".encode("utf-8")]

    overall_result = True
    ret = slow_test(console, random_text)
    if not ret:
        overall_result = False
        print("Slow test failed")

    ret = fast_test(console, random_text)
    if not ret:
        overall_result = False
        print("Fast test failed")
