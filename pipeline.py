import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mltools as ml
import data_loader
import warnings
warnings.filterwarnings('ignore')

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder,FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, GridSearchCV, cross_validate
from sklearn.feature_selection import mutual_info_classif
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, BaggingClassifier, VotingClassifier
# load data (provided method)
train_data, valid_data = data_loader.load_train_data('Data/adult.data', valid_rate=0.1, is_df=True)
test_data = data_loader.load_test_data('Data/adult.test', is_df=True)

#update fields
native_country_dict={' ?': '?', ' Cambodia': 'Africa', ' Canada': 'North America', ' China': 'Asia', 
	' Columbia': 'Latin America', ' Cuba': 'Latin America', ' Dominican-Republic': 'Latin America', 
	' Ecuador': 'Latin America', ' El-Salvador': 'Latin America', ' England': 'Europe', 
	' France': 'Europe', ' Germany': 'Europe', ' Greece': 'Europe', ' Guatemala': 'Latin America', 
	' Haiti': 'Latin America', ' Holand-Netherlands': 'Europe', ' Honduras': 'Latin America', 
	' Hong': 'Asia', ' Hungary': 'Europe', ' India': 'Asia', ' Iran': 'Asia', ' Ireland': 'Europe', 
	' Italy': 'Europe', ' Jamaica': 'Latin America', ' Japan': 'Asia', ' Laos': 'SE Asia', 
	' Mexico': 'Latin America', ' Nicaragua': 'Latin America', ' Outlying-US(Guam-USVI-etc)': '?', 
	' Peru': 'Latin America', ' Philippines': 'Asia', ' Poland': 'Europe', ' Portugal': 'Europe', 
	' Puerto-Rico': 'Latin America', ' Scotland': 'Europe', ' South': '?', ' Taiwan': 'Asia', 
	' Thailand': 'SE Asia', ' Trinadad&Tobago': 'Latin America', ' United-States': 'North America', 
	' Vietnam': 'SE Asia', ' Yugoslavia': 'Europe'}
fields_to_update={'native-country': native_country_dict,
'relationship':
	{' Husband': 'Spouse', ' Not-in-family': 'Not-in-family', ' Other-relative': 'Distant', 
	' Own-child': 'Own-child', ' Unmarried': 'Unmarried', ' Wife': 'Spouse'},
'marital-status':
	{' Divorced': 'Split', ' Married-AF-spouse': 'Married', ' Married-civ-spouse': 'Married', 
	' Married-spouse-absent': 'Split', ' Never-married': 'Single', ' Separated': 'Split', 
	' Widowed': 'Split'},
'workclass':
	{' Federal-gov': 'Federal-gov', ' Local-gov': 'Local-gov', ' Never-worked': 'Unemployed',
	' State-gov': 'Local-gov', ' Without-pay': 'Unemployed'},
'income':{' <=50K':0,' >50K':1}
}

for field, changes in fields_to_update.items():
	train_data[field].replace(to_replace=changes,inplace=True)
	valid_data[field].replace(to_replace=changes,inplace=True)
	test_data[field].replace(to_replace=changes,inplace=True)
#drop unnecessary
train_data = train_data.drop(columns = ['fnlwgt', 'education'])
valid_data = valid_data.drop(columns = ['fnlwgt', 'education'])
test_data = test_data.drop(columns = ['fnlwgt', 'education'])
#numerical
num_features = ['age', 'education-num', 'capital-gain', 'capital-loss', 'hours-per-week']
num_transformer = Pipeline(steps = [('scaler', StandardScaler())])
#categorical
cat_features = ['workclass', 'marital-status', 'occupation', 'relationship', 'race', 'sex', 'native-country']
cat_transformer = Pipeline(steps = [('imputer', SimpleImputer(missing_values = ' ?',strategy = 'constant')),
                                    ('onehot', OneHotEncoder(handle_unknown = 'ignore'))])
# create preprocessor containing above pipelines
preprocessor = ColumnTransformer(transformers=[('num', num_transformer, num_features), 
                                               ('cat', cat_transformer, cat_features)])
# create various pipelines, each invoking the preprocessor and a different classifier

# Logistic Regression

gb=GradientBoostingClassifier()
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                            ('clf', gb)])
##print(pipeline.get_params().keys())
#split into X and Y
X = train_data.drop(columns = 'income')
Y = train_data['income']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = .2)

classifiers={
'LR':LogisticRegression(),'LinSVC':LinearSVC(dual = False),#GaussianNB(priors = None),
'RandForest':RandomForestClassifier(),'GradBoost':GradientBoostingClassifier(),'SVC':SVC(),
'Bag':BaggingClassifier(GradientBoostingClassifier(),max_samples = 0.2,max_features = 0.8,bootstrap_features = True)}

# for c in classifiers:
#     pipeline.set_params(clf = c)
#     scores = cross_validate(pipeline, X_train, Y_train)
#     print('---------------------------------')
#     print(str(c))
#     print('-----------------------------------')
#     for key, values in scores.items():
#             print(key,' mean ', values.mean())
#             print(key,' std ', values.std())

#parameter tuning
pipeline.set_params(clf=GradientBoostingClassifier())

grid={'clf__loss':['deviance','exponential'],
	'clf__max_features':[5,6],
	'clf__min_samples_split':np.logspace(-1.9,-1.5,10)
	}
#loss=’deviance’, learning_rate=0.1, n_estimators=100, subsample=1.0, criterion=’friedman_mse’, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_depth=3, min_impurity_decrease=0.0, min_impurity_split=None, init=None, random_state=None, max_features=None, verbose=0, max_leaf_nodes=None, warm_start=False, presort=’auto’, validation_fraction=0.1, n_iter_no_change=None, tol=0.0001
gr_boosting = GridSearchCV(pipeline, grid, cv=3)
gr_boosting.fit(X_train, Y_train) 
print(gr_boosting.best_params_,np.amax(gr_boosting.cv_results_["mean_test_score"]))
scores_df = pd.DataFrame(gr_boosting.cv_results_).sort_values(by='rank_test_score')
print(scores_df)
old = pd.read_csv('gradBoost.cv')
test = pd.merge(old,scores_df,how='outer',on=['param_clf__max_features','param_clf__min_samples_split','param_clf__loss'])
test.sort_values(by='rank_test_score')
test.to_csv('test.cv')
