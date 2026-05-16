import argostranslate.package
for p in argostranslate.package.get_installed_packages():
    print(p.from_code + "->" + p.to_code)