"""The framework-spec parser — grammar-hosted binding.

dsl/FrameworkSpec.g4 is the declared grammar; ANTLR generates the
parser (taf/_antlr/); parse() walks the parse tree into the model
dict consumers read:

    {"dsl": {name, framework, version, binding},
     "vocabulary": {form: entry}, "locators": {rung: entry}}

Regenerate the parser after grammar changes:

    java -cp "$ANTLR_CP" org.antlr.v4.Tool -Dlanguage=Python3 \\
        -o /tmp/antlrgen dsl/FrameworkSpec.g4
    mv /tmp/antlrgen/dsl/*.py taf/_antlr/

where $ANTLR_CP is the antlr tool + runtime jars.
"""

import os


def parse(text):
    """DSL text → the model dict."""
    from antlr4 import InputStream, CommonTokenStream
    from taf._antlr.FrameworkSpecLexer import FrameworkSpecLexer
    from taf._antlr.FrameworkSpecParser import FrameworkSpecParser
    lex = FrameworkSpecLexer(InputStream(text))
    tree = FrameworkSpecParser(CommonTokenStream(lex)).start()
    return _Walk().visit_start(tree)


def parse_file(path):
    return parse(open(path, encoding="utf-8").read())


def _text(ctx):
    return ctx.getText()


def _str(tok):
    """'...' unescaped or TRIPLE raw."""
    s = tok.getText()
    if s.startswith('"""'):
        return s[3:-3]
    return s[1:-1].replace('\\"', '"')


class _Walk:
    def visit_start(self, ctx):
        m = {"dsl": {"name": "framework-spec",
                     "framework": _text(ctx.NAME()),
                     "version": int(_text(ctx.NUMBER())),
                     "binding": "grammar-hosted"},
             "vocabulary": {}, "locators": {}}
        m["contract"] = {"env": {}, "refusals": []}
        m["artifacts"] = {}
        for d in ctx.decl():
            kw = d.getChild(0).getText()          # vocabulary|locators|contract
            if kw == "artifacts":
                for am in d.artifactMember():
                    m["artifacts"][_text(am.NAME())] = _str(am.STRING())
                continue
            if kw == "contract":
                for cm in d.contractMember():
                    kind = cm.getChild(0).getText()
                    if kind == "env":
                        m["contract"]["env"][_text(cm.NAME())] = \
                            _str(cm.STRING())
                    else:
                        m["contract"]["refusals"].append(_text(cm.NAME()))
                continue
            for e in d.entry():
                m[kw][self._entry_name(e)] = self._entry(e)
        return m

    def _entry_name(self, e):
        return _text(e.NAME())

    def _entry(self, e):
        out = {"arg": {}}
        for mem in e.member():
            kw = mem.getChild(0).getText()
            if kw == "description":
                out["description"] = _str(mem.STRING())
            elif kw == "arg":
                nm = _text(mem.NAME())
                at = mem.argType()
                out["arg"][nm] = (_str(at.STRING()) if at.STRING()
                                  else _text(at.NAME())) if at else nm
            elif kw == "caption":
                out["caption"] = _str(mem.STRING())
            elif kw == "key":
                out["key"] = _text(mem.NAME())
            elif kw in ("python", "java"):
                out.setdefault("spell", {})[kw] = _str(mem.STRING())
            elif kw == "variants":
                out["variants"] = [self._variant(v)
                                   for v in mem.variant()]
            elif kw == "lines":
                out["spell"] = self._lang_lines(mem)
            elif kw == "wrap":
                out["wrap"] = self._wrap(mem)
        if len(out["arg"]) == 1:
            out["arg"] = next(iter(out["arg"].values()))
        return out

    def _variant(self, v):
        when = [_text(n) for n in v.NAME()]
        sp = {}
        for ll in v.langLine():
            sp[ll.getChild(0).getText()] = _str(ll.STRING())
        return {"when": when, "spell": sp}

    def _lang_lines(self, mem):
        sp = {}
        for ll in mem.langLine():
            sp.setdefault(ll.getChild(0).getText(),
                          []).append(_str(ll.STRING()))
        return sp

    def _wrap(self, mem):
        w = {}
        for wl in mem.wrapLine():
            lang, side = wl.getChild(0).getText(), wl.getChild(1).getText()
            w.setdefault(lang, {}).setdefault(
                side, []).append(_str(wl.STRING()))
        return w
