import sys
from anki_commands import invoke, request
from bs4 import BeautifulSoup
import requests
import os

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


def voidGenAudio(strWord,strSentence):
    """
    Generate audio for sentence.
    """
    cmd = "edge-tts --voice ja-JP-NanamiNeural --text '{}' --write-media audio/{}.mp3".format(strSentence,strWord.strip())
    os.system(cmd)


def voidCreateNote(strExpression, strExampleSentence):
    """
    Make a card with expression and example sentence
    """
    noteFields = kNOTE_FIELDS

    noteFields['Expression'] = strExpression
    noteFields['Japanese Example Sentence'] = strExampleSentence.replace(strExpression.strip(),'___')
    noteFields['Test Word Alone?'] = "y"
    noteFields['Japanese Definition'] = strGetDefinitions(strExpression)

    note = {
        'deckName':kDECK_NAME,
        'modelName':kMODEL_NAME,
        'fields':noteFields,
        'options':{
            'allowDuplicate':True,
        },
        "audio":[{
            'path':'{}/audio/{}.mp3'.format(os.getcwd(),strExpression.strip()),
            'filename':'my_audio__{}.mp3'.format(strExpression.strip()),
            'fields':['Recording']
        }]
        
    }
    invoke('addNote',note=note)
    # delete audio after
    os.remove('audio/{}.mp3'.format(strExpression.strip()))

def strGetExampleSentence(strWord):
    """
    Gets example sentence from yourei.jp
    """
    res = requests.get(kSITE_URL_BASE+strWord)
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
    listElementDefs = soup.find_all('ol',{'class':'meaning cx'})
    for e in listElementDefs:
        strRes += e.find('p',{'class':'text'}).get_text() + "\n"
    return strRes

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
                    voidGenAudio(line,strExampleSentence)
                    voidCreateNote(line,strExampleSentence)
                else:
                    print('either line or example sentence is missing for: {line}')
            except Exception as e:
                print('*************')
                print(e)
                print('word: {}'.format(line))
                print('*************')
    # write the errors
    with open('error_words.txt','w') as f:
        for word in listErrorWords:
            f.write(word)