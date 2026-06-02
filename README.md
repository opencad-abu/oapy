# oapy

Si2 OpenAccess 22.61 Python bindings via pybind11.

oapy 是 [aivi](https://github.com/opencad-abu/aivi) 的子项目，为 aivi 平台提供 OpenAccess 数据访问能力。本项目仅包含 Python 绑定层，不涉及 OA C++ 实现。

## 模块

| 模块 | 覆盖 | 大小 | 说明 |
|------|------|------|------|
| `_common` | oaCommon | 1.2M | 插件基础接口 |
| `_base` | oaBase | 11M | 基础类型、属性、名称空间 |
| `_dm` | oaDM | 3.4M | 数据管理（库、单元、视图） |
| `_cms` | oaCM | 2.5M | 变更管理系统 |
| `_tech` | oaTech | 5.4M | 工艺定义、层、约束 |
| `_design` | oaDesign | 20M | 电路设计（网络、实例、版图） |
| `_wafer` | oaWafer | 2.2M | 晶圆/光罩 |
| `liboapyRegistry` | 共享注册表 | 1.1M | 跨模块类型 downcast |

## 依赖

**运行时：**
- Python 3.12
- OpenAccess 22.61 共享库（`liboaBase.so`, `liboaDesign.so` 等）
- libstdc++ (GLIBCXX ≥ 3.4.18)

**编译时（仅从源码构建需要）：**
- GCC 9.3+ (C++17)
- CMake 3.20+
- pybind11 3.0+
- OpenAccess 22.61 头文件 + 库
- OA DM 插件（DMFileSys、DMTurbo 等）

## 安装

```bash
# 当前系统 (glibc 2.34+)
pip install dist/oapy-0.1b0-cp312-cp312-linux_x86_64.whl

# RHEL7/CentOS7 (glibc 2.17+)
pip install dist/oapy-0.1b0-cp312-cp312-glibc-2.17_x86_64.whl
```

## Labs

`labs/` 目录包含 60 个 Python 实验脚本，对应 OpenAccess 22.61 C++ Lab 教程的 Python 移植版，涵盖 OA API 的各个模块。

### Lab 章节

| 章节 | 主题 | Lab 数量 |
|------|------|---------|
| Ch2 | MDPARies 环境配置 | 1 |
| Ch3 | Sample 基础操作 | 1 |
| Ch4 | oaDump 调试工具 | 1 |
| Ch6 | 图形对象 (oaFig) | 2 |
| Ch8 | 名称空间 & DM 数据 | 2 |
| Ch9 | 库列表操作 | 1 |
| Ch10 | 单元视图 & 数据压缩 | 2 |
| Ch11 | Schematic 创建 | 3 |
| Ch12 | Module 层次结构 | 2 |
| Ch13 | Occurrence 遍历 | 5 |
| Ch14 | 插件扩展 & DM 插件 | 3 |
| Ch16 | 文本/评估/符号/Pin/Schematic/RQ | 11 |
| Ch17 | Observer 观察者模式 | 8 |
| Ch18 | Pcell 参数化单元 | 8 |
| Ch20 | Tech 工艺库 | 2 |
| Ch21 | Constraint 约束 | 1 |
| Ch22 | 设计参数 | 1 |
| Ch25 | Traits 特征 | 1 |
| 附加 | 综合实验 | 5 |

### 环境变量

运行 lab 前需要设置以下环境变量（`run_lab.sh` 已自动配置）：

```bash
# Python 库路径
export LD_LIBRARY_PATH="/path/to/python3.12/lib:${LD_LIBRARY_PATH}"

# oapy 绑定库
export LD_LIBRARY_PATH="/path/to/oapy/oapy/_oa:${LD_LIBRARY_PATH}"

# OpenAccess 库
export LD_LIBRARY_PATH="/path/to/oa/22.61/lib/linux_rhel70_gcc93x_64/opt:${LD_LIBRARY_PATH}"

# OA 插件搜索路径
export OA_PLUGIN_PATH="/path/to/oa/22.61/data/plugins:${OA_PLUGIN_PATH}"

# Python 模块路径
export PYTHONPATH="/path/to/oapy:${PYTHONPATH}"
```

如果使用 oacpp 自编译 OA 库（aivi 项目），还需要 `LD_PRELOAD` 预加载 oacpp 库以覆盖官方版本：

```bash
export LD_PRELOAD="/path/to/oacpp/lib/liboaBase.so:/path/to/oacpp/lib/liboaDM.so:..."
```

### 运行 Lab

```bash
cd labs

# 查看可用 lab
./run_lab.sh

# 运行指定 lab
./run_lab.sh lab11_1_inverter.py

# 示例输出
============================================================
oapy Lab 11-1: Inverter (反相器)
============================================================
✅ OA initialized
📚 Library: aiviLabLib created
...
```

## API 文档

https://opencad-abu.github.io/oapy-docs-zh/

## License

Private — 仅限内部使用
