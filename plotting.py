from typing import Any

from io import BytesIO
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



async def create_plot(
    mmr_history:list,
    season = None,
)->BytesIO:
    if season == 4:
        ranks = [0, 4000, 5500, 7000, 8500, 10000, 11500, 13000, 14500]
        colors_between = [0]
    elif season == 5:
        ranks = [0, 2000, 4000, 6000, 8000, 10000, 11000, 13000, 14000]
        colors_between = [1000, 3000, 5000, 7000, 9000, 12000]
    elif season == 6 or season == 7:
        ranks = [0, 2000, 4000, 6000, 8000, 10000, 12000, 14000, 15000]
        colors_between = [1000, 3000, 5000, 7000, 9000, 11000, 13000]
    elif season == 8:
        ranks = [0, 2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 17000]
        colors_between = [1000, 3000, 5000, 7000, 9000, 11000, 13000, 15000]
        colors = ['#817876', '#E67E22', '#7D8396', '#F1C40F', '#3FABB8','#286CD3','#D51C5e' ,'#9CCBD6', '#0E0B0B', '#A3022C']
    else:
        ranks = [0, 2000, 4000, 6000, 8000, 10000, 11000, 13000, 14000]
        colors_between = [1000, 3000, 5000, 7000, 9000, 12000]

    if season != 8:
        colors = ['#817876', '#E67E22', '#7D8396', '#F1C40F', '#3FABB8','#286CD3', '#9CCBD6', '#0E0B0B', '#A3022C']

    xs = np.arange(len(mmr_history))
    plt.rcParams.update(plt.rcParamsDefault)
    plt.style.use('graph_style.mplstyle')
    lines = plt.plot(mmr_history)
    plt.setp(lines, 'color', 'snow', 'linewidth', 1.0)
    xmin, xmax, ymin, ymax = plt.axis()
    plt.ylabel("MMR")
    plt.grid(True, 'both', 'both', color='snow', linestyle=':')

    for i in range(len(ranks)):
        if ranks[i] > ymax:
            continue
        maxfill = ymax
        if i + 1 < len(ranks):
            if ranks[i] < ymin and ranks[i + 1] < ymin:
                continue
            if ranks[i + 1] < ymax:
                maxfill = ranks[i + 1]
        if ranks[i] < ymin:
            minfill = ymin
        else:
            minfill = ranks[i]
        plt.fill_between(xs, minfill, maxfill, color=colors[i])
        if season >= 5:
            divide =  [i for i in colors_between if minfill <= i <= maxfill]
            plt.hlines(divide, xmin, xmax, colors='snow', linestyle='solid', linewidth=1)
    plt.fill_between(xs, ymin, mmr_history, facecolor='#212121', alpha=0.4)
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.clf()
    plt.close()
    return buffer



def result_graph(results:list[dict[str,Any]])->BytesIO:
    df = pd.DataFrame(results)
    xs = np.arange(len(df))
    plt.rcParams.update(plt.rcParamsDefault)
    lines = plt.plot(
        np.sign(df['score']-df['enemyScore']).cumsum(),
        label='Wins - Loses'
    )
    plt.setp(lines, color='green', linewidth=1.0)
    _, _, ymin, ymax = plt.axis()
    plt.grid(True, 'both', 'both', color='gray', linestyle=':')
    plt.legend(
        bbox_to_anchor=(0,1),
        loc = 'upper left',
        borderaxespad = 0.5
    )
    plt.fill_between(xs, ymin, 0, facecolor='#87ceeb', alpha=0.3)
    plt.fill_between(xs, 0, ymax, facecolor='#ffa07a', alpha=0.3)
    plt.title('Win&Lose History')
    buffer = BytesIO()
    plt.savefig(buffer,format='png',bbox_inches='tight')
    buffer.seek(0)
    plt.clf()
    plt.close()
    return buffer