import sys
from time import sleep
from anki_commands import invoke, request
from bs4 import BeautifulSoup
import requests
import os
from PIL import Image

kICON_HEIGHT = 1000
kAUDIO_PATH = "audio"
kIMG_PATH = "imgs"
kLOCAL_DIR = os.getcwd()
kHEADERS = headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}

# note type
kMODEL_NAME= "JapaneseNoteOneSide"
# deck name
kDECK_NAME = "Japanese Kotobank"
# fields for note
kNOTE_FIELDS= {
    'Japanese Example Sentence':'',
    'Expression':'',
    'Image':'',
    'Japanese Definition':'',
    'Pronunciation (Kana/Pinyin)':'',
    'Test Word Alone?':'',
    'Recording':'',
    'Kanji':'',
    'Pronunciation (Pitch)':''
}
#url
kSITE_URL_BASE="https://yourei.jp/"

def strGetExampleSentence(strWord):
    """
    Gets example sentence from yourei.jp
    """
    res = requests.get(kSITE_URL_BASE+strWord,headers=kHEADERS)
    soup = BeautifulSoup(res.text,'html.parser')
    # get the first sentence
    strSentence= soup.find(id='sentence-1').text.split('...')[0]
    # try to shorten the sentence
    for line in strSentence.split('。'):
        if strWord in line:
            return line
    return strSentence

def strGetDefinitions(strWord):
    """
    Get definitions from goo.jp
    """
    strBaseUrl = "https://dictionary.goo.ne.jp/word/"

    strRes = ""

    res = requests.get(strBaseUrl + strWord)
    soup = BeautifulSoup(res.text,'html.parser')
    listElementDefs = soup.find_all('div',{'class':'meaning'})
    if len(listElementDefs) == 0:
        listElementDefs = soup.find_all('div',{'class':'meanging'})
    for e in listElementDefs:
        for e in listElementDefs:
            strText = " ".join(e.get_text().split())
            strRes += strText

    return strRes.strip()

# Given a formatted query (see strFormatQuery)
# create a GoogleImages formatted URL.
def strCreateUrlFromFormattedQuery(strQuery):
    # creates a url that GoogleImages can understand
    retStr = "https://www.google.com/search?q={}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwiXt8DEr-n3AhXymeAKHRK1ASUQ_AUoAXoECAEQAw&biw=960&bih=871&dpr=1".format(strQuery)

    return retStr

# Get an image link from Google Images.
# Gets the first image available.
# Thus it performs no checks as to the accuracy of the image,
# or the licensing.
def strGetFirstImgLink(query):
    """
    Output: an image link.
    Input: a formated query string (see `strFormatQuery`)
    """
    # request the html page
    req = requests.get(query)

    # format it with bs4
    soup = BeautifulSoup(req.content,'html.parser')

    res = soup.select('img[src^=http]')
    if(len(res) != 0):
        return res[0]['src']
    else:
        raise Exception

# Download an image given an image link.
#
def voidDownloadImgFromLink(strFilePath,strLink):
    # save to file

    with open(strFilePath,'wb') as f:
        f.write(requests.get(strLink).content)
# Resize an image.
# NOTE THAT THIS OVERWRITES THE IMAGE.
#
def voidResizeImgFile(strFilePath,intWidth,intHeight):
    img = Image.open(strFilePath).convert('RGB')
    img.thumbnail(size=(intWidth,intHeight))
    img.save(strFilePath,optimize=True,quality=50)

# Search a query and download the first image that appears.
# Note that this does not take into account
# the accuracy of the image or the licensing.
def voidSearchAndDownloadTopImg(strQuery,strFilePath):
    # prepare the query
    strFormattedQuery = strCreateUrlFromFormattedQuery(strQuery)

    strImgLink = strGetFirstImgLink(strFormattedQuery)

    voidDownloadImgFromLink(strFilePath,strImgLink)
    img = Image.open(strFilePath)
    wperc = (kICON_HEIGHT/ float(img.size[1]))
    wsize = int((float(img.size[0])*float(wperc)))
    voidResizeImgFile(strFilePath,wsize,kICON_HEIGHT)

def voidGenAudio(strWord,strSentence):
    """
    Generate audio for sentence.
    """
    cmd = "pipenv run tts --text '{}' --model_name 'tts_models/ja/kokoro/tacotron2-DDC' --out_path '{}/{}/{}.mp3'".format('.' + strSentence,kLOCAL_DIR,kAUDIO_PATH,strWord.strip())
    os.system(cmd)


def voidCreateNote(strExpression, strExampleSentence):
    """
    Make a card with expression and example sentence
    """


    # remove new lines
    strExpression = strExpression.strip()

    audioPath = '{}/{}/{}.mp3'.format(kLOCAL_DIR,kAUDIO_PATH,strExpression)
    imgPath = '{}/{}/{}.jpg'.format(kLOCAL_DIR,kIMG_PATH,strExpression)

    # gen audio
    voidGenAudio(strExpression,strExampleSentence)
    # gen image
    voidSearchAndDownloadTopImg(strExpression,imgPath)


    noteFields = kNOTE_FIELDS
    noteFields['Expression'] = strExpression
    noteFields['Japanese Example Sentence'] = strExampleSentence.replace(strExpression,'___')
    noteFields['Japanese Definition'] = strGetDefinitions(strExpression)

    note = {
        'deckName':kDECK_NAME,
        'modelName':kMODEL_NAME,
        'fields':noteFields,
        'options':{
            'allowDuplicate':True,
        },
        "audio":[{
            'path':audioPath,
            'filename':'my_audio__{}.mp3'.format(strExpression),
            'fields':['Recording','Audio']
        }]
        ,
        "picture":[{
            'path':imgPath,
            'filename':'my_img__{}.jpg'.format(strExpression),
            'fields':['Image']
        }]
    }

    invoke('addNote',note=note)
    # delete audio after
    os.remove(audioPath)
    # delete img after
    os.remove(imgPath)

if __name__ == "__main__":
    # get args
    args = sys.argv
    if len(args) != 2:
        print("usage:\npython3 gen.py [TEXT FILE]")
        exit(1)

    listErrorWords = []
  
    strTextFileName = args[1]
    # get permissions
    with open(strTextFileName,'r') as f:
        for line in f:
            try:

                strExampleSentence = strGetExampleSentence(line.strip())
                if line != '' and strExampleSentence != '':
                    voidCreateNote(line,strExampleSentence)
                else:
                    print('either line or example sentence is missing for: {line}')
                
                sleep(0.5)
            except Exception as e:
                print('*************')
                print(e)
                print('word: {}'.format(line))
                print('*************')
