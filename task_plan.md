# 产品目录生成修复计划

## 目标
修复产品目录生成工具，实现:
1. 正确读取中文编码的Excel文件
2. 提取源文件中的图片并嵌入到输出Excel
3. 输出文件保留中文内容

## 问题分析

### 问题1: 中文编码问题
- param_price.xlsx 读取时中文显示乱码
- 需要在 pd.read_excel() 添加 encoding 参数

### 问题2: 图片提取与匹配
- param_price.xlsx: 提取66张图片，但行号索引不匹配
- consumables: 使用 DISPIMG 公式引用图片，需要解析公式获取图片ID

### 问题3: 图片没有嵌入输出
- output Excel 中 image_path 全为空
- 需要在 excel_writer.py 添加图片嵌入功能

## 修复计划

### Phase 1: 修复中文编码 (parser.py)
- [ ] 添加多种编码尝试读取 Excel
- [ ] 测试 param_price.xlsx 正确解析

### Phase 2: 修复图片提取 (parser.py)
- [ ] 修改 extract_excel_images 匹配逻辑
- [ ] 添加 DISPIMG 公式解析
- [ ] 测试图片提取

### Phase 3: 修复图片嵌入输出 (excel_writer.py)
- [ ] 添加图片嵌入函数
- [ ] 在 save_catalogs 中调用

### Phase 4: 测试整合
- [ ] 完整流程测试
- [ ] 验证输出

## 当前状态
- 3个源文件: consumables(en), param_price(cn), 新品报价表(cn)
- 处理结果: 130个产品
- 输出: image_path 全为空