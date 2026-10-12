# ID Tool

这是一个用于学习、演示和测试的身份证号码生成/校验工具，包含：
- 交互式菜单
- 命令行模式
- 17 位校验位计算
- 14 位基础信息穷举
- 可控批量生成（有限/无限）

重要说明
- 仅用于学习、测试、演示和模拟用途
- 严禁用于任何非法用途、身份欺诈、隐私侵害或违反当地法律法规的行为
- 不要将真实个人信息、真实身份证号码或真实区域编码数据提交到仓库中

## 使用方法

### 1. 交互式运行
```bash
python id_tool.py
```

### 2. 生成样例
```bash
python id_tool.py generate --count 10 --output results.csv
```

### 3. 无限生成（谨慎使用）
```bash
python id_tool.py generate --infinite --output output/id_stream.csv
```

### 4. 计算 17 位校验码
```bash
python id_tool.py calc17 11000020000101123
```

### 5. 14 位穷举
```bash
python id_tool.py exhaust14 11000020000101 --filter male
```

## 文件说明
- `id_tool.py`：主脚本
- `README.md`：项目说明
- `LICENSE`：MIT 许可证
- `.gitignore`：忽略开发文件和输出文件

## 安全建议
- 将仓库保持为私有或仅与可信用户共享
- 不要在仓库中保存真实身份证数据
- 如果需要真实区域码，请自行提供并遵守当地法律法规
- 在任何公开场合使用前，务必确认权限和合规性

## 关于中文版与英文版

如需使用中文版请转到https://github.com/asdasd5543/id-tool/releases/tag/v1.0.0

如需英文版请转到https://github.com/asdasd5543/English-version-ID-Tool/releases/tag/v1.0.0
