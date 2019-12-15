
from bs4 import BeautifulSoup
import requests
import pandas as pd
import string
import numpy as np
import re
import nltk
import itertools
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

def web_crawl(urls):

  """This function takes in a list of urls and returns
     a dictionary with each word as an index and the values as
     the occurence list of each word"""

  tags = ['h1',"h2","h3","h4","h5","h6","p","li"]
  global  docids
  docids = []
  master_dict = {}

  for url in urls:
    docids.append(url)
    r = requests.get(url)
    s = BeautifulSoup(r.content, 'html.parser')

    #find text, get only text, append to array
    words = []
    for tag in tags:
      for text in s.find_all(tag):
        temp = text.get_text()
        words.append(temp)

    text = []
    for item in words:
      #Breaks down sentences into individual words
      text.append(word_tokenize(item))

    #flatten list of list to one list
    flattened_list  = list(itertools.chain(*text))
    words = [word.lower() for word in flattened_list]

    #gets stop words in english and removes them
    stop_words = set(stopwords.words('english'))
    filtered_list = [w for w in words if not w in stop_words]

    #Removes alphanumeric
    flat_list = [re.sub('\w*\d\w*', '', text) for text in filtered_list]

    #Removes punctuations
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in flat_list]
    stripped = [word for word in stripped if len(word) > 1]
    master_dict = store_info(stripped, master_dict)

  return master_dict

def store_info(flat_list,master_dict):

    """This function takes in a list of words for each webpage
        and a master dictionary and updates the information in the
        dictionary based on the words present"""

  for word in flat_list:
    if word not in master_dict.keys():   #If the word is not present, create a new occurance it
      temp = [(len(docids)-1,1)]
      master_dict.update({word : temp })
    else:
      temp = master_dict[word]
      docid,freq = temp[-1]
      if docid == len(docids) - 1:  #If we are on the same webpages, update the word frequency
        temp[-1] = (docid,freq+1)
      else:
        temp.append((len(docids)-1, 1))
        master_dict.update({word: temp})

  return master_dict

def addtotrie(word,head,wordtmp):
    """This function takes in a word, the current node and a temp copy of the words_dict
       It add a new word into the trie compressing words along the way. It returns
       the root node with an updated compressed trie"""
  _notend = '*'
  node = head
  check = False

  for n in node.keys():

    prefix = commonPrefix(word,n)  #Finds the prefix between two words

    if len(prefix) > 0:
      check = True
      num = len(prefix)
      otherword = word[num:]  #Get the rest of the word after the prefix is removed

      #If the prefix is less then the current node length then we traverse downwards
      if num < len(n):
        otherhalf = n[num:] #Other half of the node without the prefix
        temp = node[n]

        #add in the prefix as a key
        node[prefix] = ({},_notend)
        node,is_terminal = node[prefix]

        #Assign and reconstruct the new nodes
        node[otherhalf] = temp
        node[otherword] = ({},words_dict[wordtmp])

        node = head
        del node[n]
        break
      else:

        node,is_terminal = node[n]
        node = addtotrie(otherword,node,wordtmp)
        node = head
        break
   #If the word did not exist in keys, create a new entry of it.
  if check == False:
    node[word] =  ({},words_dict[wordtmp])

  return node

def add_words(new_dict):
    """This function initiates the compressed trie creation"""
  _notend = '*'
  root = ({}, _notend)
  node, is_terminal = root

  for word in new_dict.keys():
    wordtmp = word
    node = addtotrie(word,node,wordtmp)
  root = node,is_terminal
  return root

#Find the common prefix between two words
def commonPrefix(str1, str2):
  n1 = len(str1)
  n2 = len(str2)
  result = ""
	# Compare str1 and str2
  j = 0
  i = 0
  while(i <= n1 - 1 and j <= n2 - 1):
    if (str1[i] != str2[j]):
      break
    result += (str1[i])
    i += 1
    j += 1

  #print("result is:" + result)
  return result

