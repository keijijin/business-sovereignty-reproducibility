# 実証手順

このcheckoutのREADMEとmethodology.md、business.jsonが正本です。Node.js 22.13以上とPython 3を用意し、checkout直下で実行します。

```bash
node scripts/build.mjs
node scripts/dev.mjs 4177 .local/new-demo.sqlite
python3 materials/python_server.py 4178 .local/new-python.sqlite
```

画面の実験人物「海」で起票、訂正、提出。v2で自己承認が403、「蓮」の承認が200であることを確かめます。下書きは起票者が取り下げられ、本文と履歴を保持します。提出後の訂正は409です。

仕様切替と全体export/importはatelierの承認者（海・蓮）だけに許可します。澪には403を返します。仕様切替は監査欄で操作者と日時と前後版を確認します。通常の一覧・個別操作は各人物のテナント内です。

学習回答を保存しても業務revisionは進みません。競合した業務操作は再読み込みしてから判断し直します。取下げは削除ではなく200件に数えます。上限に達したら管理人物でexportしてください。

```bash
python3 scripts/review-checks.py
node scripts/check-boundaries.mjs
node scripts/check-media.mjs
```

これらは合成データを新しいDBに作り、同じ評価を二実装へ実行し、両方向の移行と200件の大容量データを検査します。実行記録はcontent/evidence.jsonです。過去の公開確認、ローカル評価、未実施を区別します。既存の稼働DBを消す必要はありません。

公開環境はSites認証ごとにD1/R2を分けます。Pythonはローカルの交換先であり公開サイトの実装ではありません。動画をローカルで取り込むと.local/mediaに保存し、元のmediaを保持します。
