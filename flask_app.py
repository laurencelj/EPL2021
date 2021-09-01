from flask import Flask, render_template, request
import pandas as pd
from numpy import argmin, argmax
from nltk import edit_distance
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

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
df_joined["Surname"] = df_joined["Player"].apply(lambda x: x[x.find(" ")+1:].lower())

team_xgs = df_joined[["fixture","team_fixed", "opposition_fixed","team_xG"]].drop_duplicates().reset_index(drop=True)

team_xgs = pd.merge(team_xgs, team_xgs[["fixture","team_fixed","team_xG"]],  how='left',
         left_on=["fixture", "opposition_fixed"],
         right_on=["fixture", "team_fixed"], suffixes=["__team","__opp"])

avxgs = team_xgs[["team_fixed__team","team_xG__team"]].groupby("team_fixed__team").mean()
avxgs["team_fixed"] = avxgs.index
df_joined = pd.merge(df_joined, avxgs,  how='left', left_on=['opposition_fixed'], right_on = ['team_fixed']).drop(["team_fixed_y"], axis=1).rename(columns = {"team_xG__team":"opponent_av_xG"})


player_names_upper = list(set(df_joined["Player"]))
player_names = [x.lower().replace(" ","") for x in player_names_upper]
player_surnames = [x[x.find(" ")+1:].lower() for x in player_names_upper]

teams = list(teams_dates["team"].drop_duplicates())
teams_points = [61,55,41,39,67,44,59,28,59,66,69,86,74,45,23,43,62,26,65,45]
team_standings = pd.DataFrame({"team":teams,"points":teams_points}).sort_values("points", ascending=False).reset_index(drop=True)

@app.route('/')
def home():
    fig = plt.figure()
    fig.savefig("/home/laurencelj/epl/assets/plots/xA_graph.png", transparent=True,dpi=1 )
    fig.savefig("/home/laurencelj/epl/assets/plots/xG_graph.png", transparent=True,dpi=1  )
    fig.savefig("/home/laurencelj/epl/assets/plots/shot_conversion.png", transparent=True ,dpi=1 )
    fig.savefig("/home/laurencelj/epl/assets/plots/assist_conversion.png", transparent=True ,dpi=1 )
    fig.savefig("/home/laurencelj/epl/assets/plots/mins.png", transparent=True,dpi=1  )
    fig.savefig("/home/laurencelj/epl/assets/plots/changed_table.png", transparent=True,dpi=1  )
    fig.savefig("/home/laurencelj/epl/assets/plots/def_xg.png", transparent=True , dpi=1)

    return render_template('index.html',
    fixtures = "",
    text="",
    headline_stats="",
    headline_names="",
    suggestions="")


