"""
HTMLデータビューアを生成（データ埋め込み）
"""
import json
import os

DATA_DIR = "/Users/yuki/workspace/qwen-jp/data"
OUTPUT_HTML = f"{DATA_DIR}/data_viewer.html"

TARGET_FILES = [
    "logic_math.jsonl",
    "reasoning.jsonl",
    "tool_calling.jsonl",
    "japan_knowledge.jsonl",
    "japanese_cultural_logic.jsonl",
    "japanese_expressions.jsonl",
    "identity_creator.jsonl",
    "current_events.jsonl",
    "witty_qa.jsonl",
    "witty_companion.jsonl",
    "japanese_commonsense.jsonl",
    "bias_neutralization.jsonl",
    "philosophy_mentor.jsonl",
    "safety_deflection.jsonl",
    "investment_career.jsonl",
    "offline_mode.jsonl",
    "conversation_hooks.jsonl",
    "reasoning_40.jsonl",
    "top100_questions.jsonl",
    "logic_to_emotion.jsonl",
    "hooking_greetings.jsonl",
    "ai_comedy.jsonl",
    "current_trends_2026.jsonl",
    "japan_news_2024_2025.jsonl",
    "number_sense.jsonl",
    "textbook_knowledge.jsonl",
]

def load_all_data():
    all_data = []
    for filename in TARGET_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        item = json.loads(line)
                        # メタデータがなければ追加
                        if "metadata" not in item:
                            item["metadata"] = {}
                        if "source" not in item["metadata"]:
                            item["metadata"]["source"] = filename.replace(".jsonl", "")
                        if "category" not in item["metadata"]:
                            item["metadata"]["category"] = filename.replace(".jsonl", "")
                        all_data.append(item)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    return all_data

