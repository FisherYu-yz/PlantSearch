from pathlib import Path
import csv
import io
import json
import time

import numpy as np
import streamlit as st
import torch
from torch import nn
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image, ImageOps


@st.fragment
def show_download_button(csv_data):
    st.download_button(
        label="📥 下载本次检索结果（CSV）",
        data=csv_data,
        file_name="plant_search_results.csv",
        mime="text/csv",
    )


BASE_DIR = Path(__file__).resolve().parent
GALLERY_DIR = BASE_DIR / "data" / "gallery"

st.set_page_config(
    page_title="校园植物检索",
    page_icon="🌿",
    layout="wide",
)

PLANTS_FILE = BASE_DIR / "data" / "plants.json"
try:
    with PLANTS_FILE.open("r", encoding="utf-8-sig") as file:
        PLANTS = json.load(file)

    required_fields = {
        "name",
        "scientific_name",
        "features",
        "description",
        "campus_location",
    }
    if not isinstance(PLANTS, dict) or not PLANTS:
        raise ValueError("植物资料必须是非空字典。")

    for plant_id, info in PLANTS.items():
        if not isinstance(info, dict):
            raise ValueError(f"{plant_id} 的资料格式不正确。")

        missing = required_fields - info.keys()
        if missing:
            raise ValueError(
                f"{plant_id} 缺少字段：{', '.join(sorted(missing))}"
            )
        if not all(
            isinstance(info[field], str)
            for field in required_fields
        ):
            raise ValueError(f"{plant_id} 的资料字段必须填写为文字。")
except (OSError, ValueError) as error:
    st.error(f"植物资料读取失败：{error}")
    st.stop()


def read_image(path):
    """读取图片，纠正手机拍摄方向并统一为 RGB。"""
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def normalize(vector):
    """单位化特征，便于使用点积计算余弦相似度。"""
    vector = np.asarray(vector, dtype=np.float32)
    return vector / max(float(np.linalg.norm(vector)), 1e-12)


@st.cache_resource
def load_model():
    """模型只加载一次，使用 CPU 运行。"""
    weights = ResNet18_Weights.DEFAULT
    model = resnet18(weights=weights)
    model.fc = nn.Identity()
    model.eval()
    return model, weights.transforms()


def extract_feature(image, method):
    """对图库和查询图片使用相同的特征提取过程。"""
    if method == "RGB 颜色直方图":
        pixels = np.asarray(image.resize((256, 256)))
        histograms = [
            np.histogram(
                pixels[:, :, channel],
                bins=32,
                range=(0, 256),
            )[0]
            for channel in range(3)
        ]
        return normalize(np.concatenate(histograms))

    model, transform = load_model()
    tensor = transform(image).unsqueeze(0)

    with torch.inference_mode():
        vector = model(tensor).squeeze(0).cpu().numpy()

    return normalize(vector)


def gallery_signature():
    """记录文件变化；增删或修改图库后自动刷新特征。"""
    files = []

    for plant_id in PLANTS:
        folder = GALLERY_DIR / plant_id
        if not folder.exists():
            continue

        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix.lower() in {
                ".jpg", ".jpeg", ".png"
            }:
                info = path.stat()
                files.append(
                    (str(path), plant_id, info.st_mtime_ns, info.st_size)
                )

    return tuple(files)


@st.cache_data(show_spinner=False)
def build_gallery(signature, method):
    """计算并缓存图库特征，查询时不重复计算。"""
    records = []
    features = []
    skipped = []

    for path, plant_id, modified_time, file_size in signature:
        try:
            image = read_image(path)
        except (OSError, ValueError):
            skipped.append(Path(path).name)
            continue

        # 模型或计算错误应正常报告，不当成坏图片忽略。
        feature = extract_feature(image, method)
        features.append(feature)
        records.append({"path": path, "plant_id": plant_id})

    if not features:
        return records, np.empty((0, 0), dtype=np.float32), skipped

    return records, np.stack(features), skipped


with st.sidebar:
    st.header("检索设置")
    method = st.selectbox(
        "检索方法",
        ["ResNet18 深度特征", "RGB 颜色直方图"],
    )
    top_k = st.slider("返回图片数量", 1, 10, 5)

    signature = gallery_signature()
    st.write(f"图库图片数量：{len(signature)}")

    if st.button("清除图库特征缓存"):
        build_gallery.clear()
        st.success("缓存已清除，下次检索时重新计算。")

    st.caption("首次使用深度特征需要下载预训练模型权重。")

st.title("🌿 校园植物图鉴检索助手")
st.write("上传植物照片，查找图库中的相似图片。")
plant_names = "、".join(info["name"] for info in PLANTS.values())
st.caption(
    f"已配置植物：{plant_names}。"
    "结果是图库内的相似候选，相似度不代表识别正确的概率。"
)

uploaded = st.file_uploader(
    "上传植物照片",
    type=["jpg", "jpeg", "png"],
)

if uploaded is None:
    st.info("请上传一张查询照片，建议使用 data/queries 中的独立测试图片。")
    st.stop()

