import os
import pdfplumber

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

ROOT = r"C:/Users/DELL/Videos/Datasets/emt_ai/datasets"  # scan everything under here

found, opened, with_text, no_text, failed = 0, 0, 0, 0, []

for dirpath, _, filenames in os.walk(ROOT):
    for fn in filenames:
        if fn.lower().endswith(".pdf"):
            found += 1
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT)

            # PDF name in yellow
            print(f"\n===== {YELLOW}{rel}{RESET} =====")

            try:
                with pdfplumber.open(path) as pdf:
                    opened += 1
                    any_text = False
                    for i, page in enumerate(pdf.pages, start=1):
                        # Page number in green
                        print(f"\n{GREEN}--- Page {i} ---{RESET}")
                        try:
                            text = page.extract_text()
                            if text and text.strip():
                                any_text = True
                                print(text)
                            else:
                                print("[No text found on this page]")
                        except Exception as e:
                            print(f"[Error extracting this page: {e}]")
                    if any_text:
                        with_text += 1
                    else:
                        no_text += 1
            except Exception as e:
                failed.append((rel, str(e)))
                print(f"[SKIPPED: could not open] {e}")

print("\n" + "-"*80)
print(f" \n===== {YELLOW} =======   Scanned under: {ROOT}")
print(f" \n===== {YELLOW} =======   PDFs found:        {found}")
print(f" \n===== {YELLOW} =======   Opened successfully:{opened}")
print(f"  \n===== {YELLOW} =======  With text:         {with_text}")
print(f"  \n===== {YELLOW} =======  No text (likely scans): {no_text}")
print(f"Failed to open:    {len(failed)}")
if failed:
    print("\nFailed files:")
    for rel, reason in failed:
        print(f" - {rel} -> {reason}")