def main():
    print("データを読み込み中...")
    all_data = load_all_data()
    print(f"読み込み完了: {len(all_data)}件")

    # 重複削除
    seen = set()
    unique_data = []
    for item in all_data:
        user_msg = ""
        for msg in item.get("messages", []):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")[:200]
                break
        if user_msg and user_msg not in seen:
            seen.add(user_msg)
            unique_data.append(item)

    print(f"重複削除後: {len(unique_data)}件")

    # JSONをエスケープ
    json_str = json.dumps(unique_data, ensure_ascii=False)

    html_template = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ElioChat 学習データビューア</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Hiragino Sans', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .stat-number { font-size: 2.2em; font-weight: bold; color: #00d2ff; }
        .stat-label { color: #aaa; margin-top: 5px; font-size: 14px; }
        .filters {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 12px;
            margin: 20px 0;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filters select, .filters input {
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid #444;
            background: #2a2a4a;
            color: #fff;
            font-size: 14px;
        }
        .filters input { flex: 1; min-width: 200px; }
        .data-list { display: flex; flex-direction: column; gap: 15px; }
        .data-item {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #3a7bd5;
        }
        .data-item.logic { border-color: #ff6b6b; }
        .data-item.japan { border-color: #4ecdc4; }
        .data-item.tool { border-color: #ffe66d; }
        .data-item.witty { border-color: #ff9ff3; }
        .data-item.safety { border-color: #54a0ff; }
        .data-item.investment { border-color: #2ecc71; }
        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 10px;
            background: rgba(0,210,255,0.2);
            color: #00d2ff;
        }
        .message { margin: 10px 0; padding: 15px; border-radius: 8px; }
        .message.system { background: rgba(255,255,255,0.03); color: #666; font-size: 11px; max-height: 60px; overflow: hidden; }
        .message.user { background: rgba(58,123,213,0.3); }
        .message.assistant { background: rgba(0,210,255,0.1); }
        .role { font-weight: bold; margin-bottom: 8px; color: #00d2ff; font-size: 13px; }
        .content { white-space: pre-wrap; line-height: 1.7; font-size: 14px; }
        .think-tag { color: #888; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; display: block; margin: 10px 0; font-style: italic; }
        .tool-call { background: rgba(255,230,109,0.2); padding: 10px; border-radius: 8px; margin: 10px 0; font-family: monospace; }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        .pagination button {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: #3a7bd5;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }
        .pagination button:hover { background: #2a6bc5; }
        .pagination button:disabled { background: #444; cursor: not-allowed; }
        .pagination span { padding: 10px; color: #aaa; }
        .source-badge {
            font-size: 11px;
            color: #666;
            margin-left: 10px;
        }
        @media (max-width: 600px) {
            .filters { flex-direction: column; }
            .filters select, .filters input { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 ElioChat 学習データビューア</h1>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-count">-</div>
                <div class="stat-label">総データ数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="unique-count">-</div>
                <div class="stat-label">ユニーク数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="source-count">-</div>
                <div class="stat-label">ソース数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="filtered-count">-</div>
                <div class="stat-label">表示中</div>
            </div>
        </div>
        <div class="filters">
            <select id="source-filter"><option value="">すべてのソース</option></select>
            <input type="text" id="search" placeholder="🔍 キーワード検索...">
        </div>
        <div class="data-list" id="data-list"></div>
        <div class="pagination" id="pagination"></div>
    </div>
    <script>
        const allData = ''' + json_str + ''';
        let filteredData = allData;
        let currentPage = 1;
        const perPage = 15;

        function init() {
            document.getElementById('total-count').textContent = allData.length;
            document.getElementById('unique-count').textContent = allData.length;

            const sources = new Set();
            allData.forEach(item => sources.add(item.metadata?.source || 'unknown'));

            document.getElementById('source-count').textContent = sources.size;

            const srcSelect = document.getElementById('source-filter');
            [...sources].sort().forEach(src => {
                const opt = document.createElement('option');
                opt.value = src;
                opt.textContent = src + ' (' + allData.filter(d => d.metadata?.source === src).length + ')';
                srcSelect.appendChild(opt);
            });

            document.getElementById('source-filter').addEventListener('change', applyFilters);
            document.getElementById('search').addEventListener('input', applyFilters);
            applyFilters();
        }

        function applyFilters() {
            const src = document.getElementById('source-filter').value;
            const search = document.getElementById('search').value.toLowerCase();

            filteredData = allData.filter(item => {
                const itemSrc = item.metadata?.source || '';
                const content = JSON.stringify(item.messages || []).toLowerCase();
                if (src && itemSrc !== src) return false;
                if (search && !content.includes(search)) return false;
                return true;
            });

            currentPage = 1;
            render();
        }

        function render() {
            document.getElementById('filtered-count').textContent = filteredData.length;

            const start = (currentPage - 1) * perPage;
            const end = start + perPage;
            const pageData = filteredData.slice(start, end);

            const list = document.getElementById('data-list');
            list.innerHTML = pageData.map((item, idx) => {
                const src = item.metadata?.source || 'unknown';
                const cat = item.metadata?.category || src;
                const catClass = cat.includes('logic') || cat.includes('math') ? 'logic' :
                               cat.includes('japan') ? 'japan' :
                               cat.includes('tool') ? 'tool' :
                               cat.includes('witty') || cat.includes('humor') ? 'witty' :
                               cat.includes('safety') || cat.includes('bias') ? 'safety' :
                               cat.includes('invest') || cat.includes('career') ? 'investment' : '';

                const messages = (item.messages || []).map(msg => {
                    let content = escapeHtml(msg.content || '');
                    content = content.replace(/&lt;think&gt;([\\s\\S]*?)&lt;\\/think&gt;/g,
                        '<span class="think-tag">💭 $1</span>');
                    content = content.replace(/&lt;tool_call&gt;([\\s\\S]*?)&lt;\\/tool_call&gt;/g,
                        '<div class="tool-call">🔧 $1</div>');

                    const icon = msg.role === 'system' ? '📋' : msg.role === 'user' ? '👤' : '🤖';
                    return '<div class="message ' + msg.role + '">' +
                        '<div class="role">' + icon + ' ' + msg.role + '</div>' +
                        '<div class="content">' + content + '</div></div>';
                }).join('');

                return '<div class="data-item ' + catClass + '">' +
                    '<span class="category-badge">' + cat + '</span>' +
                    '<span class="source-badge">' + src + '</span>' +
                    messages + '</div>';
            }).join('');

            const totalPages = Math.ceil(filteredData.length / perPage);
            const pag = document.getElementById('pagination');
            pag.innerHTML = '<button ' + (currentPage === 1 ? 'disabled' : '') + ' onclick="goPage(' + (currentPage - 1) + ')">← 前</button>' +
                '<span>' + currentPage + ' / ' + totalPages + '</span>' +
                '<button ' + (currentPage >= totalPages ? 'disabled' : '') + ' onclick="goPage(' + (currentPage + 1) + ')">次 →</button>';
        }

        function goPage(p) { currentPage = p; render(); window.scrollTo(0, 0); }
        function escapeHtml(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
        init();
    </script>
</body>
</html>'''

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"HTMLビューア生成完了: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
