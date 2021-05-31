#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyquery import PyQuery
from html2text import html2text


def clean_html(h: str) -> str:
    ret = ""
    if h == "":
        return ""
    body = PyQuery(h)("body")
    if len(body) == 0:
        return h
    for p_elem in body("p"):
        p = PyQuery(p_elem)

        # Process inner span
        for span_elem in p("span"):
            span = PyQuery(span_elem)
            span_style = span.attr("style")
            span_inner = span.html()
            if span_style.find("font-weight:600") != -1:
                span_inner = "<b>" + span_inner + "</b>"
            if span_style.find("font-style:italic;") != -1:
                span_inner = "<i>" + span_inner + "</i>"
            span.replace_with(span_inner)

        p.remove_attr("style")
        p_inner = p.html()

        # if p.attr("align") == "right":
        #     p_inner = '<div align="right">' + p_inner + '</div>'
        # Handled at save time

        if len(p("br")) == 0:  # avoid duplicate <br> for empty line
            p_inner += "<br>"
        ret += p_inner

    # Simplify <br/>
    ret = ret.replace("<br/>", "<br>")

    # Remove last <br>
    if ret.endswith("<br>"):
        ret = ret[:-4]

    # Verification
    # cleaned_ret = html2text(h).replace("\n", "").replace("**", "").replace(" ", "").replace("_", "")
    # reference = html2text(ret).replace("\n", "").replace("**", "").replace(" ", "").replace("_", "")
    # if cleaned_ret != reference:
    #     with open("html_cleaner.log", "w", encoding="utf-8") as f:
    #         f.write("================ Original ================\n")
    #         f.write(h)
    #         f.write("\n================ ret ================\n")
    #         f.write(ret)
    #         f.write("\n================ html2text(h).strip() ================\n")
    #         f.write(cleaned_ret)
    #         f.write("\n================ html2text(ret).strip() ================\n")
    #         f.write(reference)
    #     raise RuntimeError("html_cleaner verification failure")

    return ret


if __name__ == '__main__':
    print(clean_html("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:16pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">I don't really <span style=" font-weight:600;">think</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">this is accpectable</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">It's too complicated.</p></body></html>"""))

    print("================================================================")

    print(clean_html("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:16pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">This is <span style=" font-weight:600;">too</span> complicated.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">REALLY</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-style:italic;">III</span></p></body></html>"""))

    print("================================================================")

    print(clean_html("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p align="right" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:12px;">123,</span><span style=" font-size:12px; font-style:italic;">223</span></p></body></html>"""))

    print("================================================================")

    print(clean_html("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:20pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">adj.&amp;cn. required, necessary.</p></body></html>"""))

    print("================================================================")