@app.route('/', methods = ["POST","GET"])
def my_form_post():
    df1 = pd.DataFrame()
    text = request.form['text']
    text0 = text.lower().replace(" ","")
    if text0 in player_names:
        text1 = text0
        indo =[x == text0 for x in player_names].index(True)
        text = player_names_upper[indo]
        suggestions = [""]
    elif text0 in player_surnames:
        indo =[x == text0 for x in player_surnames].index(True)
        text = player_names_upper[indo]
        text1 = player_names[indo]
        suggestions = [""]

    elif text0 == "":
        fig = plt.figure()
        fig.savefig("/home/laurencelj/epl/assets/plots/xA_graph.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/xG_graph.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/shot_conversion.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/assist_conversion.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/mins.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/changed_table.png", transparent=True,dpi=1  )
        fig.savefig("/home/laurencelj/epl/assets/plots/def_xg.png", transparent=True , dpi=1)

        return render_template('index.html', fixtures = "", text="", headline_stats="",  headline_names="",suggestions="")
    else:
        scores = []
        for i in range(len(player_names)):
            scores.append(edit_distance(player_names[i], text))
        scores2 = []
        for i in range(len(player_surnames)):
            scores2.append(edit_distance(player_surnames[i], text))
        if min(scores)<min(scores2):
            text = player_names_upper[argmin(scores)]
        else:
            text = player_names_upper[argmin(scores2)]
        text1 = text.lower().replace(" ","")
        suggestions = [""]

    df1 = df_joined[df_joined['Player_lower'] == text1]
    df1 = df1.reset_index(drop=True)
    df1["contrib"] = df1["A"] + df1["G"]
    defensive_impact_per_game = (df1["opponent_av_xG"] - df1["opponent_xG"]).mean()
    defensive_impact_season = (df1["opponent_av_xG"] - df1["opponent_xG"]).sum()


    def points_gen(scores_bal):
        if scores_bal >0:
            q = 3
        elif scores_bal == 0:
            q= 1
        else:
            q=0
        return q
    df1["score_bal"] = df1["team_G"] - df1["opponent_G"]
    df1["score_bal_wo_player"] =  df1["team_G"] - df1["contrib"] - df1["opponent_G"]
    df1["points"] = df1["score_bal"].apply(points_gen)
    df1["opponent_points"] = df1["score_bal"].apply(lambda x: points_gen(-x))
    df1["points_wo_player"] = df1["score_bal_wo_player"].apply(points_gen)
    df1["opponent_points_wo_player"] = df1["score_bal_wo_player"].apply(lambda x: points_gen(-x))
    points_contrib = sum(df1["points"]) - sum(df1["points_wo_player"])
    df1["opponent_point_changes_wo_player"] = df1["opponent_points_wo_player"] - df1["opponent_points"]

    # HOW TABLE WOULD HAVE LOOKED WITHOUT ASSISTS AND GOALS
    affected_table = pd.merge(team_standings, df1[["opposition_fixed", "opponent_point_changes_wo_player"]],
             how="left", left_on="team", right_on="opposition_fixed")[["team","points","opponent_point_changes_wo_player"]]#.groupby(["team","points"]).sum("opponent_point_changes_wo_player")
    affectedtab = affected_table.groupby(["team","points"]).sum("opponent_point_changes_wo_player")
    their_club_points = points_contrib
    their_club_name = df1["team_fixed_x"][0]
    affectedtab["team"] = [x for x,y in affectedtab.index]
    affectedtab["points"] = [y for x,y in affectedtab.index]
    affectedtab.loc[their_club_name,"opponent_point_changes_wo_player"] = -their_club_points

    new_standings = affectedtab.reset_index(drop=True)
    new_standings["new_points"] = new_standings["points"] + new_standings["opponent_point_changes_wo_player"]
    new_standings = new_standings.sort_values("points", ascending=False).reset_index(drop=True)
    new_standings["old_standing"] = [x+1 for x in new_standings.index]
    new_standings = new_standings.sort_values("new_points", ascending=False).reset_index(drop=True)
    new_standings["new_standing"] = [x+1 for x in new_standings.index]

    fig = plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111)
    for i in range(len(new_standings)):
        teamn = new_standings.iloc[i,:]["team"]
        olds = new_standings.iloc[i,:]["old_standing"]
        news = new_standings.iloc[i,:]["new_standing"]
        xs = [1,2]
        ys = [olds, news]
        if teamn != their_club_name:
            ax.plot(xs,ys, c="#BEBEBE")
            ax.annotate(teamn, xy=(0.95,olds), fontsize=20, ha="right", c="#BEBEBE", va="center")
            ax.annotate(news, xy=(2.05,news), fontsize=20, ha="left", c="#BEBEBE", va="center")
        else:
            ax.plot(xs,ys, c="#1f77b4")
            ax.annotate(teamn, xy=(0.95,olds), fontsize=20, ha="right", c="#1f77b4", va="center")
            ax.annotate(news, xy=(2.05,news), fontsize=20, ha="left", c="#1f77b4", va="center")
    plt.gca().invert_yaxis()
    plt.xlim(0,2.5)
    ax.spines['left'].set_color('#232323')
    ax.spines['bottom'].set_color('#232323')
    ax.spines['top'].set_color('#232323')
    ax.spines['right'].set_color('#232323')
    ax.xaxis.label.set_color('#232323')
    ax.yaxis.label.set_color('#232323')
    ax.tick_params(axis='x', colors='#232323')
    ax.tick_params(axis='y', colors='#232323')
    fig.savefig("/home/laurencelj/epl/assets/plots/changed_table.png", transparent=True , dpi=100)


    setto = list(set(df1["Pos"]))
    pos_list = []
    for x in setto:
        pos_list.append(list(df1["Pos"]).count(x))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(df1['fixture'], df1['xG'], color="#1f77b4")
    ax.bar(df1['fixture'], df1['G'], alpha=0.5, color="#1f77b4")
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#232323')
    ax.spines['right'].set_color('#232323')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    ax.set_yticks([0,1,2,3])
    fig.savefig("/home/laurencelj/epl/assets/plots/xG_graph.png", transparent=True , dpi=100)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(df1['fixture'], df1['xA'], color="#1f77b4")
    ax.bar(df1['fixture'], df1['A'], alpha=0.5, color="#1f77b4")
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#232323')
    ax.spines['right'].set_color('#232323')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.set_yticks([0,1,2,3])
    fig.savefig("/home/laurencelj/epl/assets/plots/xA_graph.png", transparent=True , dpi=100)

    df2 = df1[["Min", "Sh", "G", "KP", "A","xG","xA","team_Sh","team_G","team_KP","team_A","team_xG","team_xA",
          "opponent_Sh","opponent_G","opponent_KP","opponent_A","opponent_xG","opponent_xA"]]
    df2 = df2.sum()
    df3 = pd.DataFrame(index = [0], columns=[x for x in df2.index])
    df3.iloc[0,:] = [x for x in df2.values]

    # Mins pie
    fig = plt.figure()
    ax = fig.add_subplot(111)
    mins = int(df3["Min"][0])
    ax.pie([mins, (38*90)-mins], colors=["#1f77b4", "#333333"], startangle=90,
            textprops={"color":"white"})
    my_circle=plt.Circle( (0,0), 0.7, color='#232323')
    ax.annotate(str(mins), xy=(0,0),fontsize=30, ha="center", va="center", c="white")
    p=plt.gcf()
    p.gca().add_artist(my_circle)
    fig.savefig("/home/laurencelj/epl/assets/plots/mins.png", transparent=True , dpi=100)

    # shot conversion pie chart
    fig = plt.figure()
    ax = fig.add_subplot(111)
    if df3["Sh"][0] == 0:
        fig = plt.figure()
        fig.savefig("/home/laurencelj/epl/assets/plots/shot_conversion.png", transparent=True )
    else:
        shot_conversion = df3["G"][0]/df3["Sh"][0]
        ax.pie([shot_conversion, 1-shot_conversion], colors=["#1f77b4", "#333333"], startangle=90,
            textprops={"color":"white"})
        my_circle=plt.Circle( (0,0), 0.7, color='#232323')
        ax.annotate(str(int(100*shot_conversion))+"%", xy=(0,0),fontsize=30, ha="center", va="center", c="white")
        p=plt.gcf()
        p.gca().add_artist(my_circle)
        fig.savefig("/home/laurencelj/epl/assets/plots/shot_conversion.png", transparent=True , dpi=100)

    # assist conversion pie chart
    fig = plt.figure()
    ax = fig.add_subplot(111)
    if df3["KP"][0] == 0 and df3["A"][0] == 0:
        fig = plt.figure()
        fig.savefig("/home/laurencelj/epl/assets/plots/assist_conversion.png", transparent=True )
    else:
        assist_conversion = df3["A"][0]/(df3["KP"][0]+df3["A"][0])
        ax.pie([assist_conversion, 1-assist_conversion], colors=["#1f77b4", "#333333"], startangle=90,
            textprops={"color":"white"})
        my_circle=plt.Circle( (0,0), 0.7, color='#232323')
        ax.annotate(str(int(100*assist_conversion))+"%", xy=(0,0),fontsize=30, ha="center", va="center", c="white")
        p=plt.gcf()
        p.gca().add_artist(my_circle)
        fig.savefig("/home/laurencelj/epl/assets/plots/assist_conversion.png", transparent=True , dpi=100)

