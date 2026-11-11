# 校园植物图鉴检索助手

数字图像处理课程双人项目原型。上传植物照片，使用 RGB 颜色直方图或预训练 ResNet18 特征检索本地图库，查看候选图片和植物资料，并导出 CSV。

## 当前功能

- JPG、JPEG、PNG 上传及预览
- RGB 直方图 / ResNet18 特征检索与余弦相似度排序
- 手动调整百分比范围，裁剪查询主体
- 植物图鉴展开、统一尺寸的结果卡片
- UTF-8 BOM 编码 CSV 下载，方便 Excel 查看
- 图库特征缓存；图片变化后自动重新计算

当前数据：蓝花楹、白玉兰、荷花，各 5 张图库图片、2 张查询图片。结果是图片排名，同一植物可出现多次。相似度不是识别正确概率；图库外植物也会返回相似候选，系统尚不支持可靠的未知类别拒识。

## 环境

原开发环境：Windows、Python 3.9.23、PyTorch 2.5.0、torchvision 0.20.0、Streamlit 1.40.2，CPU 运行。新环境尚需独立安装验证。使用 Python 3.9 或 3.11 的独立环境，不要用 Python 3.14 安装此组固定版本。

## 下载项目

点击 GitHub 的 Code → Download ZIP 并解压，或运行：

```powershell
git clone https://github.com/FisherYu-yz/PlantSearch.git
cd PlantSearch
```

以下命令均在解压/克隆后的项目根目录运行。先用 `python --version` 确认终端使用的 Python。

## 安装并启动

### 方式一：新建虚拟环境

确保当前 Python 是上述建议版本，再运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

无需激活虚拟环境，也无需修改 PowerShell 执行策略。

### 方式二：使用现有 Conda 环境

在能使用 Conda 的终端中激活自己的环境：

```powershell
conda activate 你的环境名
python --version
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

已有工作的 PyTorch 环境应先检查版本，安装前注意固定依赖可能调整现有包，建议使用独立环境。

### Windows 启动脚本

`start.bat` 优先使用项目内的 `.venv`，否则使用终端 PATH 中的 `python`。使用 Conda 时可在已激活环境的终端执行 `.\start.bat`。

原 `启动网页.bat` 写死了开发者电脑的 Python 路径，仅适用于该电脑；其他人请用上述命令或 `start.bat`。

浏览器打开终端显示的 Local URL（通常为 http://localhost:8501）。保持终端开启，Ctrl+C 停止。首次出现 Email 提示可直接回车。

## 模型权重

ResNet18 首次运行需要联网下载约 45 MB 预训练权重，之后复用 PyTorch 本地缓存。课堂演示前应在演示电脑上完成一次深度检索，并重启程序验证。下载失败时先使用 RGB 方法检查其他功能。GitHub 上传代码不会自动部署网页，GitHub Pages 也不能直接运行此 Python 服务。

## 数据结构

| 路径 | 用途 |
|---|---|
| app.py | 网页、特征提取、排序及导出 |
| data/plants.json | 植物资料 |
| data/gallery/plant001 | 蓝花楹图库 |
| data/gallery/plant002 | 白玉兰图库 |
| data/gallery/plant003 | 荷花图库 |
| data/queries/plant001～003 | 独立查询图片 |
| requirements.txt | 应用直接依赖 |
| environment-full.txt | 原环境快照，不作为安装清单 |

`environment-full.txt` 含 Conda 构建机本地文件路径，其他电脑不能直接按该文件安装。

新增植物时，在 JSON 中加入唯一编号及与现有条目一致的字段，在 gallery 下建立相同编号目录并放入图片，在 queries 下另放独立查询图片。使用标准 JSON，不加注释或末尾逗号。

## 操作与测试

1. 上传 queries 中的照片，选择方法和返回数量，点击开始检索。
2. 查看结果，展开图鉴，下载 CSV。
3. 同一查询照片分别测试 RGB 与 ResNet18；裁剪实验记录左右、上下百分比范围。
4. 记录第一名是否为真实类别，以及 P@5 = 前五张中正确类别图片数 / 5。图库不足五张时按实际返回数量报告指标。
5. 展示至少一个失败或明显受限案例，不删除困难样本以改善统计。
6. 测试下载后页面是否保留结果、损坏图片是否有提示、程序重启后是否能运行。

当前 CSV 记录是否裁剪，但不记录裁剪坐标，需另行记录。6 张查询图片仅适合初步验证，正式评价需要更多独立照片；避免原图和其裁剪版分居图库与测试集。

## 常见问题

- app.py 不存在：进入项目目录，或提供 app.py 的完整路径。
- 找不到 streamlit/torch：使用安装依赖时同一个 Python 启动。
- 图库数量为零：检查 gallery 目录、编号与 JSON 一致，图片直接放在编号目录内。
- RGB 排名不理想：整图颜色统计受背景影响，作为对照方法如实记录。
- 调整参数后结果消失：当前只有点击开始检索时展示结果，调整后请重新点击。
- 同学打不开 localhost：localhost 指访问者自己的电脑。独立运行按安装步骤；同网访问可执行 `python -m streamlit run app.py --server.address 0.0.0.0`，同学打开终端 Network URL。仅在信任网络允许防火墙访问；校园网络可能隔离设备。

## 图片与资料来源

当前 JSON 中链接为 Wikimedia Commons 的植物分类页，不是逐图授权记录。应补充每张图片的详情页 URL、作者和许可，并核对植物介绍来源。网上图片不能标为校园实拍；校园位置未核实，当前保留“待实地调查”。本仓库未替第三方图片授予新许可。

## 展示准备

开发成员负责稳定运行、修复和技术流程说明；测试展示成员负责独立测试、结果统计、失败案例、PPT 和视频。按课程要求准备 7 分钟汇报及 3 分钟问答，最终压缩包包含 PPT 与 MP4，总大小控制在 100 MB 内。
