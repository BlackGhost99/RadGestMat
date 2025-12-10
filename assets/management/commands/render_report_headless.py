from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Render the latest AuditLog report to tmp/report_headless_<pk>.html for inspection.'

    def add_arguments(self, parser):
        parser.add_argument('--pk', type=int, help='Primary key of the AuditLog to render (default: latest)')

    def handle(self, *args, **options):
        try:
            from assets.models import AuditLog
            from assets import views as asset_views
        except Exception as e:
            self.stderr.write(f'Error importing project modules: {e}')
            return

        pk = options.get('pk')
        report = None
        if pk:
            report = AuditLog.objects.filter(pk=pk).first()
            if not report:
                self.stderr.write(f'No AuditLog with pk={pk}')
                return
        else:
            report = AuditLog.objects.order_by('-pk').first()
            if not report:
                self.stderr.write('No AuditLog entries found')
                return

        # Build the same context the view would
        formatted_changes = asset_views._format_changes_for_display(report)
        human_sentence = asset_views._build_human_readable_sentence(report, formatted_changes)
        summary = asset_views._build_creative_summary(report) or ''
        context = {
            'report': report,
            'formatted_changes': formatted_changes,
            'summary': summary,
            'human_sentence': human_sentence,
            'context_sentence': asset_views._build_context_sentence(report),
            'sanitized_metadata': asset_views._sanitize_metadata(getattr(report, 'metadata', None)),
        }

        try:
            html = render_to_string('assets/report_detail.html', context)
        except Exception as e:
            self.stderr.write(f'Error rendering template: {e}')
            return

        base = getattr(settings, 'BASE_DIR', os.getcwd())
        tmpdir = os.path.join(base, 'tmp')
        os.makedirs(tmpdir, exist_ok=True)
        outpath = os.path.join(tmpdir, f'report_headless_{report.pk}.html')
        try:
            with open(outpath, 'w', encoding='utf-8') as f:
                f.write(html)
            self.stdout.write(f'Wrote {outpath}')
        except Exception as e:
            self.stderr.write(f'Error writing output file: {e}')
