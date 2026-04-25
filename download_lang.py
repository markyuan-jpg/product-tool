# Check argos-translate packages
print("Checking available translations...")

try:
    import argostranslate.package
    
    # Already installed
    installed = argostranslate.package.get_installed_packages()
    print(f"Already installed:")
    for pkg in installed:
        print(f"  {pkg.from_code} -> {pkg.to_code}")
    
    # Check if we can do en->zh
    print("\nLooking for English -> Chinese...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    
    found_en_zh = None
    for pkg in available:
        if pkg.from_code == "en" and pkg.to_code == "zh":
            found_en_zh = pkg
            print(f"Found en->zh: {pkg.from_name} -> {pkg.to_name}")
            break
    
    if found_en_zh:
        print("Installing en->zh...")
        found_en_zh.install()
        print("Done!")
    else:
        # Try search more broadly
        print("Searching for any Chinese...")
        for pkg in available[:20]:
            if "zh" in [pkg.from_code, pkg.to_code]:
                print(f"  {pkg.from_code} -> {pkg.to_code}: {pkg.from_name}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()