# defensive xg chart
    fig = plt.figure()
    ax = fig.add_subplot(111)
    if df3["Min"][0] == 0:
        fig = plt.figure()
        fig.savefig("/home/laurencelj/epl/assets/plots/def_xg.png", transparent=True )
    else:
        if defensive_impact_per_game >= 0:
            ax.pie([defensive_impact_per_game, 1-defensive_impact_per_game], counterclock=False,
            colors=["green", "#333333"], startangle=90,
                textprops={"color":"white"})
        else:
            ax.pie([abs(defensive_impact_per_game), 1-abs(defensive_impact_per_game)], colors=["red", "#333333"], startangle=90,
                textprops={"color":"white"})
        my_circle=plt.Circle( (0,0), 0.7, color='#232323')
        ax.annotate(str(round(defensive_impact_per_game,2)), xy=(0,0),fontsize=30, ha="center", va="center", c="white")
        p=plt.gcf()
        p.gca().add_artist(my_circle)
        fig.savefig("/home/laurencelj/epl/assets/plots/def_xg.png", transparent=True , dpi=100)

    headline_stats = {
        "name":text,
        "club":df1["team_fixed_x"][0],
        "pos":setto[argmax(pos_list)],
        "goals":int(df3["G"][0]),
        "mins":int(df3["Min"][0]),
        "assists":int(df3["A"][0]),
        "shots":int(df3["Sh"][0]),
        "key_passes":int(df3["KP"][0]),
        "points_contrib":points_contrib,
        "defensive_impact_per_game":defensive_impact_per_game,
        "defensive_impact_season":round(defensive_impact_season,1)
        }

    headline_names = {
        "club":"Club:  ",
        "pos":"Primary position:  ",
        "goals":"Goals scored:  ",
        "assists":"Goals assisted:  ",
        "points_contrib": "Points contributed:  ",
        "defensive_impact_season":"Defensive xG effect:  ",
        "minutes":"Minutes played:  "
        }

    return render_template('index.html',
    text=text,
    headline_stats=headline_stats,
    headline_names=headline_names,
    suggestions=suggestions)


if __name__ == '__main__':
    app.run(debug=True)
