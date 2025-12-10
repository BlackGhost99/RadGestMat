WeasyPrint installation notes (Windows)

WeasyPrint requires native (C) libraries on Windows (Cairo, Pango, GDK/GTK runtime). pip installing `weasyprint` may fail until these are installed.

Recommended steps:

1) Install a GTK runtime / Cairo + Pango environment.
   - Easiest option: use the GTK Runtime installer (3.x) from "GTK for Windows Runtime" (search for "GTK for Windows Runtime Environment Installer") and follow the installer.
   - Alternative (advanced): use MSYS2 and install the needed packages:
     - Install MSYS2 (https://www.msys2.org/) then run (in MSYS2 Mingw64 shell):

       pacman -Syu
       pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-cairo mingw-w64-x86_64-pango mingw-w64-x86_64-gdk-pixbuf

     - Make sure the `mingw64/bin` is on PATH when running your Python environment if you installed shared libraries that way.

2) Install the Python package in the project's virtualenv:

   PowerShell example (run from project root):

   & S:\Brice\RadGestMat\.venv\Scripts\Activate.ps1
   pip install weasyprint

3) If pip install fails with missing build dependencies, ensure you have a working C compiler and the native libs (see step 1). On Windows many users find the GTK runtime installer easiest.

4) Verification (in project root):

   & S:\Brice\RadGestMat\.venv\Scripts\Activate.ps1
   python -c "from weasyprint import HTML; print('weasyprint available')"

Notes:
- WeasyPrint pulls several Python packages as dependencies (e.g. cairocffi). These Python packages also need native Cairo headers/libraries to build or work.

wkhtmltopdf alternative (recommended on Windows)
------------------------------------------------
- If you prefer a simpler server-side PDF strategy on Windows, consider `wkhtmltopdf` + `pdfkit`.
- Download the wkhtmltopdf Windows binary from: https://wkhtmltopdf.org/downloads.html
- Install the package or unzip the portable build and place `wkhtmltopdf.exe` somewhere on your PATH (for example `C:\Program Files\wkhtmltopdf\bin`).
- In the project's venv install the Python helper:

   & S:\Brice\RadGestMat\.venv\Scripts\Activate.ps1
   pip install pdfkit

- The application will detect `wkhtmltopdf` automatically if it's on PATH. Alternatively, set the environment variable `WKHTMLTOPDF_CMD` to the full path of `wkhtmltopdf.exe`.

This repository includes a fallback implementation that will try WeasyPrint first, then `wkhtmltopdf` via `pdfkit` before showing the HTML fallback message.

If you want, I can try `pip install weasyprint` and `pip install pdfkit` now and report the output; on Windows you'll still need to install a wkhtmltopdf binary or the GTK runtime for WeasyPrint to produce PDFs.