try:
    query_image = read_image(uploaded)
except (OSError, ValueError):
    st.error("无法读取这张图片，请更换有效图片。")
    st.stop()

search_image = query_image
enable_crop = st.checkbox("裁剪植物主体后检索", value=False)

if enable_crop:
    st.write("调整范围，让裁剪区域尽量包含植物主体。")
    x_range = st.slider(
        "左右范围（百分比）",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=1,
    )
    y_range = st.slider(
        "上下范围（百分比，0 为顶部）",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=1,
    )

    width, height = query_image.size
    x1 = round(width * x_range[0] / 100)
    x2 = round(width * x_range[1] / 100)
    y1 = round(height * y_range[0] / 100)
    y2 = round(height * y_range[1] / 100)

    if x2 <= x1 or y2 <= y1:
        st.warning("裁剪区域不能为空，请拉开范围滑块。")
        st.stop()

    search_image = query_image.crop((x1, y1, x2, y2))

left, right = st.columns([1, 1])

with left:
    st.subheader("查询图片")
    st.image(
        search_image,
        caption="实际用于检索的图片",
        use_container_width=True,
    )

with right:
    st.subheader("图片信息")
    st.write(f"文件名：{uploaded.name}")
    st.write(f"尺寸：{query_image.width} × {query_image.height}")
    st.write(f"检索方法：{method}")
    st.write(f"返回数量：{top_k}")
    search_clicked = st.button("开始检索", type="primary")

if search_clicked:
    if not signature:
        st.error(
            "图库为空。请检查 data/gallery/plant001、plant002、"
            "plant003 中是否有 JPG 或 PNG 图片。"
        )
        st.stop()

    try:
        with st.spinner("正在准备图库并检索，首次运行需要稍等……"):
            records, matrix, skipped = build_gallery(signature, method)

            if not records:
                st.error("图库图片均无法读取，请检查图片文件。")
                st.stop()

            # 单独统计查询时间，不包括图库初始化。
            start = time.perf_counter()
            query_feature = extract_feature(search_image, method)
            scores = matrix @ query_feature
            order = np.argsort(-scores, kind="stable")[
                :min(top_k, len(records))
            ]
            elapsed = time.perf_counter() - start

    except Exception as error:
        st.error(f"检索失败：{error}")
        st.info(
            "如果提示模型下载失败，可先切换“RGB 颜色直方图”"
            "验证完整检索流程，再处理模型下载。"
        )
        st.stop()

    if skipped:
        st.warning("以下图片无法读取，已跳过：" + "、".join(skipped))

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([
        "查询图片",
        "检索方法",
        "是否启用裁剪",
        "查询耗时（秒）",
        "排名",
        "植物编号",
        "植物名称",
        "学名",
        "余弦相似度",
        "图库图片",
    ])
    for rank, index in enumerate(order, start=1):
        record = records[int(index)]
        plant = PLANTS[record["plant_id"]]
        writer.writerow([
            uploaded.name,
            method,
            "是" if enable_crop else "否",
            f"{elapsed:.4f}",
            rank,
            record["plant_id"],
            plant["name"],
            plant["scientific_name"],
            f"{float(scores[index]):.6f}",
            f"{record['plant_id']}/{Path(record['path']).name}",
        ])
    csv_data = csv_buffer.getvalue().encode("utf-8-sig")
    show_download_button(csv_data)

    st.subheader("相似图片")
    st.caption(
        f"返回 {len(order)} 张图片；查询耗时 {elapsed:.3f} 秒"
        "（不含图库初始化）。同一种植物可能出现多张图片。"
    )

    for row_start in range(0, len(order), 3):
        columns = st.columns(3)
        for column_index, index in enumerate(
            order[row_start:row_start + 3]
        ):
            rank = row_start + column_index + 1
            record = records[int(index)]
            plant = PLANTS[record["plant_id"]]
            original = read_image(record["path"])
            preview = ImageOps.pad(
                original,
                (600, 400),
                method=Image.Resampling.LANCZOS,
                color=(240, 242, 240),
            )
            with columns[column_index]:
                with st.container(border=True):
                    st.image(
                        preview,
                        use_container_width=True,
                    )
                    st.markdown(
                        f"**第 {rank} 名 · {plant['name']}**"
                    )
                    st.caption(plant["scientific_name"])
                    st.write(
                        f"余弦相似度：{float(scores[index]):.3f}"
                    )
                    st.caption(Path(record["path"]).name)
                    with st.expander("查看植物图鉴"):
                        st.markdown(
                            f"**中文名：** {plant['name']}"
                        )
                        st.markdown(
                            f"**学名：** "
                            f"*{plant['scientific_name']}*"
                        )
                        st.markdown("**观察要点**")
                        st.write(plant["features"])
                        st.markdown("**图库说明**")
                        st.write(plant["description"])
                        st.markdown(
                            f"**校园位置：** "
                            f"{plant['campus_location']}"
                        )
                        st.caption(
                            "检索结果供参考，请结合实物特征确认。"
                        )