from flask import Flask, render_template, request
import pandas as pd
from numpy import argmin
from nltk import edit_distance
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def LD(s, t):
    if s == "":
        return len(t)
    if t == "":
        return len(s)
    if s[-1] == t[-1]:
        cost = 0
    else:
        cost = 1

    res = min([LD(s[:-1], t)+1,
               LD(s, t[:-1])+1,
               LD(s[:-1], t[:-1]) + cost])

    return res

app = Flask(__name__)


df = pd.read_csv('/home/laurencelj/epl/.data/epl2021_new.csv')

teams_dates = pd.DataFrame({"team":df["team_fixed"], "date":df["datetime"]}).drop_duplicates().reset_index(drop=True).sort_values(by=["team", "date"]).reset_index(drop=True)
teams_dates['fixture'] = [(x%38) + 1 for x in range(760)]
df_joined =  pd.merge(teams_dates, df,  how='left', left_on=['team','date'], right_on = ['team_fixed','datetime'])
df_joined = df_joined.sort_values(by=["team_fixed", "fixture"]).reset_index(drop=True)

df_joined["Player_lower"] = df_joined["Player"].apply(lambda x: str.lower(x).replace(" ",""))



player_names_upper = list(set(df_joined["Player"]))
player_names = [x.lower().replace(" ","") for x in player_names_upper]

@app.route('/')
def home():
    fig = plt.figure()
    fig.savefig("/home/laurencelj/epl/assets/plots/xA_graph.png", transparent=True )
    fig.savefig("/home/laurencelj/epl/assets/plots/xG_graph.png", transparent=True )
    return render_template('index.html', fixtures = "", text="", headline_stats="", suggestions="")

@app.route('/', methods = ["POST","GET"])
def my_form_post():
    text = request.form['text']
    text0 = text.lower().replace(" ","")
    if text0 in player_names:
        text1 = text0
        suggestions = [""]
    else:
        scores = []
        for i in range(len(player_names)):
            scores.append(edit_distance(player_names[i], text))
        text = player_names_upper[argmin(scores)]
        text1 = text.lower().replace(" ","")
        suggestions = [""]

    df1 = df_joined[df_joined['Player_lower'] == text1]
    df1 = df1.reset_index(drop=True)
    fixtures = df1["fixture"][0:6]


    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(df1['fixture'], df1['xG'], color="#1f77b4")
    ax.bar(df1['fixture'], df1['G'], alpha=0.3, color="#1f77b4")
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#232323')
    ax.spines['right'].set_color('#232323')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    fig.savefig("/home/laurencelj/epl/assets/plots/xG_graph.png", transparent=True , dpi=200)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(df1['fixture'], df1['xA'], color="#1f77b4")
    ax.bar(df1['fixture'], df1['A'], alpha=0.3, color="#1f77b4")
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#232323')
    ax.spines['right'].set_color('#232323')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    fig.savefig("/home/laurencelj/epl/assets/plots/xA_graph.png", transparent=True , dpi=200)




    df2 = df1[["Min", "Sh", "G", "KP", "A","xG","xA","team_Sh","team_G","team_KP","team_A","team_xG","team_xA",
          "opponent_Sh","opponent_G","opponent_KP","opponent_A","opponent_xG","opponent_xA"]]
    df2 = df2.sum()
    df3 = pd.DataFrame(index = [0], columns=[x for x in df2.index])
    df3.iloc[0,:] = [x for x in df2.values]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.pie([df3["Min"][0], (38*90) -df3["Min"][0]], colors=["#1f77b4", "#232323"], startangle=90,
       labels=[str(int(100*df3["Min"][0]/((38*90) )))+"% of minutes played",""],
      textprops={"color":"white"})
    my_circle=plt.Circle( (0,0), 0.7, color='#232323')
    p=plt.gcf()
    p.gca().add_artist(my_circle)
    fig.savefig("/home/laurencelj/epl/assets/plots/mins_pie.png", transparent=True , dpi=100)

    headline_stats = {
        "name":text,
        "club":df1["team_fixed"][0],
        "pos":df1["Pos"][0],
        "goals":int(df3["G"][0]),
        "assists":int(df3["A"][0]),
        "shots":int(df3["Sh"][0]),
        "key_passes":int(df3["KP"][0])
        }




    return render_template('index.html', fixtures = fixtures, text=text, headline_stats=headline_stats, suggestions=suggestions)


if __name__ == '__main__':
    app.run(debug=True)
