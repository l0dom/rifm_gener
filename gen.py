__author__ = 'Андрей'
import re
import os
import collections
import codecs
import pickle
import argparse

from random import uniform
ext=(".bbe",".bbr",".tbe",".tbr")
rus_alphabet = re.compile('[а-яА-Я-]+|[.,:;?!]')
eng_alphabet = re.compile('[a-zA-Z-]+|[.,:;?!]')
direct="moduls/"
hdirect="history/"

class Bredogener():
    
    def __init__ (self,arg):
        self.chance = {}
        self.files = {ext[0]:[],ext[1]:[],ext[2]:[],ext[3]:[]}
        self.hfiles = {ext[0]:[],ext[1]:[],ext[2]:[],ext[3]:[]}
        self.num_simbols = 0
        self.min_words = arg.min_words
        self.max_words = arg.max_words
        self.num_sentens = arg.num_sentens
        self.param = list(arg.param)
        self.name_of_file = arg.file if arg.file[-4:]==".txt" else arg.file+".txt"
        self.alphabet = eng_alphabet if "eng" in self.param else rus_alphabet
        self.text_cod = arg.text_code
        self.type = ".bb" if "bg" in self.param else ".tb"
        self.type += "e" if "eng" in self.param else "r"

        if not os.path.exists(direct):
            os.mkdir(direct)
        if not os.path.exists(hdirect):
            os.mkdir(hdirect)
        if not os.path.exists(hdirect+"history"+self.type):
            self.__dump_model("history.txt")
        if not os.path.exists(hdirect+"history.nms"):
            self.__dump_names()


    #Генератор строк. Возвращает строки из файла
    def __gen_lines(self,file):
        with codecs.open(file, "r", self.text_cod) as data:
            for line in data:
                yield line.lower()

    #Генератор слов из строк
    def __gen_tokens(self,lines,alphabet):
        for line in lines:
            for token in self.alphabet.findall(line):
                yield token

    #Генератор триграмов
    def __gen_trigrams(self,tokens):
        t0, t1 = '$', '$'
        for t2 in tokens:
            yield t0, t1, t2
            if t2 in '.!?':
                yield t1, t2, '$'
                yield t2, '$','$'
                t0, t1 = '$', '$'
            else:
                t0, t1 = t1, t2

    #Генератор биграмов
    def __gen_bigrams(self,tokens):
        t0 = '$'
        for t1 in tokens:
            yield t0, t1
            if t1 in'.!?':
                yield t1, '$'
                t0 = '$'
            else:
                t0 = t1

    #Подсчет шансов
    def __tri_training (self,file_name):
        lines=self.__gen_lines(file_name)
        token=self.__gen_tokens(lines,self.alphabet)
        trigrams = self.__gen_trigrams(token)

        bi, tri = collections.defaultdict(lambda: 0.0),  collections.defaultdict(lambda: 0.0)

        for t0, t1, t2 in trigrams:
            bi[t0, t1] += 1
            tri[t0, t1, t2] += 1


        chance = {}
        for (t0,t1),ch in bi.items():
            chance[t0,t1]={}

        for (t0, t1, t2), ch in tri.items():
            chance[t0, t1][t2] =  ch/bi[t0, t1]
        return self.__len_of_file(file_name),chance

    #Возвращает бредопредложение
    def __tri_generate_sentence(self):
        phrase = ''
        n=0
        t0, t1 = '$', '$'
        while n<=self.min_words:
            phrase = ''
            n=0
            t0, t1 = '$', '$'
            while n!=self.max_words:
                tmp = self.__unirand(self.chance[t0, t1])
                t0, t1 = t1, tmp
                if t1 == '$': break
                if t1 in ('.!?,;:') or t0 == '$':
                    phrase += t1
                else:
                    phrase += ' ' + t1
                n+=1
        return phrase.capitalize()

    #Рандом слов
    def __unirand(self,seq):
        sum_, freq_ = 0, 0
        for i in seq:
            sum_ += seq[i]
        rnd = uniform(0, sum_)
        for i in seq:
            freq_ += seq[i]
            if rnd < freq_:
                return i

    def __bi_training(self,file_name):
        lines=self.__gen_lines(file_name)
        token=self.__gen_tokens(lines,self.alphabet)
        bigrams=self.__gen_bigrams(token)

        one,bi = collections.defaultdict(lambda: 0.0),collections.defaultdict(lambda: 0.0)

        for t0, t1 in bigrams:
            bi[t0, t1] += 1
            one[t0]+=1

        chance = {}
        for t0,ch in one.items():
            chance[t0]={}

        for (t0, t1), ch in bi.items():
            chance[t0][t1] =  ch/one[t0]
        return self.__len_of_file(file_name),chance

    def __bi_generate_sentence(self):
        phrase = ""
        n=0
        t='$'
        while n<=self.min_words:
            phrase = ""
            n=0
            t='$'
            while n!=self.max_words:
                tmp = self.__unirand(self.chance[t])
                if tmp == '$': break
                if tmp in ('.!?,;:') or t == '$':
                    phrase += tmp
                else:
                    phrase += ' ' + tmp
                t=tmp
                n+=1
        return phrase.capitalize()

    def __sentens(self):
        text = ""
        for i in range(self.num_sentens):
            text+=self.__bi_generate_sentence() if (self.type[:3]==".bb") else self.__tri_generate_sentence()
        return text

    #Возвращает колю символов в файле
    def __len_of_file(self,file_name):
        with codecs.open(file_name,"r",self.text_cod) as f:
            return len(f.read())

    def __dump_model (self,file_name):
        tmp = hdirect if file_name=="history.txt" else direct
        with open(tmp+file_name.replace(".txt",self.type), "wb") as data:
            pickle.dump((self.num_simbols,self.chance),data)

    def __load_model (self,file_name):
        tmp = hdirect if file_name=="history.txt" else direct
        with open(tmp+file_name.replace(".txt",self.type),"rb") as data:
            self.num_simbols,self.chance = pickle.load(data)

    def __dump_names (self):
        with open (hdirect+"history.nms","wb") as data:
            pickle.dump(self.hfiles,data)

    def __load_names (self):
        with open (hdirect+"history.nms","rb") as data:
            self.hfiles=pickle.load(data)
        for i in os.listdir(direct):
            if i[-4:] in ext:
                self.files[i[-4:]].append(i.replace(i[-4:],""))


    def add_to_history (self):
        with open(hdirect + "history" + self.type,"rb") as data:
            hnum,hchance = pickle.load(data)
        coef=hnum/(self.num_simbols+hnum)

        for i in hchance:
            for j in hchance[i]: hchance[i][j]*=coef

        for i in self.chance:
            if i not in hchance:
                hchance[i]={}
            for j in self.chance[i]:
                if j in hchance[i]:
                    hchance[i][j]+=self.chance[i][j]*(1-coef)
                else:
                    hchance[i][j]=self.chance[i][j]*(1-coef)

        with open(hdirect+"history"+self.type,"wb") as data:
            pickle.dump((self.num_simbols+hnum,hchance),data)

        self.hfiles[self.type].append(self.name_of_file)

    def work (self):
        #Подготовка модели

        self.__load_names()
        if self.name_of_file!="history.txt":
            if not os.path.exists(self.name_of_file):
                print ("Отсутсвует указанный файл")
                return
            if self.name_of_file not in self.files[self.type] or "dcm" in self.param:
                self.num_simbols, self.chance = self.__bi_training(self.name_of_file) if (self.type[:3]==".bb") else \
                    self.__tri_training(self.name_of_file)
            else:
                self.__load_model(self.name_of_file)
                self.param.append("dsm")
        else:
            self.__load_model(self.name_of_file)
            self.param.append("nhm")
        #Дамп модели
        if "nhm" not in self.param and self.name_of_file not in self.hfiles[self.type]:
            self.add_to_history()
        if "dsm" not in self.param and self.name_of_file not in self.files[self.type]:
            self.__dump_model(self.name_of_file)
        self.__dump_names()
        #Вывод результата

        return self.__sentens()


