import cv2
import numpy as np

import easyocr
import matplotlib.pyplot as plt
import mss
from pynput.keyboard import Key, Controller
from time import sleep, time

keyboard = Controller()

with open("decks.txt", "r") as infile:
    raw = infile.read()

with open("config.txt", "r") as infile:
    CONFIG = infile.readlines()

CONFIG = [int(CONFIG[0]), float(CONFIG[1]), float(CONFIG[2])]

decks_process = [[y.strip() for y in x.strip().split("\n")] for x in raw.split("\n\n")]


def process_deck(deck, i=0):
    if i >= len(deck):
        return [deck]
    result = []
    if "|" in deck[i]:
        for variation in deck[i].split("|"):
            result.extend(
                process_deck(deck[:i] + [variation.strip()] + deck[i + 1 :], i + 1)
            )
    return result or process_deck(deck, i + 1)


decks = []

for deck in decks_process:
    decks.extend(process_deck(deck))


reader = easyocr.Reader(["en"], gpu=False)


def if_target(options, target_decks):
    for deck in target_decks:
        for i, option in enumerate(options):
            if option in deck:
                keyboard.press(str(i + 1))
                sleep(CONFIG[2])
                keyboard.release(str(i + 1))
                sleep(CONFIG[1])

                new_targets = []
                for purgedeck in target_decks:
                    if option in purgedeck:
                        purgedeck.remove(option)
                        new_targets.append(purgedeck)

                return option, new_targets
    return False


# burn = 0

target_decks = [[y for y in x] for x in decks]
final_selection = []
with mss.mss() as sct:

    # Grab frames in an endless lopp until q key is pressed
    # print(sct.monitors)
    while True:
        # Iterate over the list of monitors, and grab one frame from each monitor (ignore index 0)
        for monitor_number, mon in enumerate(sct.monitors[CONFIG[0] : CONFIG[0] + 1]):
            monitor = {
                "top": mon["top"],
                "left": mon["left"],
                "width": mon["width"],
                "height": mon["height"],
                "mon": monitor_number,
            }  # Not used in the example

            # Grab the data
            img = np.array(
                sct.grab(mon)
            )  # BGRA Image (the format BGRA, at leat in Windows 10).

            # if time() < burn:
            #     continue

            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            y = int(0.340 * img.shape[0])
            x = [int(n * img.shape[1]) for n in [0.168, 0.340, 0.512]]

            yb = int(0.049 * img.shape[0])
            xb = int(0.109 * img.shape[1])

            options = []

            for i in range(3):
                crop = img[y : y + yb, x[i] : x[i] + xb]
                # cv2.imwrite("bla.png", img[y : y + yb, x[i] : x[i] + xb])
                options.append(
                    " ".join(
                        [x.strip().lower() for x in reader.readtext(crop, detail=0)]
                    )
                )

            print(options)

            if sel := if_target(options, target_decks):
                final_selection.append(sel[0])
                target_decks = sel[1]

                if len(final_selection) == 8:
                    break
            else:
                target_decks = [[y for y in x] for x in decks]
                final_selection = []
                keyboard.press(Key.esc)
                sleep(CONFIG[2])
                keyboard.release(Key.esc)
                sleep(CONFIG[2])
                keyboard.press(Key.enter)
                sleep(CONFIG[2])
                keyboard.release(Key.enter)
                sleep(CONFIG[1])
                # burn = time() + 1.5


cv2.destroyAllWindows()
