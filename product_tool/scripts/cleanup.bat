@echo off
chcp 65001 >nul

REM Delete debug/test files
del /Q check_v4.py compare.py summary_gen.py check_gen.py test_generic.py test_parse_medical.py 2>nul
del /Q debug_hubei.py debug_dmio.py debug_detect.py debug_cols.py debug_result.py debug_full.py 2>nul
del /Q debug_trace.py debug_price3.py debug_price2.py debug_price.py debug_zhanghu3.py debug_zhanghu2.py 2>nul
del /Q debug_zhanghu.py debug_source2.py debug_source.py debug_missing.py debug_botswana.py 2>nul
del /Q check_raw.py test_price2.py check_output.py check_prices.py test_price.py 2>nul
del /Q merge_data.py organize_images.py rename_images.py find_models.py debug_param.py debug_pi.py 2>nul
del /Q run_test.bat 2>nul

REM Delete output folders
rmdir /S /Q output\单独解析 2>nul
rmdir /S /Q output\通用解析 2>nul  
rmdir /S /Q output\通用解析_v4 2>nul

echo Done!