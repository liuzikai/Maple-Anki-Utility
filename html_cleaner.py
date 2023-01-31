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
            if span_style.find("font-weight:") != -1:
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
