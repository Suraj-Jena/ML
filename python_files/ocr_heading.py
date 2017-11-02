import re
import string

import pandas as pd
from sklearn import model_selection
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

dataset = pd.read_csv(r'D:\backup\PycharmProjects\test\Image Batches-20171017T131547Z-001\Not_Success_rows_ver.csv',
                      encoding='cp1256')
dataset = dataset[dataset['page_type_final'] == 'remittance'].reset_index()
print(dataset.shape)


# countVectorizer = CountVectorizer(tokenizer=cleanandstem, min_df=50,max_df=0.5, stop_words='english')
# theString = countVectorizer.fit_transform(dataset['row_string'])
# this function is used to remove punctuations marks and also removes stop words like 'the' , 'a' ,'an'
def cleaning(sentence):
    punctuation_removed = [char for char in sentence if char not in string.punctuation]
    punctuation_removed = [char for char in punctuation_removed if char not in string.digits]
    punctuation_removed = "".join(punctuation_removed)
    l = [word.lower() for word in punctuation_removed.split()]
    return [word for word in l if len(word) > 2]


'''
.*((inv)|(policy)).*
'''

pattern = re.compile('.*((^|\s)((inv)|(pol)|(doc)|(net)|(num))).*')


def containsNumber(x):
    i = 0
    for s in x:
        try:
            if int(s):
                i = i + 1
        except ValueError:
            d = 0
            continue
    return i


def funcRegEx(x):
    st = str(x).lower().strip()
    i = containsNumber(st)
    if i <= 2:
        if pattern.fullmatch(str(x).lower().strip()):
            return 1
        else:
            return 0
    else:
        return 0


def cleaning_new(sentence):
    fd = '?-+/\\.,'
    punctuation_removed = [char for char in sentence if char not in fd]
    punctuation_removed = "".join(punctuation_removed)
    l = [word.lower() for word in punctuation_removed.split()]
    return ' '.join(l)


# applying both together
def cleanandstem(sentence):
    return cleaning(sentence)


pat = re.compile('([a-zA-Z]*[0-9]+).*([$]?[0-9]*[\,]?[0-9]*[\.]?[0-9]+)')
pat2 = re.compile('([$]?[0-9]*[\,]?[0-9]*[\.][0-9]+)')


def checkHeading(dataset1):
    i = -1
    for e in range(0, len(dataset1)):
        if dataset1.loc[e]['heading'] == 1:
            for r in range(1, 6):
                s = dataset1.loc[e + r]['row_string']

                # print(s)
                if pat.fullmatch(str(s).lower().strip()) is not None:
                    i = 1
                    break
                else:
                    i = 0
            if i == 0:
                # print(dataset1.loc[e]['row_string'])
                dataset1.loc[e, 'heading'] = 0
                print(dataset1.loc[e]['heading'])
    return dataset1


dataset['row_string'] = dataset['row_string'].apply(cleaning_new)
dataset['heading'] = dataset['row_string'].apply(funcRegEx)
# dataset = checkHeading(dataset)
tfidf = CountVectorizer(tokenizer=cleanandstem, min_df=100, stop_words='english',
                        vocabulary=['invoice', 'policy', 'gross', 'net', 'number', 'date', 'paid', 'document',
                                    'description', 'discount', 'inv'])
theString = tfidf.fit_transform(dataset['row_string'])
combine1 = pd.DataFrame(theString.todense())
combine1.columns = tfidf.get_feature_names()
print(combine1.columns)
X = dataset.loc[:, ['heading']]
X = pd.concat([combine1.reset_index(drop=True), X.reset_index(drop=True)], axis=1, ignore_index=True)
Y = dataset.loc[:, 'is_heading']
validation_size = 0.2
seed = 20
X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size,
                                                                                random_state=seed)


def func(x):
    if x['total'] == 1 and x['pred_proba_0'] < 0.8 and x['pred'] == 0:
        return 1
    return x['pred']


rfc = RandomForestClassifier(n_estimators=200, )
rfc.fit(X_train, Y_train)
predictions = rfc.predict(X_validation)
predictions_prob = rfc.predict_proba(X_validation)
pred_prob = pd.DataFrame(data=predictions_prob, columns=[0, 1])
det = pd.DataFrame({"y_val": Y_validation.copy(deep=False).values, "total":
    X_validation.copy(deep=False).iloc[:, -2].values, "pred": predictions, "pred_proba_0": pred_prob[0],
                    "pred_proba_1": pred_prob[1]})
# det['pred'] = det.apply(func, axis=1)
a4 = pd.DataFrame(data=predictions, columns=['predictions'])

print(accuracy_score(det['y_val'], det['pred']))
print(confusion_matrix(det['y_val'], det['pred']))
print(classification_report(det['y_val'], det['pred']))

print(accuracy_score(Y_validation, X_validation.iloc[:, -1].values))
print(confusion_matrix(Y_validation, X_validation.iloc[:, -1].values))
print(classification_report(Y_validation, X_validation.iloc[:, -1].values))

dataset[dataset['is_heading'] != dataset['heading']].loc[:, ['row_string', 'is_heading', 'heading']] \
    .to_csv('ocr_heading.csv')
