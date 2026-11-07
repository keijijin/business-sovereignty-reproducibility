# 業務主権開発の研究論文

著者：Keiji Jin／神 敬二。所属は提供されていないため記載しない。日英は同じ研究課題、実測値、制約、参考文献に対応した未査読の研究論文草稿であり、投稿・採録はしていない。

- `paper-en.pdf` / `paper-ja.pdf`：閲覧用。日本語フォントを埋め込む。
- `paper-en.docx` / `paper-ja.docx`：編集用Word原稿。
- `paper-en.md` / `paper-ja.md`：本文の編集正本。
- `references.bib`：引用キーを持つBibTeXデータ。
- `references.json`：17件の一次資料、確認箇所、版と参照日。2026年の3件はプレプリントとして扱う。
- `claim-evidence.json`：論文の主張と記録の対応。
- `validation.json`：入力ハッシュ、日英の参照・数値・版、出力PDFの検査記録。
- `build_documents.py`：MarkdownからDOCXを生成する再現用コード。

英語題は Business Sovereignty through Replaceable Implementations、日本語題は「業務主権を支える実装交換可能性」。副題でAI支援開発の探索的実証と位置づける。

主張は、実装交換の判定条件を定義し、合成的な業務システムの二実装で特定の条件を確認した、という範囲に限定する。44件は各実装のアサーション群であり、異種の全検査を合算した統計的成功率を示さない。移行6件は二つのfixtureに対する計6アサーションである。過去の反例は提供レビューの観察であり、新規に再実行した旧版比較実験ではない。

投稿先は指定されていないため、特定のACM・IEEE・情報処理学会テンプレートは仮定せず、1段組の汎用原稿とした。投稿前には投稿先の書式・匿名化・AI開示規定を適用し、著者が引用、著者責任、資金・利益相反、成果物の配布権限を確認する。公開再現パッケージは https://github.com/keijijin/business-sovereignty-reproducibility の固定タグ artifact-v1.0.0 を参照する。元の非公開履歴は含まない。

## 再生成

編集正本を変更後、文書用Python環境（python-docxを含む）で `python3 research/paper/build_documents.py` を実行する。本稿はCodexのbundled document runtimeで作成した。DOCXをPDFへ変換し全ページを検査した。PDFはDOCXの変換結果である。

日本語はHiragino Mincho ProN、英数字はTimes New Romanを指定する。別環境では、利用可能で適切なライセンスの日本語書体を指定する。今回の変換では、作業用fontconfigにシステムの日本語書体の読取り先と書込み可能なcacheを指定した。実行環境の既定設定で日本語が欠落することがあったため、PDFで字形と埋込みを確認した。書体本体はリポジトリへ同梱しない。

論文作成では業務コードと保存済み評価を変更しておらず、今回の文章化を評価の独立再現とは呼ばない。

第1.1版は公開再現用リポジトリと固定タグを文献[17]として追加し、入手可能性・妥当性・clone手順を更新した。業務コードと元の実測記録は変更していない。
