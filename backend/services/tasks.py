import os
from celery import Celery


def get_celery() -> Celery | None:
    broker_url = os.getenv("CELERY_BROKER_URL")  # e.g., redis://localhost:6379/0
    backend_url = os.getenv("CELERY_RESULT_BACKEND")  # e.g., redis://localhost:6379/1
    if not broker_url or not backend_url:
        return None
    app = Celery("legal_analyzer", broker=broker_url, backend=backend_url)
    return app


celery_app = get_celery()

if celery_app:

    @celery_app.task(name="backend.tasks.run_export_task")
    def run_export_task(file_id: str, format: str, task_id: str):
        # Lazy import to avoid circulars
        from main import analysis_cache, report_generator, export_tasks

        cached_data = analysis_cache[file_id]
        analysis = cached_data["analysis"]
        original_filename = cached_data["original_filename"].rsplit(".", 1)[0]

        try:
            if format.lower() == "json":
                file_path = report_generator.export_as_json(analysis, original_filename)
            else:
                file_path = report_generator.export_as_pdf(analysis, original_filename)
            export_tasks[task_id]["status"] = "completed"
            export_tasks[task_id]["file_path"] = file_path
        except Exception:
            export_tasks[task_id]["status"] = "failed"