def parse_arg():
    parser=argparse.ArgumentParser(
        description='''Эта программа создает бред на основе изученного текстового файла, 
        Процесс обучения происходит на основе построения триграмов или биграмов, 
        После обучения генирация предложений может происходить по уже построенным моделям''',
        epilog=''' Автор программы Новиков Андрей.
        Автор программы не несет никакой ответсвенности ни за что.'''
    )
    parser.add_argument("-f","--file",default="history.txt",help="Имя файла обучения ")
    parser.add_argument("-w","--max_words",type=int,default=50,help="Максимальное число слов в предложении ")
    parser.add_argument("-m","--min_words",type=int,default=5,help="Минимальное число слов в предложении ")
    parser.add_argument("-s","--num_sentens",type=int,default=1,help="Число сгенерированных предложений ")
    parser.add_argument("-c","--text_code",choices=["utf-8","utf-16","utf-32"],\
                        default="utf-8",help="Выбор кодировки входного файла ")
    parser.add_argument("-p","--param",nargs='+', choices=["nhm","bg","dsm","eng","dcm"],default=[],help='''
        nhm(not history model) - модель триграмма(двуграмма)
        полученная из нового ресурса не добавляется к архиву моделей, 
        bg(bigram) - построение предложений на основе биграмов, а не триграмов, 
        dsm(don`t save model) - не сохранять новую модель в файл, 
        eng(english) - работать только с английскими текстами, 
        dcm(don^t check models) - не проверять уже существующие модели, 
    ''')
    return parser


def main():


    prog_args = parse_arg().parse_args()

    bred=Bredogener(prog_args)
    print(bred.work())
    print ("End of work")



if __name__=="__main__":
    main()