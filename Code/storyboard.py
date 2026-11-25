"""Lay out one portrait storyboard page per scene using frames from the master."""
from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


def save_board(scenes, target, clock):
    fonts = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("BoardSans", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("BoardBold", str(fonts / "VeraBd.ttf")))
    pdf = Canvas(str(target), pagesize=A4)
    pdf.setTitle("What Is a Vector? | Six-scene storyboard")
    w, h = A4
    margin = 42
    width = w - 2 * margin
    ink, muted, accent = "#142A38", "#425B66", "#00735F"

    def write(x, y, words, font="BoardSans", size=10, color=ink):
        pdf.setFillColor(HexColor(color))
        pdf.setFont(font, size)
        pdf.drawString(x, y, words)

    for index, scene in enumerate(scenes, 1):
        write(margin, h-40, "M3   /   MATHEMATICAL ANIMATION", "BoardBold", 9, accent)
        write(w-128, h-40, "STORYBOARD", "BoardBold", 9, muted)
        pdf.setStrokeColor(HexColor("#BACAD0"))
        pdf.line(margin, h-53, w-margin, h-53)
        write(margin, h-83, f"SCENE {index:02d}     /     {scene['span']}", "BoardBold", 11, accent)
        write(margin, h-122, scene["title"], "Times-Roman", 31)
        image_height = width * 9 / 16
        image_bottom = h-144-image_height
        pdf.drawImage(scene["image"], margin, image_bottom, width, image_height)
        write(margin, image_bottom-17, f"Master frame at {clock(scene['still_time'])}",
              size=9, color=muted)
        y = image_bottom-49
        for title, body in [("VISUAL ACTION", scene["action"]), ("NARRATION CUE", scene["cue"]),
                            ("MATHEMATICS", scene["math"])]:
            write(margin, y, title, "BoardBold", 9, accent)
            y -= 19
            for line in simpleSplit(body, "BoardSans", 11, width):
                write(margin, y, line, size=11)
                y -= 16
            y -= 15
        if index == 1:
            write(margin, y, "LEARNING OBJECTIVE", "BoardBold", 9, accent)
            for line in simpleSplit("Read a displacement from its components and predict "
                                    "the endpoint of a sum of scaled movements.", "BoardSans", 11, width):
                y -= 17
                write(margin, y, line, size=11)
        if y < 44:
            raise ValueError(f"Storyboard text reaches the footer on page {index}.")
        pdf.line(margin, 44, w-margin, 44)
        write(margin, 27, "What Is a Vector?", size=9, color=muted)
        write(w-margin-29, 27, f"{index}  /  6", size=9, color=muted)
        pdf.showPage()
    pdf.save()
