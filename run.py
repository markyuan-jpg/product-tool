#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Product Catalog Generator

Usage:
    #整合模式，默认生成全部4个文件
    python run.py --input ./data
    
    #整合模式，只生成产品目录（无价格）
    python run.py --input ./data --without-price
    
    #单文件模式，为每个文件单独生成
    python run.py --single --input ./data
"""
import argparse
import io
import os
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="生成产品目录Excel文件")
    parser.add_argument("--input", "-i", default="./data", help="输入文件夹路径")
    parser.add_argument("--output", "-o", default="./output", help="输出文件夹路径")
    parser.add_argument("--skip-translate", action="store_true", help="跳过翻译")
    parser.add_argument("--no-interactive", "-n", action="store_true", help="非交互模式")
    parser.add_argument("--exchange-rate", type=float, default=None, help="手动指定汇率")
    parser.add_argument("--no-rate-fetch", action="store_true", help="不自动获取汇率")
    parser.add_argument("--template", "-t", choices=["simple", "standard", "detailed"], default=None, help="输出模板")
    parser.add_argument("--no-company-info", action="store_true", help="隐藏公司信息")
    parser.add_argument("--company-name", default=None, help="公司名称")
    parser.add_argument("--company-address", default=None, help="公司地址")
    parser.add_argument("--contact", default=None, help="联系人")
    parser.add_argument("--phone", default=None, help="联系电话")
    parser.add_argument("--price-term", default=None, help="价格条款")
    parser.add_argument("--moq", default=None, help="最小起订量")
    parser.add_argument("--lead-time", default=None, help="交货期")
    parser.add_argument("--payment", default=None, help="付款方式")
    parser.add_argument("--validity", type=int, default=None, help="报价有效期(天)")
    parser.add_argument("--group-by", choices=["none", "file", "sheet"], default="none", help="产品分组方式")
    
    # New arguments for output modes
    parser.add_argument("--single", action="store_true", help="单文件处理模式（不合并）")
    parser.add_argument("--with-price", action="store_true", help="生成报价单（有价格）")
    parser.add_argument("--without-price", action="store_true", help="生成产品目录（无价格）")
    parser.add_argument("--pdf-only", action="store_true", help="只处理PDF文件")
    parser.add_argument("--excel-only", action="store_true", help="只处理Excel文件")
    
    # NEW: 规格参数序列化选项
    parser.add_argument("--industry", default=None, help="行业类型（为后续行业模板预留，如：bike, scooter, power station等）")
    parser.add_argument("--no-serialize", action="store_true", help="禁用规格参数序列化，保留原始列")
    
    args = parser.parse_args()
    
    # Configure logging
    from src.utils.logger import get_logger, set_log_level
    set_log_level("INFO")
    logger = get_logger("run")
    
    # Resolve paths
    input_folder = os.path.abspath(args.input)
    output_folder = os.path.abspath(args.output)
    
    logger.info("产品目录生成器")
    logger.info(f"输入文件夹: {input_folder}")
    logger.info(f"输出文件夹: {output_folder}")
    
    # Check if input exists
    if not os.path.exists(input_folder):
        # If single file specified
        if os.path.isfile(input_folder):
            input_folder = os.path.dirname(input_folder)
        else:
            logger.error(f"输入文件夹不存在: {input_folder}")
            sys.exit(1)
    
    # Check for supported files
    excel_files = []
    pdf_files = []
    
    # Excel files
    for ext in ["*.xlsx", "*.xls"]:
        for f in glob.glob(os.path.join(input_folder, ext)):
            if os.path.isfile(f):
                excel_files.append(f)
    
    # PDF files
    for ext in ["*.pdf"]:
        for f in glob.glob(os.path.join(input_folder, ext)):
            if os.path.isfile(f):
                pdf_files.append(f)
    
    # Apply filters based on args
    if args.pdf_only:
        supported_files = pdf_files
    elif args.excel_only:
        supported_files = excel_files
    else:
        supported_files = excel_files + pdf_files
    
    if not supported_files:
        logger.error(f"没有找到支持的文件")
        sys.exit(1)
    
    logger.info(f"找到 {len(supported_files)} 个文件")
    
    # Get exchange rate
    exchange_rate = args.exchange_rate or 7.2
    if not args.no_rate_fetch:
        from src.core.parser import get_exchange_rate
        exchange_rate = get_exchange_rate()
    
    # Company config
    company_config = {}
    if not args.no_company_info:
        company_config["company_name"] = args.company_name or "Company Name"
        company_config["company_address"] = args.company_address or "Address"
        company_config["contact"] = args.contact or "Contact"
        company_config["phone"] = args.phone or "Phone"
    else:
        company_config["company_name"] = ""
    
    if args.price_term:
        company_config["price_term"] = args.price_term
    if args.moq:
        company_config["moq"] = args.moq
    if args.lead_time:
        company_config["lead_time"] = args.lead_time
    if args.payment:
        company_config["payment"] = args.payment
    if args.validity:
        company_config["validity"] = str(args.validity)
    
    # Default output modes
    with_price = True
    without_price = True
    
    if args.with_price and not args.without_price:
        without_price = False
    if args.without_price and not args.with_price:
        with_price = False
    
    if args.single:
        # Single file mode - process each file separately
        logger.info("单文件处理模式")
        
        for file_path in supported_files:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            sub_folder = os.path.join(output_folder, file_name)
            os.makedirs(sub_folder, exist_ok=True)
            
            logger.info(f"\n处理文件: {os.path.basename(file_path)}")
            
            from src.core.parser import load_single_file
            serialize = not args.no_serialize
            df = load_single_file(file_path, exchange_rate, serialize=serialize)
            
            if df is None or df.empty:
                logger.warning(f"  无法读取: {file_path}")
                continue
            
            logger.info(f"  读取到 {len(df)} 个产品")
            
            # Skip translation if requested
            if args.skip_translate:
                logger.info("  跳过翻译")
                df_en = df.copy()
            else:
                try:
                    from src.core.translator import ProductTranslator
                    translator = ProductTranslator()
                    if translator.available:
                        df_en = translator.translate_dataframe(df)
                    else:
                        df_en = df.copy()
                except:
                    df_en = df.copy()
            
            from src.output.excel_writer import save_catalogs
            
            # Generate without price
            if without_price:
                save_catalogs(df, sub_folder, template_name=args.template, use_translation=False, use_price=False)
                if "name_en" in df_en.columns:
                    save_catalogs(df_en, sub_folder, template_name=args.template, use_translation=True, use_price=False)
            
            # Generate with price
            if with_price:
                save_catalogs(df, sub_folder, template_name=args.template, use_translation=False, use_price=True)
                if "name_en" in df_en.columns:
                    save_catalogs(df_en, sub_folder, template_name=args.template, use_translation=True, use_price=True)
    else:
        # Integration mode - merge all files
        logger.info("[1/6] 读取文件...")
        from src.core.parser import load_documents
        
        # Determine file type filter
        if args.pdf_only:
            file_type = "pdf"
        elif args.excel_only:
            file_type = "excel"
        else:
            file_type = "all"
        
        # 规格参数序列化选项
        serialize = not args.no_serialize
        if args.no_serialize:
            logger.info("  禁用规格参数序列化")
        
        df = load_documents(input_folder, exchange_rate, fetch_rate=not args.no_rate_fetch, file_type=file_type, serialize=serialize)
        logger.info(f"读取到 {len(df)} 个产品")
        
        if df.empty:
            logger.error("没有解析到产品数据")
            sys.exit(1)
        
        # Match images
        logger.info("\n[4/6] 匹配产品图片...")
        from src.core.parser import match_images
        
        if "image_path" not in df.columns or df["image_path"].isna().all():
            image_folder = input_folder
            for subfolder in ["images", "imgs", "pics"]:
                test_folder = os.path.join(input_folder, subfolder)
                if os.path.isdir(test_folder):
                    image_folder = test_folder
                    break
            df = match_images(df, image_folder=image_folder)
        else:
            logger.info("  图片已从Excel提取")
        
        # Skip translation if requested
        if args.skip_translate:
            logger.info("\n[5/6] 跳过翻译")
            df_en = df.copy()
        else:
            logger.info("\n[5/6] 翻译为英文...")
            try:
                from src.core.translator import ProductTranslator
                translator = ProductTranslator()
                if translator.available:
                    df_en = translator.translate_dataframe(df)
                    logger.info("  翻译完成")
                else:
                    logger.info("  翻译模型不可用")
                    df_en = df.copy()
            except Exception as e:
                logger.info(f"  翻译失败: {e}")
                df_en = df.copy()
        
        # Save outputs
        logger.info("\n[6/6] 生成文件...")
        from src.output.excel_writer import save_catalogs
        
        if without_price:
            save_catalogs(df, output_folder, template_name=args.template, use_translation=False, use_price=False)
            if "name_en" in df_en.columns:
                save_catalogs(df_en, output_folder, template_name=args.template, use_translation=True, use_price=False)
        
        if with_price:
            save_catalogs(df, output_folder, template_name=args.template, use_translation=False, use_price=True)
            if "name_en" in df_en.columns:
                save_catalogs(df_en, output_folder, template_name=args.template, use_translation=True, use_price=True)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    import glob
    main()