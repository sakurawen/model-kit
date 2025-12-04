import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

try:
    from fbx import *
except ImportError:
    print("错误: 无法导入FBX SDK Python绑定")
    print("请确保FBX SDK已正确安装并且Python绑定在系统路径中")
    print("\n安装方法:")
    print("1. 下载 FBX Python SDK: https://aps.autodesk.com/developer/overview/fbx-sdk")
    print("2. 或使用 pip 安装: pip install fbx")
    sys.exit(1)


class FBXTextureExtractor:
    """FBX模型贴图提取器"""
    
    # 要排除的贴图类型后缀（不区分大小写）
    EXCLUDE_SUFFIXES = [
        '_metallic',
        '_normal',
        '_roughness',
        '_specular',
        '_bump',
        '_height',
        '_ao',
        '_ambient',
        '_occlusion'
    ]
    
    def __init__(self, fbx_file_path, output_base_dir="output"):
        self.fbx_file_path = fbx_file_path
        self.output_base_dir = output_base_dir
        self.textures = set()  # 使用set避免重复
        # 创建基于时间戳的输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(output_base_dir, timestamp)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def extract_textures(self):
        """提取FBX文件中的所有贴图"""
        print(f"正在加载FBX文件: {self.fbx_file_path}")
        
        # 初始化FBX SDK管理器
        manager = FbxManager.Create()
        if not manager:
            print("错误: 无法创建FBX管理器")
            return False
        
        # 创建IO设置对象
        ios = FbxIOSettings.Create(manager, IOSROOT)
        manager.SetIOSettings(ios)
        
        # 创建导入器
        importer = FbxImporter.Create(manager, "")
        
        # 初始化导入器
        if not importer.Initialize(self.fbx_file_path, -1, manager.GetIOSettings()):
            print(f"错误: 无法初始化导入器")
            print(f"错误信息: {importer.GetStatus().GetErrorString()}")
            importer.Destroy()
            manager.Destroy()
            return False
        
        # 创建场景
        scene = FbxScene.Create(manager, "myScene")
        
        # 导入场景
        importer.Import(scene)
        importer.Destroy()
        
        print("FBX文件加载成功,正在扫描贴图...")
        
        # 遍历场景中的所有纹理
        texture_count = scene.GetTextureCount()
        print(f"找到 {texture_count} 个纹理对象")
        
        for i in range(texture_count):
            texture = scene.GetTexture(i)
            if texture:
                self._process_texture(texture)
        
        # 同时遍历所有材质来查找纹理
        self._scan_materials(scene)
        
        # 复制贴图文件
        if self.textures:
            print(f"\n共找到 {len(self.textures)} 个唯一贴图文件")
            self._copy_textures()
        else:
            print("\n未找到任何贴图文件")
        
        # 清理
        manager.Destroy()
        
        return True
    
    def _process_texture(self, texture):
        """处理单个纹理对象"""
        # 尝试获取文件名,FbxFileTexture类型的纹理有GetFileName方法
        try:
            filename = texture.GetFileName()
            if filename:
                # 检查是否应该排除此贴图
                basename = os.path.basename(filename)
                name_lower = basename.lower()
                
                # 检查文件名是否包含排除的后缀
                should_exclude = False
                for suffix in self.EXCLUDE_SUFFIXES:
                    if suffix in name_lower:
                        should_exclude = True
                        print(f"  - 跳过贴图: {basename} (类型: {suffix.strip('_')})")
                        break
                
                if not should_exclude:
                    self.textures.add(filename)
                    print(f"  - 发现主贴图: {basename}")
        except AttributeError:
            # 不是FbxFileTexture类型,跳过
            pass
    
    def _scan_materials(self, scene):
        """扫描场景中所有材质的纹理"""
        root_node = scene.GetRootNode()
        if root_node:
            self._scan_node_materials(root_node)
    
    def _scan_node_materials(self, node):
        """递归扫描节点及其子节点的材质"""
        # 检查当前节点的材质
        material_count = node.GetMaterialCount()
        for i in range(material_count):
            material = node.GetMaterial(i)
            if material:
                self._scan_material_properties(material)
        
        # 递归处理子节点
        for i in range(node.GetChildCount()):
            self._scan_node_materials(node.GetChild(i))
    
    def _scan_material_properties(self, material):
        """扫描材质的所有属性以查找纹理"""
        # 常见的纹理属性名称（这些常量在运行时从fbx模块中可用）
        try:
            texture_properties = [
                FbxSurfaceMaterial.sDiffuse,  # type: ignore
                FbxSurfaceMaterial.sAmbient,  # type: ignore
                FbxSurfaceMaterial.sSpecular,  # type: ignore
                FbxSurfaceMaterial.sEmissive,  # type: ignore
                FbxSurfaceMaterial.sBump,  # type: ignore
                FbxSurfaceMaterial.sNormalMap,  # type: ignore
                FbxSurfaceMaterial.sTransparentColor,  # type: ignore
                FbxSurfaceMaterial.sReflection,  # type: ignore
                "DiffuseColor",
                "SpecularColor",
                "ShininessExponent",
                "TransparencyFactor",
                "EmissiveColor",
                "AmbientColor"
            ]
        except (NameError, AttributeError):
            # 如果FbxSurfaceMaterial不可用，使用字符串属性名
            texture_properties = [
                "DiffuseColor",
                "SpecularColor",
                "EmissiveColor",
                "AmbientColor"
            ]
        
        for prop_name in texture_properties:
            prop = material.FindProperty(prop_name)
            if prop.IsValid():
                # 检查属性是否有关联的纹理
                try:
                    texture_count = prop.GetSrcObjectCount(FbxCriteria.ObjectType(FbxTexture.ClassId))  # type: ignore
                    for i in range(texture_count):
                        texture = prop.GetSrcObject(FbxCriteria.ObjectType(FbxTexture.ClassId), i)  # type: ignore
                        if texture:
                            self._process_texture(texture)
                except (NameError, AttributeError):
                    # 如果FbxCriteria不可用，跳过
                    pass
    
    def _copy_textures(self):
        """复制贴图文件到输出目录"""
        print(f"\n正在复制贴图到: {self.output_dir}")
        
        copied_count = 0
        failed_count = 0
        
        for texture_path in self.textures:
            if os.path.exists(texture_path):
                filename = os.path.basename(texture_path)
                dest_path = os.path.join(self.output_dir, filename)
                
                try:
                    shutil.copy2(texture_path, dest_path)
                    print(f"  ✓ 已复制: {filename}")
                    copied_count += 1
                except Exception as e:
                    print(f"  ✗ 复制失败 {filename}: {e}")
                    failed_count += 1
            else:
                # 尝试相对路径
                fbx_dir = os.path.dirname(self.fbx_file_path)
                relative_path = os.path.join(fbx_dir, os.path.basename(texture_path))
                
                if os.path.exists(relative_path):
                    filename = os.path.basename(texture_path)
                    dest_path = os.path.join(self.output_dir, filename)
                    
                    try:
                        shutil.copy2(relative_path, dest_path)
                        print(f"  ✓ 已复制 (相对路径): {filename}")
                        copied_count += 1
                    except Exception as e:
                        print(f"  ✗ 复制失败 {filename}: {e}")
                        failed_count += 1
                else:
                    print(f"  ✗ 文件不存在: {texture_path}")
                    failed_count += 1
        
        print(f"\n总结: 成功 {copied_count} 个, 失败 {failed_count} 个")
        print(f"输出目录: {os.path.abspath(self.output_dir)}")


def main():
    """主函数"""
    print("=" * 60)
    print("FBX贴图提取工具")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print(f"  python {sys.argv[0]} <fbx文件路径> [输出目录]")
        print("\n示例:")
        print(f"  python {sys.argv[0]} model/example.fbx")
        print(f"  python {sys.argv[0]} model/example.fbx my_output")
        
        # 如果没有参数,尝试使用默认的示例文件
        default_fbx = "model/example.fbx"
        if os.path.exists(default_fbx):
            print(f"\n未指定FBX文件,使用默认文件: {default_fbx}")
            fbx_file = default_fbx
        else:
            print("\n错误: 请指定FBX文件路径")
            sys.exit(1)
    else:
        fbx_file = sys.argv[1]
    
    # 检查FBX文件是否存在
    if not os.path.exists(fbx_file):
        print(f"错误: 文件不存在: {fbx_file}")
        sys.exit(1)
    
    # 获取输出目录(可选参数)
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    # 创建提取器并执行
    extractor = FBXTextureExtractor(fbx_file, output_dir)
    success = extractor.extract_textures()
    
    print("\n" + "=" * 60)
    if success:
        print("提取完成!")
    else:
        print("提取失败!")
    print("=" * 60)


if __name__ == "__main__":
    main()
