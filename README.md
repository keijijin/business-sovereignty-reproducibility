# Business Sovereignty Replication Artifact

Public replication package for **Business Sovereignty through Replaceable Implementations**, by Keiji Jin. Includes source, specifications, recorded checks, eight videos, and sanitized SQLite snapshots. The immutable code/data baseline is tag `artifact-v1.0.0`.

```bash
git clone --branch artifact-v1.0.0 --depth 1 https://github.com/keijijin/business-sovereignty-reproducibility.git
cd business-sovereignty-reproducibility
node scripts/build.mjs
node scripts/validate-artifact.mjs
python3 scripts/review-checks.py
```

Use Node.js >=22.13 and Python 3. The recorded environment used Node.js 26.5.1 and Python 3.14. This runner writes a fresh evaluation record; preserve `content/evidence.json` first if comparing with the historical run. Local reproduction requires no account, hosted credentials, or cloud services. The hosted demonstration remains owner-restricted.

[English and Japanese manuscripts](https://github.com/keijijin/business-sovereignty-reproducibility/tree/main/research/paper) are maintained on `main`; their later document updates are separate from the fixed code/data baseline.

## 業務主権アカデミー & 実証ラボ

業務の意図・仕様・評価を組織の資産として残し、実装を選び直すための方法論と実動PoC。8単元の教材、NotebookLM動画8本、設計変更申請のJavaScript版とPython版、SQLiteスナップショットをこのcheckoutに含みます。

正本は [方法論](materials/methodology.md)、[機械可読の業務契約](materials/business.json)、[受け入れ評価](materials/acceptance.py) です。以前の別ディレクトリ `spec-to-app/poc` は不要です。初期構想は [履歴資料](docs/initial-methodology-concept.md) として残しています。未実施の実験0〜6と現段階の範囲は方法論の9章を参照してください。

## ローカルで開く

Node.js 22.13以上（検査には26.5.1）、Python 3を使用。Node.js組込みSQLiteを使うためNode.js 20には対応しません。外部パッケージは不要です。このcheckoutで実行してください。

```bash
node scripts/build.mjs
node scripts/validate-artifact.mjs
node scripts/dev.mjs 4177 .local/demo.sqlite
```

[ローカル画面](http://127.0.0.1:4177)。127.0.0.1だけで待ち受け、開発用の固定workspaceを使用します。公開環境はSites認証IDごとにD1とR2を分離します。`npm run build` と `bash scripts/build.sh` も同じビルドを呼びます。

Python版は同じcheckoutから次を実行します。Web画面はJavaScript版です。Pythonは交換先のHTTP APIでありSites上では動きません。

```bash
python3 materials/python_server.py 4178 .local/python.sqlite
```

## 契約と評価

両実装は起動時に自分の `materials/business.json` を読みます。人物・部品・文字数・件数・容量上限はその値を使い、未対応の状態構成などは起動を拒否します。ローカルで別仕様を検証するときはJavaScriptの `BUSINESS_SPEC` またはPythonの `--spec` を指定できます。Workerはビルド時に同じJSONを取り込み、起動時に検査します。自然言語の規則の変更だけで処理ロジックが自動生成されるわけではありません。

交換契約はUnicodeコードポイント、実在するUTC ISO日時（ミリ秒3桁とZ）、真偽値を許さない整数revisionです。R06の通常操作はテナント内だけ。管理テナントatelierの承認者だけが全実験テナントのexport/importと仕様切替を行い、切替はpolicyHistoryに残します。これはSites認証IDによる利用者workspace分離とは別の境界です。

未使用の新しいDBでそれぞれを起動した場合、以下を実行できます。評価は合成データを書き込みます。

```bash
python3 materials/acceptance.py http://127.0.0.1:4177
python3 materials/acceptance.py http://127.0.0.1:4178
```

全体の再検査は、独自の空DBと一時ポートでサーバーを起動し、終了時に停止します。両実装の受け入れ評価、双方向移行、絵文字を最大長まで入れた200件の保存・読出し・移行、JSON定数の変更反映を検査します。

```bash
python3 scripts/review-checks.py
node scripts/check-boundaries.mjs
node scripts/check-media.mjs
```

`content/evidence.json` は保存した実行記録で、検査対象commitと入力ハッシュを表示します。過去の公開確認は当時の記録です。ローカルSQLiteでD1と同じSQLを検査しても、公開D1の全条件の実証とは呼びません。同一制作セッションの評価であり盲検ではありません。

## 操作と保存

「海」で起票・訂正・提出し、v2の自己承認拒否と「蓮」の承認を確かめます。「海」「蓮」は仕様版を切り替えられ、「澪」は他テナントの申請参照・全体export・仕様切替ができません。下書きは起票者が取り下げられ、履歴と件数を保持します。

上限は件数200・要求24MB・workspace16MB・申請200KB・申請監査20件・仕様監査2000件を同時に適用します。超過する保存は413、201件目は409です。訂正は提出と判断の監査2枠を確保します。取下げは削除ではなく、上限到達時のデータ回収はexportを使います。学習記録は別テーブル・別revisionです。ローカル動画の取込先は `.local/media` で、Git管理の `media` を上書きしません。

[復元手順とスナップショット](snapshots/README.md)、[実証手順書](materials/runbook.md)、[レビュー修正記録](docs/review-remediation.md) を参照してください。この再現用リポジトリは公開です。認証IDを置換した現行スナップショットを、新しいGit履歴で配布します。元の非公開リポジトリの過去履歴と私有原本は含めません。

## 限界

公開環境はWorker/JavaScriptとD1、ローカル交換先は標準ライブラリPython/SQLiteです。Quarkus、FastAPI、PostgreSQL、Podmanは初期構想であり、このcheckoutの実装ではありません。完全な無人再生成、提供元の異なるモデルへの交換、第三者の盲検再現、書込み開始後の逆移行は未実施です。動画は制作時点の概念解説で、APIの最新契約はJSONと方法論を正本とします。

Sitesのソース保存には動画のサイズ制限があるため、GitHubの完本とSitesの配信用ソースは別履歴で保持します。[公開ソースの保存範囲](docs/source-publication.md)を参照してください。
