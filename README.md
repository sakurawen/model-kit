# model-kit

FBX模型贴图提取工具 - 自动从FBX文件中提取所有贴图到指定目录

## 功能特性

- 🎯 自动扫描FBX文件中的所有纹理和贴图
- 📁 使用时间戳创建唯一的输出目录
- 🔍 支持多种贴图类型(漫反射、法线、高光等)
- 📋 详细的提取过程日志
- 💾 自动处理相对路径和绝对路径

## 前置要求

需要安装Autodesk FBX SDK Python绑定:

1. 下载FBX SDK: https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-3-1
2. 安装对应的Python版本
3. 将FBX Python绑定添加到系统路径

## 使用方法

### 激活虚拟环境

```bash
# 首先激活虚拟环境
source .venv/bin/activate
```

### 基本用法

```bash
# 使用默认示例文件
python main.py

# 指定FBX文件
python main.py path/to/your/model.fbx

# 指定自定义输出目录
python main.py path/to/your/model.fbx custom_output
```

### 输出结构

```
output/
└── 20231205_143025/    # 时间戳文件夹
    ├── texture1.png
    ├── texture2.jpg
    └── normal_map.png
```

## 示例输出

```
============================================================
FBX贴图提取工具
============================================================
正在加载FBX文件: model/example.fbx
FBX文件加载成功,正在扫描贴图...
找到 3 个纹理对象
  - 发现贴图: diffuse.png
  - 发现贴图: normal.png
  - 发现贴图: specular.png

共找到 3 个唯一贴图文件

正在复制贴图到: output/20231205_143025
  ✓ 已复制: diffuse.png
  ✓ 已复制: normal.png
  ✓ 已复制: specular.png

总结: 成功 3 个, 失败 0 个
输出目录: /path/to/output/20231205_143025

============================================================
提取完成!
============================================================
```

## 项目结构

```
model-kit/
├── main.py           # 主程序
├── model/            # 示例FBX文件目录
│   └── example.fbx
├── output/           # 输出目录(自动创建)
└── README.md
```

## 技术说明

- 使用Autodesk FBX SDK进行FBX文件解析
- 递归扫描场景节点和材质
- 支持FbxFileTexture类型的纹理
- 自动处理文件路径解析

## 注意事项

- 确保FBX SDK已正确安装
- 贴图文件需要与FBX文件在相同目录或使用正确的相对路径
- 每次运行会创建新的时间戳目录