#This function traverses through the compressed trie to find match word
def find_word_in_trie(trie,word):

  node,terminal = trie
  num_word = len(word)
  flag = False

  for n in node.keys():
    prefix = commonPrefix(word,n)

    if len(prefix) < 0: #The index matched no prefix in the word
      continue  #continue to next key

    if len(prefix) > 0: #The index matched with a prefix in the word

      flag = True
      num_prefix = len(prefix)
      temp_word = word[num_prefix:] #Get a new word with the prefix removed

      if len(temp_word) > 0:        #If len of new word is greater we recursively call find_word_in_trie again
        flag = find_word_in_trie(node[n],temp_word)
        break

      if len(temp_word) == 0: #The prefix matched was the entire word
        node,terminal = node[n]
        if len(node.keys()) > 0:
          if "" in node.keys():
            _,terminal = node['']
            return terminal #return the terminal entry
          else:
            return terminal
        elif len(node.keys()) == 0:
          return terminal

  return flag

#This function takes in user search query and cleans it for use i find word in trie
def process_user_input(search):

  indi_words = word_tokenize(search) #Breaks down sentences into individual words
  indi_words = [word.lower() for word in indi_words] #lowercase
  stop_words = set(stopwords.words('english'))
  indi_words = [w for w in indi_words if not w in stop_words]  #Removes stop words from our word list
  indi_words = [re.sub('\w*\d\w*', '', text) for text in indi_words] #Removes alphanumeric words or words that contain numbers

  import string
  table = str.maketrans('', '', string.punctuation)
  indi_words = [w.translate(table) for w in indi_words]

  indi_words = [word for word in indi_words if len(word) > 0]

  return indi_words

#Important function number 1000
def rank_results(results):

  sums = []
  count = list(np.zeros(len(docids)))
  ranked = pd.DataFrame()
  for sect in results:

    word = sect[0]  #gets the word
    occ_list = sect[1] #gets the occurence list

    if occ_list == False:
      continue
    elif occ_list == '*':
        continue
    else:

      for n in range(len(docids)):
        for entry in occ_list:
          id,freq = entry
          if id == n:
            count[n] = count[n] + freq

      docid_present = [id for id,_ in occ_list]  #gets the docids that match with the word

      true_false_list = [] #used to create a list of 1 and 0 to indicate whether a word is present in a docid

      for n in range(len(docids)):
        if n in docid_present:
          true_false_list.append(1)
        else:
          true_false_list.append(0)

      ranked[word] = true_false_list #Create a new column with word as heading and true_false list

  for index in range(len(ranked)):  #Create a list of each row summed
    sums.append(ranked.iloc[index].sum())

  ranked["Total Hits"] = sums
  ranked["Total Frequency"] = count

  #Sorts the dataframe based on two column criterias
  ranked.sort_values(['Total Hits', 'Total Frequency'], ascending=[False, False], inplace = True)

  return ranked

def main():
    f = open("websites.txt","r")
    if f.mode == "r":
      contents = f.readlines()

    contents = [link.split("\n")[0] for link in contents] #Strip out the /n from each link

    global words_dict
    words_dict = web_crawl(contents) #Perform the scrapping and indexing operations on our urls
    trie = add_words(words_dict)     #Constructs our compressed trie

    while True:

      choice = input("Type yes to search on, no to stop: ")
      choice = choice.lower()
      if choice == "yes":
        search = input("What's your search query: ?")
        words_to_search = process_user_input(search) #Processign the search query
        print(words_to_search)
        result = []

        if len(words_to_search) == 0:
          print("No words match your search query")
        else:

          for word in words_to_search:   #For each word input, find and return its occurence list
            result.append((word,find_word_in_trie(trie,word)))

          ranked = rank_results(result)
          if (ranked.isnull().values.any() == True):
            print("No words match your search query")
          else:
            indexes = list(ranked.index)
            print("The top four search results are: ")
            for n in indexes[:4]:
              print(str(docids[n]))  #Prints the top four matched pages

      elif choice == "no":
        print("Thanks for visitng!")
        break
      else:
        pass


if__name__ == "__main__":
    main()
