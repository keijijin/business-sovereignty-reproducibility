# DBスナップショットと動画の登録

この公開再現用GitHubリポジトリは、動画8本と、取得時点のDBスナップショット4点を含む。

- `../media/unit-01.mp4` 〜 `unit-08.mp4`：Notebookで生成した動画の実ファイル。通常のGitで管理する。Git LFSは不要。
- `local-javascript.sqlite`：JavaScript実装のローカルDB。SQLite backup APIで取得。
- `local-python.sqlite`：Python実装のローカルDB。
- `local-migration-python.sqlite`：JavaScriptからPythonへ移行したローカルDB。
- `hosted-d1.sqlite`：公開サイトD1の業務テーブル `DB/workspaces` を読み出し、workspace識別子を置換し、SQLiteへ格納した論理スナップショット。D1のプラットフォーム内部テーブルやR2のデータは含まない。
- 同名の `.sql`：各スナップショットをSQLとして復元できる形式。
- `hosted-d1.rows.json`：公開DBから取得した業務テーブルの全行と取得時点。
- `manifest.json`：動画・DB・SQL・公開DB取得データのサイズとSHA-256。

稼働中のDBや公開R2への自動同期ではない。データは取得時点の保存である。実験人物は合成データであり、現行のユーザーworkspace識別子は教材用sample-workspaceへ置換した。元データはGit管理外の私有保存先に保持する。この公開版は新しいGit履歴であり、元の非公開Git履歴を含まない。

## GitHubから再現する

リポジトリを通常の `git clone` で取得すれば、MP4もSQLiteも取得できる。Git LFSの導入や追加ダウンロードは不要。

サイトのcheckoutで、未使用のファイル名を指定する。

```bash
python3 scripts/restore-db.py snapshots/local-javascript.sqlite .local/restored-javascript.sqlite
node scripts/build.mjs
node scripts/dev.mjs 4177 .local/restored-javascript.sqlite
```

`http://127.0.0.1:4177` で、保存した業務と全8単元の動画を確認できる。

Python実装のDBは次のように復元する。

```bash
python3 scripts/restore-db.py snapshots/local-python.sqlite .local/restored-python.sqlite
python3 materials/python_server.py 4178 .local/restored-python.sqlite
```

公開D1の業務データをローカルJavaScript実装で確認する場合、認証に使うworkspace識別子が異なるため、単一workspaceをローカル開発IDへ対応づける。

```bash
python3 scripts/restore-db.py snapshots/hosted-d1.sqlite .local/restored-hosted.sqlite --workspace-owner local-developer
node scripts/dev.mjs 4180 .local/restored-hosted.sqlite
```

この対応づけは新しい復元先にだけ行う。元スナップショットと公開DBは変更しない。公開サイトへ復元する場合は、別途、対象Siteの認証IDと配置先を確認する。

`.sql` を使う場合は、空の新しいSQLite DBへ読み込む。既存の稼働DBには適用しない。スナップショットはすべて `PRAGMA integrity_check` が `ok` であることを確認した。

現行版の起動にはNode.js 22.13以上が必要。`python3 scripts/verify-snapshots.py` で17資産のハッシュとSQLite整合性・教材用IDを検査できる。古いスナップショットは起動時に新テーブルを追加するが、当時記録されていなかった仕様切替監査を遡って捏造しない。
