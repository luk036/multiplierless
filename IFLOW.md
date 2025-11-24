# iFlow 项目上下文 - multiplierless

## 项目概述

**multiplierless** 是一个用 Python 实现的专门用于设计无乘法器 FIR（有限脉冲响应）滤波器的项目。该项目的目标是在信号处理应用中创建低通滤波器，同时避免使用乘法操作，这在某些硬件实现中是有益的，因为它可以减少硬件复杂性和功耗。

该项目使用了椭球法（ellipsoid method）进行优化，并依赖几个专门的库：
- `luk036/csdigit`：用于规范符号数字（CSD）表示
- `luk036/bairstow`：用于多项式根求解
- `luk036/ellalgo`：用于椭球法优化

## 主要特性

- 每次迭代最多进行一次平方根运算
- 支持矩阵不等式和网络问题的 oracle
- 支持并行切面（Parallel-Cuts）
- 纯 Python 代码实现

## 核心文件和功能

### 1. `spectral_fact.py`
实现谱因式分解算法，这是信号处理中的关键技术：
- `spectral_fact(r)`：计算满足给定自相关性的最小相位脉冲响应
- `inverse_spectral_fact(h)`：从给定的脉冲响应重建自相关系数

### 2. `lowpass_oracle_q.py`
实现 `LowpassOracleQ` 类，用于处理带 CSD 约束的低通滤波器设计问题：
- 使用谱因式分解和 CSD 表示进行滤波器优化
- 提供评估和优化滤波器设计的功能

### 3. `skeleton.py`
包含项目的基本框架，包括一个斐波那契数列示例函数和命令行接口设置

## 依赖关系

- Python >= 3.9
- numpy >= 1.12.0
- decorator >= 4.1.0
- importlib-metadata (用于 Python < 3.9)

## 构建和运行

该项目使用 PyScaffold 4.0.2 设置，可以通过以下方式安装：

```bash
pip install -e .
```

或者通过标准安装方式：

```bash
pip install .
```

## 测试

项目使用 pytest 进行测试，测试文件位于 `tests/` 目录下。可以通过以下命令运行测试：

```bash
pytest tests/
```

## 开发约定

- 代码遵循 PEP 8 标准，最大行长度为 88（与 Black 兼容）
- 使用 Flake8 进行代码质量检查
- 使用 MyPy 进行类型检查（配置在 `mypy.ini` 中）
- 项目使用 setuptools-scm 管理版本

## 项目结构

```
src/
└── multiplierless/
    ├── __init__.py
    ├── csd.tpy
    ├── lowpass_oracle_q.py
    ├── lowpass_oracle.tpy
    ├── matrix2.tpy
    ├── rootfinding.tpy
    ├── skeleton.py
    ├── spectral_fact.py
    ├── vector2.tpy
    └── __pycache__/
```

## 用例

该项目主要用于数字信号处理领域的研究和开发，特别是需要避免乘法运算的硬件约束环境。它提供了设计优化的低通滤波器的工具，这些滤波器可以在资源受限的环境中高效实现。

## 相关项目

- [multiplierless-cpp](https://github.com/luk036/multiplierless-cpp) - C++ 实现的类似功能