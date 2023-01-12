# Analyzer bot

本botはマリオカート8デラックスのチーム活動をサポートする機能を備えたbotになります。

## 機能


本botの主な機能は以下の通りです。

- MK8DX 150cc Lounge における戦績確認
- プレイヤーの検索
- 交流戦の挙手
- 交流戦の戦績管理
- 交流戦の参加アンケート

MK8DX 150cc Loungeの戦績は[MK8DX 150cc Leaderboard](https://www.mk8dx-lounge.com/Leaderboard)より取得しています。

## 特徴


#### **複数アカウントの連携**

本botはラウンジサーバーに参加しているDiscordアカウントのIDを連携させることによって、ラウンジサーバーに加入していないアカウントでも戦績を参照できるようになっています。

#### **広範囲の検索**

プレイヤーの検索にはDiscord IDやNintendo Switchのフレンドコード、ラウンジ名などが使用できますが、これはbotにより自動で判別されるため、入力が簡単でありながら多くの要素で検索することが可能です。


#### **スラッシュコマンドとテキストコマンドの両対応**

ほとんどのコマンドがチャット欄にコマンドを打ち込む形式のテキストコマンドと、" / "から始まるスラッシュコマンドの両方に対応しているため、使いやすい形式でコマンドを実行できます。


#### **ロールとの連携**

Discordサーバー内のロール（役職）と連携した機能を実装しているため、サーバーごとにより自由な使い方が実現できます。



## 謝辞


本botの作成にあたり、以下のプログラムを参考にさせていただきました。

- [StatsBot-150cc-Lounge](https://github.com/fuyu-neko/StatsBot-150cc-Lounge)
- [MK8DX-Lounge-Bot](https://github.com/cyndaquilx/MK8DX-Lounge-Bot)


## 使用方法

 [招待リンク](https://discord.com/api/oauth2/authorize?client_id=1038322985146273853&permissions=8&scope=bot)から各自サーバーへ本botを招待してください。また、コマンドの確認はサーバー内にて`!help`と入力することで確認できます。

