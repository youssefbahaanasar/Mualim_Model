import html

from .catalog import get_hadith
from .comparison import compare_texts, tokenize
from .inference import HadithRecognizer


def select_reference(number, start, count, scope="full"):
    words = get_hadith(int(number), scope=scope).split()
    start = 1 if start is None else int(start)
    count = 0 if count is None else int(count)
    if start < 1 or count < 0 or start > len(words):
        raise ValueError("اختر بداية صحيحة؛ عدد الكلمات صفر يعني حتى نهاية الحديث")
    return " ".join(words[start - 1:] if count == 0 else words[start - 1:start - 1 + count])


def reset_reference(number, scope):
    return 1, 0, select_reference(number, 1, 0, scope), "", "", None


def update_reference(number, start, count, scope):
    return select_reference(number, start, count, scope), "", "", None


def render_result(result):
    labels = {"replace": "استبدال", "delete": "كلمة ناقصة", "insert": "كلمة زائدة"}
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            labels[item["type"]], item["reference_index"] + 1,
            html.escape(item["expected"]), html.escape(item["predicted"]))
        for item in result["errors"]
    )
    if not rows:
        return '<p dir="rtl">لم تظهر اختلافات كلمات بعد تجاهل التشكيل والترقيم.</p>'
    return ('<div dir="rtl"><table><thead><tr><th>الاختلاف</th><th>موضع الكلمة</th>'
            '<th>المرجع</th><th>النص المستخرج</th></tr></thead><tbody>' + rows + '</tbody></table></div>')


def create_app():
    import gradio as gr

    recognizer = HadithRecognizer()

    def analyze(audio, number, start, count, scope):
        try:
            if not audio:
                raise ValueError("ارفع تسجيلًا أو سجّل صوتك أولًا")
            reference = select_reference(number, start, count, scope)
            if not tokenize(reference):
                raise ValueError("اختر مقطعًا يحتوي على كلمات")
            transcript = recognizer.transcribe(audio)
            result = compare_texts(reference, transcript)
            result["hadith_number"] = int(number)
            result["reference_scope"] = scope
            return transcript, render_result(result), result
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    with gr.Blocks(title="مراجعة الأربعين النووية") as app:
        gr.Markdown("# مراجعة قراءة الأربعين النووية\n"
                    "اختر الحديث وسجّل قراءتك. النتائج اختلافات بين النص المستخرج والمرجع؛ "
                    "قد يخطئ التعرف على الكلام. لا تُقيّم هذه النسخة الحركات أو مخارج الحروف، "
                    "ولا تتحقق من أن الصوت حديث أو ترفض القرآن تلقائيًا.")
        number = gr.Dropdown(choices=[(f"الحديث {i}", str(i)) for i in range(1, 43)], value="1", label="الحديث")
        scope = gr.Radio(choices=[("المتن فقط", "matn"), ("الحديث كاملًا", "full")],
                         value="matn", label="نطاق القراءة")
        gr.Markdown("المتن فقط: الرواية الأساسية بدون مقدمة الراوي والتخريج. "
                    "الحديث كاملًا: يشمل الراوي والتخريج والروايات الإضافية كما في المصدر. "
                    "اقرأ النص المعروض؛ يمكنك تحديد جزء منه بعد اختيار النطاق.")
        with gr.Row():
            start = gr.Number(value=1, minimum=1, precision=0, label="بداية الكلمة (من ١)")
            count = gr.Number(value=0, minimum=0, precision=0, label="عدد الكلمات (٠ حتى النهاية)")
        reference = gr.Textbox(value=get_hadith(1, "matn"), label="المقطع المرجعي", interactive=False, lines=8)
        audio = gr.Audio(sources=["upload", "microphone"], type="filepath", label="تسجيل الحديث")
        button = gr.Button("راجع القراءة", variant="primary")
        transcript = gr.Textbox(label="النص المستخرج آليًا", interactive=False)
        differences = gr.HTML()
        result = gr.JSON(label="تفاصيل المقارنة")
        review = button.click(analyze, [audio, number, start, count, scope],
                              [transcript, differences, result], api_name="analyze")
        # Reset offsets when switching to a shorter hadith or reading scope.
        for control in (number, scope):
            control.change(reset_reference, [number, scope],
                           [start, count, reference, transcript, differences, result], cancels=[review])
        for control in (start, count):
            control.input(update_reference, [number, start, count, scope],
                          [reference, transcript, differences, result], cancels=[review])
        gr.Markdown("مصدر النصوص: [hadith-api](https://github.com/fawazahmed0/hadith-api)، "
                    "ترخيص Unlicense. المجموعة تضم ٤٢ حديثًا.")
    return app


def main():
    create_app().queue().launch(server_name="127.0.0.1", share=False)


if __name__ == "__main__":
    main()
