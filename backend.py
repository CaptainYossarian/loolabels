"""Drew Guyer 2017
Loolabels GPL v3
"""


import cv2
import nltk
import pickle
import pytesseract
import re
import sqlite3
import sys
import wikipedia
from PIL import Image
from google import search




SAMPLE = '/home/drg/cs/pycode/loolabels/images/sample.jpg'
SHAMPOO = '/home/drg/cs/loolabels/images/shampoo.jpg'
CANDY = '/home/drg/cs/pycode/loolabels/images/candy.jpg'
TOOTHPASTE = '/home/drg/cs/pycode/loolabels/images/toothpaste.png'
HANDSOAP = '/home/drg/cs/pycode/loolabels/images/handsoap.jpg'

def ocr_image_tostring(image):
    """Takes an image (png, jpeg, gif, tiff, bmp, etc) and converts the contents into a string.

    Args: image -- path to the image file
    Returns: string representation of the image contents
    """


    ok = pytesseract.image_to_string(Image.open(image))
    return ok


def tokenize_label_string(imagestring):
    """
    Tokenizes a string using nltk (currently an improved TreebankWordTokenizer along with PunktSentenceTokenizer
    for the specified language).

    Args: imagestring -- the string representation of an image to be tokenized
    Returns: tokenized string
    """
    tokens = nltk.word_tokenize(imagestring)
    return tokens


def preprocess_image(image, adaptive_method, thresh_type, blur_type):
    """Takes and image and cleans it up so that it can be optically recognized with more accuracy,
    then writes it to back over the image file.

    Args: image -- path of image to be cleaned up
          adaptive_method -- cv2.ADAPTIVE_THRESH_MEAN_C ; cv2.ADAPTIVE_THRESH_GAUSSIAN_C
          thresh_type -- cv2.THRESH_BINARY ; cv2.THRESH_BINARY_INV
          blur_type -- GaussianBlur ; medianBlur ; bilateralFilter
    """
    original = cv2.imread(image)
    imgray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    ready = cv2.adaptiveThreshold(imgray, 255, adaptive_method, thresh_type, 11, 5)

    if blur_type == "GaussianBlur":
        blur = cv2.GaussianBlur(ready, (5, 5), 0)
    elif blur_type == "medianBlur":
        blur = cv2.medianBlur(ready, 5)
    else:
        blur = cv2.bilateralFilter(ready, 9, 75, 75)

    cv2.imwrite(image, blur)


def clean_up_string(dirty_string):
    """Takes a string and parses the elements between periods and commas

    Args: dirty_string -- unsanitized string
    Returns: cleaned up string with no punctuation or new lines
    """
    ds = dirty_string
    ds = ds.replace("\n", "")
    ds = ds.replace("'", "")
    clean_string = re.split('[;,./]', ds)
    return clean_string


def save_for_later(obj):
    """Pickles an object and saves it to hardcoded file

    Args: obj-- desired object to be pickled and saved
    """
    filehandler = open('/home/drg/cs/pycode/loolabels/saved.txt', 'w')
    pickle.dump(obj, filehandler)


def load_from_before():
    """Loads a pickled file from hardcoded disk location

    Returns: pickled file
    """
    filehandler = open('/home/drg/cs/pycode/loolabels/saved.txt', 'r')
    previous = pickle.load(filehandler)
    return previous


def get_wikipedia_url(item):
    page = wikipedia.page(str(item))
    return page.url


def save_to_database(p):
    def myGen(p):
        for key in p:
            yield key, p[key]


    conn = sqlite3.connect('/home/drg/cs/pycode/loolabels/ingredients.db')
    c = conn.cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS products(ingredients TEXT PRIMARY KEY, wikipedia TEXT)")

        #for key in p:
           #c.execute("INSERT OR IGNORE INTO products VALUES(?,?)", (key, p[key]))
        c.executemany("INSERT OR IGNORE INTO products VALUES(?,?)", p.iteritems())

    except Exception as e:
        print "Error accessing Database"
    finally:
        conn.commit()
        conn.close()


# noinspection PyBroadException
def update_links(p):
    print"~~Gathering urls. This may take a bit"
    for ele in p:
        if p[ele] == "":
            try:
                print "UPDATING URLS\n"
                x = google_query(str(ele), "wikipedia")
                y = x.rsplit("/", 1)[1]
                p[y] = x
                del p[ele]
            except Exception:
                "AINT SHIT HERE"


def google_query(target, desired_url):
    for url in search(target, stop=20):
        if desired_url in url:
            return url


# noinspection PyBroadException
def main(image):
    try:
        preprocess_image(image, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, "bilateralFilter")
        temp = ocr_image_tostring(image)
        sanitized_string = clean_up_string(temp)
    except Exception as e:
        print e.message
        print "~~1) Image not found/path misspelled 2)Error converting image 3) Other ~~"
        sys.exit(1)
    for ele in sanitized_string:
        print ele

    urls = {}
#load_from_before()
    for ele in sanitized_string:
        try:
            urls[ele] = get_wikipedia_url(ele)
        except Exception:
            urls[ele] = ""
    update_links(urls)
    for ele in urls:
        print ele.strip() + "----->"
        print urls[ele]+"\n"
    save_to_database(urls)
#save_for_later(urls)


if __name__ == "__main__":
    main(HANDSOAP)

