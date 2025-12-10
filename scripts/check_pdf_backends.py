import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print('BASE_DIR=', BASE_DIR)

print('WKHTMLTOPDF_CMD env:', os.environ.get('WKHTMLTOPDF_CMD'))
print('shutil.which wkhtmltopdf:', shutil.which('wkhtmltopdf'))

bin_dir = os.path.join(BASE_DIR, 'bin')
found = None
if os.path.isdir(bin_dir):
    for root, dirs, files in os.walk(bin_dir):
        for f in files:
            if f.lower().startswith('wkhtmltopdf'):
                found = os.path.join(root, f)
                break
        if found:
            break

print('bin candidate:', found)

try:
    import pdfkit
    print('pdfkit import: OK')
except Exception as e:
    print('pdfkit import failed:', e)
    pdfkit = None

html = '<html><body><h1>Test</h1><p>pdf test</p></body></html>'

if pdfkit:
    wk = os.environ.get('WKHTMLTOPDF_CMD') or shutil.which('wkhtmltopdf') or found
    print('using wkhtml:', wk)
    if wk:
        try:
            config = pdfkit.configuration(wkhtmltopdf=wk)
            options = {'enable-local-file-access': '', 'load-error-handling': 'ignore', 'encoding': 'UTF-8'}
            out = pdfkit.from_string(html, False, options=options, configuration=config)
            if out:
                print('pdfkit.from_string returned bytes len:', len(out))
            else:
                print('pdfkit.from_string returned falsy value')
        except Exception as e:
            print('pdfkit generation error:', repr(e))
    else:
        print('No wkhtmltopdf found for pdfkit')

try:
    from weasyprint import HTML
    print('weasyprint import OK')
    try:
        pdf = HTML(string=html).write_pdf()
        print('weasyprint wrote pdf bytes len:', len(pdf))
    except Exception as e:
        print('weasyprint generation error:', repr(e))
except Exception as e:
    print('weasyprint not available:', repr(e))

print('done')
