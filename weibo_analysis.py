from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

csv_path = DATA_DIR / "raw_weibo.csv"

df = pd.read_csv(csv_path)

print("数据基本信息：")
print(df.info())

print("\n前 5 行数据：")
print(df.head())

print("\n缺失值统计：")
print(df.isnull().sum())

print("\n重复值数量：")
print(df.duplicated().sum())

def classify_source(source):
    source = str(source)

    if "微博视频号" in source:
        return "微博视频号"

    if "微博网页版" in source:
        return "微博网页版"

    if "超话" in source:
        return "超话/社区"

    if "iPhone" in source or "Android" in source or "vivo" in source or "荣耀" in source or "OPPO" in source or "Xiaomi" in source:
        return "手机端"

    if source == "" or source == "未知来源" or source == "nan":
        return "未知来源"

    return "其他"


# =========================
# 1. 数据清洗
# =========================

df = df.drop_duplicates()

df["username"] = df["username"].fillna("未知用户")
df["content"] = df["content"].fillna("")
df["source"] = df["source"].fillna("未知来源")
df["source_category"] = df["source"].apply(classify_source)

number_cols = ["repost_count", "comment_count", "like_count"]

for col in number_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# 内容太长，截断一下，方便图表显示
df["content_short"] = df["content"].astype(str).str.slice(0, 30) + "..."

# 自定义热度分数
df["hot_score"] = (
    df["like_count"] +
    df["comment_count"] * 2 +
    df["repost_count"] * 3
)


# =========================
# 2. 基础统计
# =========================

total_weibos = len(df)
total_likes = df["like_count"].sum()
total_comments = df["comment_count"].sum()
total_reposts = df["repost_count"].sum()

print("\n微博总数：", total_weibos)
print("总点赞数：", total_likes)
print("总评论数：", total_comments)
print("总转发数：", total_reposts)


# =========================
# 3. Plotly 图表
# =========================

figures = []


# 图 1：点赞 Top10
top_likes = df.sort_values("like_count", ascending=False).head(10)

fig1 = px.bar(
    top_likes,
    x="username",
    y="like_count",
    hover_data=["content_short", "comment_count", "repost_count"],
    title="点赞数 Top10 微博"
)

figures.append(fig1)


# 图 2：评论 Top10
top_comments = df.sort_values("comment_count", ascending=False).head(10)

fig2 = px.bar(
    top_comments,
    x="username",
    y="comment_count",
    hover_data=["content_short", "like_count", "repost_count"],
    title="评论数 Top10 微博"
)

figures.append(fig2)


# 图 3：转发 Top10
top_reposts = df.sort_values("repost_count", ascending=False).head(10)

fig3 = px.bar(
    top_reposts,
    x="username",
    y="repost_count",
    hover_data=["content_short", "like_count", "comment_count"],
    title="转发数 Top10 微博"
)

figures.append(fig3)


# 图 4：来源分布
source_counts = df["source_category"].value_counts().reset_index()
source_counts.columns = ["source_category", "count"]

fig4 = px.pie(
    source_counts,
    names="source_category",
    values="count",
    title="微博发布来源分类分布"
)

figures.append(fig4)


# 图 5：热度 Top10
top_hot = df.sort_values("hot_score", ascending=False).head(10)

fig5 = px.bar(
    top_hot,
    x="username",
    y="hot_score",
    hover_data=["content_short", "like_count", "comment_count", "repost_count"],
    title="综合热度 Top10 微博"
)

figures.append(fig5)


# 图 6：点赞、评论、转发关系散点图
top_hot_compare = df.sort_values("hot_score", ascending=False).head(10)

compare_df = top_hot_compare[[
    "username",
    "like_count",
    "comment_count",
    "repost_count"
]]

compare_df = compare_df.melt(
    id_vars="username",
    value_vars=["like_count", "comment_count", "repost_count"],
    var_name="interaction_type",
    value_name="count"
)

fig6 = px.bar(
    compare_df,
    x="username",
    y="count",
    color="interaction_type",
    barmode="group",
    title="综合热度 Top10 微博互动数据对比"
)

fig6.update_yaxes(type="log")

figures.append(fig6)

# =========================
# 4. 生成 HTML 报告
# =========================

html_parts = []

html_parts.append("""
<h1>微博“世界杯”关键词动态分析报告</h1>

<p>本报告基于微博搜索关键词“世界杯”爬取的数据，对微博内容的点赞数、评论数、转发数、发布来源和综合热度进行动态可视化分析。</p>

<h2>一、数据概况</h2>
<ul>
    <li>微博总数：{}</li>
    <li>总点赞数：{}</li>
    <li>总评论数：{}</li>
    <li>总转发数：{}</li>
</ul>

<h2>二、可视化分析</h2>
""".format(total_weibos, total_likes, total_comments, total_reposts))


html_parts.append("""
<style>
.chart-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
}

.chart-card {
    background-color: white;
    padding: 10px;
    border-radius: 10px;
}

@media (max-width: 1000px) {
    .chart-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<div class="chart-grid">
""")

for i, fig in enumerate(figures):
    fig.update_layout(
        height=420,
        margin=dict(l=40, r=20, t=60, b=70)
    )

    chart_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn" if i == 0 else False,
        default_width="100%",
        default_height="420px",
        config={
            "responsive": True,
            "displaylogo": False
        }
    )

    html_parts.append(f"""
    <div class="chart-card">
        {chart_html}
    </div>
    """)

html_parts.append("""
</div>
""")

html_parts.append("""
<h2>三、分析结论</h2>

<p>从数据结果可以看出，不同微博之间的互动数据差异较大。点赞数较高的微博通常具有更强的传播效果，而评论数较高的微博说明用户讨论度更高。通过自定义综合热度分数，可以更直观地筛选出整体传播效果较强的微博内容。</p>

<p>本项目完成了从微博数据爬取、CSV 数据保存、Pandas 数据清洗，到 Plotly 动态可视化分析的完整流程。</p>
""")


output_path = OUTPUT_DIR / "weibo_dynamic_analysis.html"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(html_parts))

print(f"\n动态分析报告已生成：{output_path}")