#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit Web UI for Product Catalog Generator

Usage:
    streamlit run app.py
"""
import io
import os
import sys
import glob
import tempfile
import time
from pathlib import Path

# Fix encoding
if sys.platform == "win32":
    import io as sys_io
    sys.stdout = sys_io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = sys_io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import streamlit as st
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ==================== UTILITY FUNCTIONS ====================

class StreamlitLogger:
    """Custom logger that displays in Streamlit."""
    
    def __init__(self):
        self.logs = []
        self.progress_bar = None
        self.status_text = None
    
    def init_progress(self, total_steps=6):
        """Initialize progress bar."""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def log(self, message, level="INFO"):
        """Add log message."""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] [{level}] {message}")
    
    def update_progress(self, current, total, message=""):
        """Update progress bar."""
        if self.progress_bar:
            self.progress_bar.progress(current / total)
        if self.status_text and message:
            self.status_text.text(message)
    
    def get_logs(self):
        """Return logs as string."""
        return "\n".join(self.logs)


# Global logger instance
logger = StreamlitLogger()


def save_uploaded_files(uploaded_files):
    """Save uploaded files to temp directory and return path."""
    temp_dir = tempfile.mkdtemp()
    saved_paths = []

    for uploaded_file in uploaded_files:
        # Determine extension
        name = uploaded_file.name
        ext = os.path.splitext(name)[1].lower()

        # Save to temp file
        path = os.path.join(temp_dir, name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        saved_paths.append(path)

    return temp_dir, saved_paths


@st.cache_resource
def get_translator():
    """Load and cache translator."""
    from src.core.translator import ProductTranslator
    return ProductTranslator(offline=True)


# ==================== MAIN PROCESSING ====================

def _process_and_show_results(
    uploaded_files,
    filter_input,
    handle_dup,
    translate_opt,
    generate_pdf,
    generate_pi,
    price_type,
    buyer_info,
):
    """Process files and show results."""
    
    with st.spinner("处理中..."):
        try:
            # Process
            results = process_files(
                uploaded_files,
                filter_text=filter_input if filter_input else None,
                handle_duplicates=handle_dup,
                translate=translate_opt,
                generate_pdf=generate_pdf,
                generate_pi=generate_pi,
                price_type=price_type,
                buyer_info=buyer_info,
            )

            if results.get("errors"):
                for err in results["errors"]:
                    st.error(err)

            st.success(f"✅ 处理完成! 共 {len(results['df'])} 条记录")

            # Download buttons
            st.markdown("---")
            st.subheader("📥 下载文件")

            cols = st.columns(3)

            # Chinese version
            if "产品目录_中文.xlsx" in results["files"]:
                cols[0].download_button(
                    label="📄 中文版",
                    data=results["files"]["产品目录_中文.xlsx"],
                    file_name="产品目录_中文.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # Bilingual version
            if "产品目录_中英文.xlsx" in results["files"]:
                cols[1].download_button(
                    label="📄 中英文版",
                    data=results["files"]["产品目录_中英文.xlsx"],
                    file_name="产品目录_中英文.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # English version
            if "产品目录_英文.xlsx" in results["files"]:
                cols[2].download_button(
                    label="📄 英文版",
                    data=results["files"]["产品目录_英文.xlsx"],
                    file_name="产品目录_英文.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # PDF versions
            if generate_pdf:
                pdf_cols = st.columns(2)
                if "产品目录_中文.pdf" in results["files"]:
                    pdf_cols[0].download_button(
                        label="📕 中文版 PDF",
                        data=results["files"]["产品目录_中文.pdf"],
                        file_name="产品目录_中文.pdf",
                        mime="application/pdf",
                    )
                
                if "Product_Catalog.pdf" in results["files"]:
                    pdf_cols[1].download_button(
                        label="📕 英文版 PDF",
                        data=results["files"]["Product_Catalog.pdf"],
                        file_name="Product_Catalog.pdf",
                        mime="application/pdf",
                    )

            # PI
            if generate_pi and "Proforma_Invoice.pdf" in results["files"]:
                st.download_button(
                    label="📋 形式发票 (PI)",
                    data=results["files"]["Proforma_Invoice.pdf"],
                    file_name="Proforma_Invoice.pdf",
                    mime="application/pdf",
                )

            # Show processing logs (collapsible)
            if results.get("logs"):
                with st.expander("📝 处理日志"):
                    st.text(results["logs"])

            # Show preview
            with st.expander("👀 数据预览"):
                st.dataframe(results["df"].head(10))

        except Exception as e:
            st.error(f"❌ 处理失败: {e}")
            import traceback
            st.code(traceback.format_exc())


def process_files(
    uploaded_files,
    filter_text=None,
    handle_duplicates=True,
    translate=False,
    generate_pdf=False,
    generate_pi=False,
    price_type="FOB",
    buyer_info=None,
):
    """
    Process uploaded files end-to-end.
    
    Args:
        uploaded_files: List of uploaded files
        filter_text: Filter query (optional)
        handle_duplicates: Whether to handle duplicates
        translate: Whether to translate
        generate_pdf: Whether to generate PDF
        generate_pi: Whether to generate PI
        price_type: Price type (FOB/CIF/EXW)
        buyer_info: Buyer info for PI (dict)
    """
    global logger
    results = {
        "df": None,
        "df_translated": None,
        "files": {},
        "errors": [],
        "has_translation": False,
        "logs": [],
    }
    
    # Initialize progress tracking
    total_steps = 6  # 1:save, 2:load, 3:filter, 4:translate, 5:save, 6:pi
    logger.init_progress(total_steps)
    logger.update_progress(0, total_steps, "准备中...")
    logger.log("开始处理文件")
    
    # Step 1: Save uploaded files to temp
    logger.update_progress(1, total_steps, "📂 保存上传文件...")
    logger.log(f"保存 {len(uploaded_files)} 个文件")
    temp_dir, file_paths = save_uploaded_files(uploaded_files)
    logger.log(f"文件保存到临时目录: {temp_dir}")
    
    # Step 2: Load files using parser
    logger.update_progress(2, total_steps, "📖 加载数据...")
    logger.log("开始加载文件...")
    try:
        from src.core.parser import load_documents
        df = load_documents(temp_dir, fetch_rate=False)
    except Exception as e:
        logger.log(f"加载失败: {e}", "ERROR")
        results["errors"].append(str(e))
        results["logs"] = logger.get_logs()
        return results

    if df is None or df.empty:
        logger.log("无法读取任何数据", "ERROR")
        results["errors"].append("无法读取任何数据")
        results["logs"] = logger.get_logs()
        return results

    logger.log(f"加载了 {len(df)} 条产品记录")
    results["df"] = df

    # Step 3: Filter (if provided)
    if filter_text:
        logger.update_progress(3, total_steps, "🔍 应用筛选...")
        logger.log(f"筛选条件: {filter_text}")
        try:
            from src.nlp.filter_parser import parse_filter_safe
            columns = df.columns.tolist()
            query = parse_filter_safe(filter_text, columns)

            if query and query != "True":
                df_filtered = df.query(query)
                logger.log(f"筛选后剩余 {len(df_filtered)} 条记录")
                df = df_filtered
        except Exception as e:
            logger.log(f"筛选失败: {e}", "WARNING")

        results["df"] = df

    # Step 4: Deduplicate
    if handle_duplicates and "model" in df.columns:
        duplicates = df[df.duplicated(subset=["model"], keep=False)]
        if not duplicates.empty:
            logger.log(f"发现 {duplicates['model'].nunique()} 个重复型号", "WARNING")

    # Step 5: Translate
    logger.update_progress(4, total_steps, "🌐 翻译...")
    if translate:
        logger.log("开始翻译...")
        try:
            translator = get_translator()
            if translator.available:
                df_translated = translator.translate_dataframe(df)
                results["has_translation"] = True
                logger.log("翻译完成")
            else:
                logger.log("翻译模型不可用，跳过", "WARNING")
                df_translated = df
        except Exception as e:
            logger.log(f"翻译失败: {e}", "WARNING")
            df_translated = df
    else:
        logger.log("跳过翻译")
        df_translated = df

    results["df_translated"] = df_translated

    # Step 6: Generate Excel files
    logger.update_progress(5, total_steps, "💾 生成Excel文件...")
    logger.log("开始生成输出文件...")
    from src.output.excel_writer import save_catalogs_with_pdf

    output_folder = tempfile.mkdtemp()
    saved = save_catalogs_with_pdf(
        df_translated,
        output_folder,
        include_translated=translate,
        generate_pdf=generate_pdf,
    )

    for f in saved:
        if os.path.exists(f):
            with open(f, "rb") as fp:
                results["files"][os.path.basename(f)] = fp.read()
            logger.log(f"生成文件: {os.path.basename(f)}")

    # Step 7: Generate PI
    if generate_pi and buyer_info:
        logger.update_progress(6, total_steps, "📋 生成形式发票...")
        logger.log("生成形式发��...")
        try:
            from src.output.pi_generator import generate_pi as gen_pi, DEFAULT_SELLER_INFO
            
            df_pi = df_translated.copy()
            if "quantity" not in df_pi.columns:
                df_pi["quantity"] = 1
            
            pi_output = os.path.join(output_folder, "Proforma_Invoice.pdf")
            result = gen_pi(df_pi, buyer_info, DEFAULT_SELLER_INFO, pi_output)
            
            if result and os.path.exists(result):
                with open(result, "rb") as fp:
                    results["files"]["Proforma_Invoice.pdf"] = fp.read()
                logger.log("生成 Proforma_Invoice.pdf")
        except Exception as e:
            logger.log(f"生成PI失败: {e}", "ERROR")

    logger.log("处理完成")
    results["logs"] = logger.get_logs()
    return results


# ==================== STREAMLIT UI ====================

st.set_page_config(
    page_title="外贸产品目录生成器",
    page_icon="📦",
    layout="wide",
)

st.title("📦 外贸产品目录生成器")
st.markdown("上传Excel/PDF/DOCX文件，生成多语言产品目录")

# Sidebar for options
with st.sidebar:
    st.header("⚙️ 设置")

    st.subheader("📁 支持格式")
    st.markdown("""
    **支持格式**: .xlsx, .xls, .pdf, .docx, .csv
    """)

    st.subheader("🔧 处理选项")
    handle_dup = st.checkbox("处理重复型号", value=True)
    translate_opt = st.checkbox("🌐 翻译为英文", value=False)
    generate_pdf = st.checkbox("📄 生成 PDF", value=False)
    generate_pi = st.checkbox("📋 生成形式发票", value=False)
    
    price_type = st.selectbox(
        "💰 价格类型",
        options=["工厂价", "FOB", "CIF"],
        index=1,
    )

# Main area - File Upload
uploaded_files = st.file_uploader(
    "📁 上传产品文件",
    type=["xlsx", "xls", "pdf", "docx", "csv"],
    accept_multiple_files=True,
    help="支持 xlsx, xls, pdf, docx, csv 格式",
)

if uploaded_files:
    st.success(f"✅ 已上传 {len(uploaded_files)} 个文件")

    # Show uploaded files
    with st.expander("📂 查看上传的文件"):
        for f in uploaded_files:
            st.write(f"  - {f.name} ({f.size/1024:.1f} KB)")

    # Filter input
    filter_input = st.text_input(
        "🔍 筛选条件（可选）",
        placeholder="例如：价格在100到500之间",
        help="使用自然语言描述筛选条件",
    )

    # Process button
    if st.button("🚀 开始生成", type="primary", use_container_width=True):
        
        # Collect buyer info AFTER clicking Generate if PI is selected
        buyer_info = None
        if generate_pi:
            with st.form("buyer_info_form"):
                st.subheader("📋 买家信息 (形式发票)")
                
                col1, col2 = st.columns(2)
                with col1:
                    buyer_company = st.text_input("公司名称 *", "")
                    buyer_address = st.text_area("地址", "")
                with col2:
                    buyer_contact = st.text_input("联系人", "")
                    buyer_phone = st.text_input("电话/邮箱", "")
                
                submit_buyer = st.form_submit_button("确认并继续")
            
            if not buyer_company:
                st.warning("请填写公司名称后继续")
            elif submit_buyer:
                buyer_info = {
                    "company": buyer_company,
                    "address": buyer_address,
                    "contact": buyer_contact,
                    "phone": buyer_phone,
                }
                
                # Proceed with processing
                _process_and_show_results(
                    uploaded_files,
                    filter_input,
                    handle_dup,
                    translate_opt,
                    generate_pdf,
                    generate_pi,
                    price_type,
                    buyer_info,
                )
            try:
                # Process
                results = process_files(
                    uploaded_files,
                    filter_text=filter_input if filter_input else None,
                    handle_duplicates=handle_dup,
                    translate=translate_opt,
                    generate_pdf=generate_pdf,
                    generate_pi=generate_pi,
                    price_type=price_type,
                    buyer_info=buyer_info,
                )

                if results.get("errors"):
                    for err in results["errors"]:
                        st.error(err)

                st.success(f"✅ 处理完成! 共 {len(results['df'])} 条记录")

                # Download buttons
                st.markdown("---")
                st.subheader("📥 下载文件")

                cols = st.columns(3)

                # Chinese version
                if "产品目录_中文.xlsx" in results["files"]:
                    cols[0].download_button(
                        label="📄 中文版",
                        data=results["files"]["产品目录_中文.xlsx"],
                        file_name="产品目录_中文.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                # Bilingual version
                if "产品目录_中英文.xlsx" in results["files"]:
                    cols[1].download_button(
                        label="📄 中英文版",
                        data=results["files"]["产品目录_中英文.xlsx"],
                        file_name="产品目录_中英文.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                # English version
                if "产品目录_英文.xlsx" in results["files"]:
                    cols[2].download_button(
                        label="📄 英文版",
                        data=results["files"]["产品目录_英文.xlsx"],
                        file_name="产品目录_英文.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                # PDF versions
                if generate_pdf:
                    pdf_cols = st.columns(2)
                    if "产品目录_中文.pdf" in results["files"]:
                        pdf_cols[0].download_button(
                            label="📕 中文版 PDF",
                            data=results["files"]["产品目录_中文.pdf"],
                            file_name="产品目录_中文.pdf",
                            mime="application/pdf",
                        )
                    
                    if "Product_Catalog.pdf" in results["files"]:
                        pdf_cols[1].download_button(
                            label="📕 英文版 PDF",
                            data=results["files"]["Product_Catalog.pdf"],
                            file_name="Product_Catalog.pdf",
                            mime="application/pdf",
                        )

                # PI
                if generate_pi and "Proforma_Invoice.pdf" in results["files"]:
                    st.download_button(
                        label="📋 形式发票 (PI)",
                        data=results["files"]["Proforma_Invoice.pdf"],
                        file_name="Proforma_Invoice.pdf",
                        mime="application/pdf",
                    )

                # Show processing logs (collapsible)
                if results.get("logs"):
                    with st.expander("📝 处理日志"):
                        st.text(results["logs"])

                # Show preview
                with st.expander("👀 数据预览"):
                    st.dataframe(results["df"].head(10))

            except Exception as e:
                st.error(f"❌ 处理失败: {e}")
                import traceback
                st.code(traceback.format_exc())

else:
    # Show sample instructions
    st.info("👆 请上传产品文件开始")

    st.markdown("""
    ### 📖 使用步骤:
    1. 上传产品文件 (xlsx, xls, pdf, docx, csv)
    2. 输入筛选条件（可选）
    3. 选择处理选项
    4. 点击"开始生成"
    5. 下载生成的文件

    ### 📦 输出文件:
    - **中文版**: 只含中文
    - **中英文版**: 中文+英文
    - **英文版**: 只含英文
    - **PDF**: 可选的 PDF 版本
    - **PI**: 形式发票 (可选)
    """)


# Footer
st.markdown("---")
st.caption("Powered by Streamlit + Pandas")